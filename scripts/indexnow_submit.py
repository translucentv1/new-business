#!/usr/bin/env python3
"""IndexNow-Submission fuer die statische GitHub-Pages-Site (Bing/Yandex/Seznam).

Warum: Google /ping ist tot (404) und Search Console braucht Login. IndexNow ist
der EINZIGE autonome, kostenlose, ToS-konforme Indexierungs-Hebel ohne Login.

WICHTIG (Scope-Regel der IndexNow-Spezifikation):
  Liegt die Key-Datei unter https://host/pfad/<key>.txt, duerfen NUR URLs unter
  /pfad/ eingereicht werden. Unsere Site liegt unter /new-business/, die
  Key-Datei im gh-pages-ROOT -> live unter /new-business/<key>.txt.
  Damit ist genau unser URL-Raum autorisiert.

GELTUNGSBEREICH (Lehre aus Ticket 18): eingereicht werden muessen die
AUSGELIEFERTEN URLs. sitemap_urls() liest aber den LOKALEN Baum. Darum wird vor
jeder Einreichung die LIVE-Sitemap geholt und gegengerechnet:
  - URL lokal, aber nicht live -> wuerde als 404 eingereicht (schadet dem Key)
  - URL live, aber nicht lokal -> stille Schrumpfung der Einreich-Menge
Beides ist INDEXNOW_DRIFT (rc=1) und wird NICHT eingereicht (ausser --allow-drift).

Ergebniswoerter (Konvention Ticket 16/17/18: echter Defekt > unmessbar > Rest):
  SUBMIT_OK                        rc=0   alles angenommen
  SUBMIT_OK_TEILMENGE              rc=0   nur mit --allow-drift: Schnittmenge
  SUBMIT_FEHLER / KEY_NICHT_LIVE /
  KEINE_URLS / INDEXNOW_DRIFT      rc=1   echter Defekt
  INDEXNOW_UNGEPRUEFT              rc=2   Netz/DNS tot -> KEIN Defekt-Vorwurf
  SUBMIT_403_KEY_NOCH_NICHT_...    rc=3   Bing hat den Key noch nicht gecrawlt

Belegpflicht: das Skript druckt den echten HTTP-Status.
  200/202 = angenommen (NICHT indexiert!).
  403     = Bing hat die Key-Datei noch NICHT gecrawlt (kein URL-Fehler!)
  422     = URL-Scope/Key passt nicht zur Key-Datei.

Nutzung:
  python scripts/indexnow_submit.py             # alle Sitemap-URLs
  python scripts/indexnow_submit.py --limit 10  # kleiner Erst-Submit
  python scripts/indexnow_submit.py --check     # nur Key-Datei live pruefen
  python scripts/indexnow_submit.py --selftest  # Fault Injection, kein Netz
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HOST = "translucentv1.github.io"
BASE = "https://translucentv1.github.io/new-business/"
KEY = "49bf6b5c07acd9038ee05981c1810baa"
KEY_URL = BASE + KEY + ".txt"
LIVE_SITEMAP_URL = BASE + "sitemap.xml"
SITEMAP = os.path.join(ROOT, "sitemap.xml")
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000  # Spec-Limit pro Request

NET = 0  # http() meldet Netz-/DNS-Fehler als Status 0

RC_OK, RC_DEFEKT, RC_UNGEPRUEFT, RC_403 = 0, 1, 2, 3


def http(url, data=None, headers=None, timeout=60, maxlen=400):
    """Liefert (status, body) auch bei HTTP-Fehlercodes (kein Raise).

    ACHTUNG (real gemessener Defekt, 2026-08-05): der Body wird auf `maxlen`
    Zeichen gekuerzt — das genuegt fuer Statusmeldungen, NICHT fuer Dokumente.
    Die Live-Sitemap sah dadurch wie 3 statt 1220 URLs aus und der Drift-Check
    schlug falsch an. Wer ein ganzes Dokument braucht: maxlen=None.
    """
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (body if maxlen is None else body[:maxlen])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, (body if maxlen is None else body[:maxlen])
    except Exception as e:  # Netzwerk/DNS
        return NET, repr(e)


def check_key_live():
    """(zustand, status): zustand in {'ok','falsch','unmessbar'}."""
    status, body = http(KEY_URL)
    if status == NET:
        print("[key] %s -> NETZFEHLER %s" % (KEY_URL, body[:80]))
        return "unmessbar", status
    ok = status == 200 and body.strip() == KEY
    print("[key] %s -> HTTP %s body=%r ok=%s" % (KEY_URL, status, body[:60], ok))
    return ("ok" if ok else "falsch"), status


def scope_filter(urls):
    """Nur autorisierter Scope; /dl/ ist per robots.txt disallow (ADR-0013)."""
    scoped = [u for u in urls if u.startswith(BASE) and "/dl/" not in u]
    return scoped


def parse_locs(raw):
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", raw)


def sitemap_urls():
    if not os.path.exists(SITEMAP):
        print("[sitemap] FEHLT: %s" % SITEMAP)
        return []
    with open(SITEMAP, "r", encoding="utf-8") as f:
        raw = f.read()
    urls = parse_locs(raw)
    scoped = scope_filter(urls)
    print("[sitemap] lokal: %d URLs gelesen, %d im Scope (%d verworfen)"
          % (len(urls), len(scoped), len(urls) - len(scoped)))
    return scoped


def live_sitemap_urls():
    """(zustand, urls): zustand in {'ok','unmessbar'} — Geltungsbereich AUSLIEFERUNG."""
    # maxlen=None ist PFLICHT: mit der 400-Zeichen-Kuerzung wuerden nur die
    # ersten ~3 <loc>-Eintraege ankommen -> falscher Drift-Alarm.
    status, body = http(LIVE_SITEMAP_URL, maxlen=None)
    if status != 200:
        print("[sitemap] LIVE %s -> HTTP %s (Geltungsbereich nicht pruefbar)"
              % (LIVE_SITEMAP_URL, status))
        return "unmessbar", []
    urls = scope_filter(parse_locs(body))
    print("[sitemap] live : %d URLs im Scope" % len(urls))
    return "ok", urls


def drift_report(local, live):
    """(nur_lokal, nur_live) — sortiert, damit die Ausgabe stabil ist."""
    return sorted(set(local) - set(live)), sorted(set(live) - set(local))


def submit(urls):
    payload = {"host": HOST, "key": KEY, "keyLocation": KEY_URL, "urlList": urls}
    body = json.dumps(payload).encode("utf-8")
    status, resp = http(ENDPOINT, data=body,
                        headers={"Content-Type": "application/json; charset=utf-8"})
    print("[submit] %d URLs -> HTTP %s %s" % (len(urls), status, resp.strip()[:200]))
    return status


def _bewerte(codes):
    """Ergebniswort + rc aus den Batch-Codes. Echter Defekt > unmessbar > 403 > OK."""
    if not codes:  # Leere-Schleife-Falle (Ticket 16): nichts gesendet ist nicht gruen
        return "SUBMIT_FEHLER kein einziger Batch gesendet codes=[]", RC_DEFEKT
    hart = [c for c in codes if c not in (200, 202, 403, NET)]
    if hart:
        return "SUBMIT_FEHLER codes=%s" % (codes,), RC_DEFEKT
    if NET in codes:
        return ("INDEXNOW_UNGEPRUEFT Netz-/DNS-Fehler beim Senden - kein Urteil "
                "ueber die URLs codes=%s" % (codes,)), RC_UNGEPRUEFT
    if 403 in codes:
        return ("SUBMIT_403_KEY_NOCH_NICHT_GECRAWLT (kein URL-Fehler) codes=%s"
                % (codes,)), RC_403
    return "SUBMIT_OK codes=%s" % (codes,), RC_OK


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N URLs")
    ap.add_argument("--check", action="store_true", help="nur Key-Datei pruefen")
    ap.add_argument("--allow-drift", action="store_true",
                    help="bei Drift die Schnittmenge lokal&live einreichen")
    ap.add_argument("--selftest", action="store_true",
                    help="Fault Injection, loest KEINE echte Einreichung aus")
    args = ap.parse_args()

    if args.selftest:
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        from _indexnow_selftest_cases import run_selftest
        return run_selftest(os.path.abspath(__file__))

    zustand, status = check_key_live()
    if zustand == "unmessbar":
        print("ERGEBNIS: INDEXNOW_UNGEPRUEFT - Netz/DNS nicht erreichbar, "
              "keine Aussage ueber die Key-Datei.")
        return RC_UNGEPRUEFT
    if args.check:
        if zustand == "ok":
            print("ERGEBNIS: KEY_LIVE")
            return RC_OK
        print("ERGEBNIS: KEY_NICHT_LIVE (HTTP %s)" % status)
        return RC_DEFEKT
    if zustand != "ok":
        print("ERGEBNIS: KEY_NICHT_LIVE - erst pushen/warten, dann erneut einreichen.")
        return RC_DEFEKT

    urls = sitemap_urls()
    if not urls:
        print("ERGEBNIS: KEINE_URLS")
        return RC_DEFEKT

    live_zustand, live_urls = live_sitemap_urls()
    if live_zustand == "unmessbar":
        print("ERGEBNIS: INDEXNOW_UNGEPRUEFT - LIVE-Sitemap nicht abrufbar, "
              "Geltungsbereich (Baum vs Auslieferung) unpruefbar.")
        return RC_UNGEPRUEFT

    nur_lokal, nur_live = drift_report(urls, live_urls)
    if nur_lokal or nur_live:
        print("[drift] nur lokal (waere 404 beim Einreichen): %d %s"
              % (len(nur_lokal), nur_lokal[:3]))
        print("[drift] nur live (stille Schrumpfung der Menge): %d %s"
              % (len(nur_live), nur_live[:3]))
        if not args.allow_drift:
            print("ERGEBNIS: INDEXNOW_DRIFT lokal=%d live=%d nur_lokal=%d nur_live=%d "
                  "- erst pushen/Sitemap erneuern, dann einreichen."
                  % (len(urls), len(live_urls), len(nur_lokal), len(nur_live)))
            return RC_DEFEKT
        urls = sorted(set(urls) & set(live_urls))
        print("[drift] --allow-drift: reiche nur die Schnittmenge ein (%d URLs)"
              % len(urls))
        if not urls:
            print("ERGEBNIS: KEINE_URLS Schnittmenge lokal&live ist leer")
            return RC_DEFEKT

    teilmenge = bool(nur_lokal or nur_live)
    if args.limit:
        urls = urls[:max(args.limit, 0)]
        teilmenge = True
        if not urls:
            print("ERGEBNIS: KEINE_URLS --limit hat alle URLs entfernt")
            return RC_DEFEKT
    print("[geltungsbereich] eingereicht wird gegen die LIVE-Auslieferung "
          "(%d URLs, vollzaehlig=%s)" % (len(urls), "nein" if teilmenge else "ja"))

    codes = []
    for i in range(0, len(urls), BATCH):
        codes.append(submit(urls[i:i + BATCH]))

    wort, rc = _bewerte(codes)
    if rc == RC_OK and teilmenge:
        wort = wort.replace("SUBMIT_OK", "SUBMIT_OK_TEILMENGE", 1)
    print("ERGEBNIS: %s" % wort)
    return rc


if __name__ == "__main__":
    sys.exit(main())
