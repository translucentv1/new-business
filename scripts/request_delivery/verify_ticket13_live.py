#!/usr/bin/env python3
"""Live-Beweis der Rechtslinks: gegen die AUSGELIEFERTEN Bodies, nicht gegen den Baum.

Hintergrund (Ticket 13): `legal_link_audit.py` prueft den LOKALEN Baum vollzaehlig.
Das genuegt nicht -- die Branch-Falle (Commit auf master / Datei unter docs/) laesst
eine Seite im Baum korrekt aussehen, waehrend live etwas anderes ausgeliefert wird.
Dieses Skript misst deshalb ausschliesslich das, was der Server wirklich schickt.

Ticket 17 hat zwei Schwaechen der Vorfassung behoben:
  * Sie prueste live nur eine STICHPROBE von 7 Seiten, waehrend das Audit 42 kennt
    -- genau die Teil-Vollstaendigkeits-Falle, gegen die Ticket 13 gebaut wurde.
    Die Zielmenge wird jetzt aus dem Baum ABGELEITET (gleiche Regel wie das Audit),
    damit kuenftige Traffic-Seiten automatisch mitgeprueft werden.
  * Sie kannte kein Ergebniswort fuer "nicht messbar" -- ein Netzausfall sah aus
    wie ein Defekt. Neu: LIVE_UNGEPRUEFT (rc=2).

Ergebniswoerter:
    LIVE_OK          rc=0   alles gemessen und in Ordnung
    LIVE_DEFEKT      rc=1   mindestens eine Seite nachweislich kaputt
    LIVE_UNGEPRUEFT  rc=2   nicht messbar (Netz/leere Zielmenge) -- weder gruen noch Defekt

Nutzung:
    python scripts/request_delivery/verify_ticket13_live.py
    python scripts/request_delivery/verify_ticket13_live.py --selftest
"""
from __future__ import annotations

import concurrent.futures as cf
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from legal_targets import (  # noqa: E402  (Pfad direkt darueber gesetzt)
    REQUIRED,
    is_exempt,
    iter_html,
    repo_root,
    tree_drift,
)

BASE = "https://translucentv1.github.io/new-business/"

# Die zwei Seiten, die in Ticket 13 vier Stunden lang live 404 lieferten.
# Historischer Regressionsanker -- sie stecken auch in der vollzaehligen Menge.
NEU = ["blog/hochzeitsrede-schreiben-lassen.html", "blog/pitch-deck-erstellen-lassen.html"]
KAUFPFAD = ["rtd.html", "thanks.html", "agb.html", "datenschutz.html", "impressum.html"]

REQUIRED = REQUIRED  # noqa: PLW0127 -- aus legal_targets, eine Quelle fuer beide Pruefer

# Soft-404: GitHub Pages liefert seine 404-Seite mit 9379 B -- FETTER als jede echte
# Landingpage. Groesse ist als Gesundheitsmerkmal wertlos, der Text ist es nicht.
SOFT404_MARKER = ("Page not found", "File not found")

# Ratelimit / voruebergehende Serverfehler sind KEIN Defekt-Beleg. Seit Ticket 29
# laeuft dieser Pruefer gegen 1258 statt 61 URLs -- damit wird 429 real moeglich.
# Ein Ratelimit darf nicht als "Seite tot" gelesen werden (Falsch-Rot auf dem
# Rechtspfad), muendet aber auch nicht in GRUEN, sondern in UNMESSBAR.
TRANSIENT_CODES = (429, 502, 503, 504)


def target_pages(root: str) -> list[str]:
    """Zielmenge REKURSIV aus dem Baum ableiten -- gemeinsame Regel (Ticket 29).

    Vorher stand hier glob("*.html") + glob("blog/*.html") -> 61 von 1287 Seiten.
    Das war dieselbe eingefrorene Stichprobe, die Ticket 17 auf Seitenebene
    beseitigt hatte, nur eine Ebene hoeher: nicht die Seitenliste war
    hartkodiert, sondern die Verzeichnisliste. `seo/` (693) und `t/` (468) lagen
    ausserhalb jeder Glob-Zeile.
    """
    out: list[str] = []
    for rel in iter_html(root):
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        exempt, _grund = is_exempt(rel, text)
        if not exempt:
            out.append(rel)
    return out


def get(url: str, timeout: int = 25):
    """(code, body). code=-1 heisst NICHT MESSBAR (Netz), nicht 'kaputt'."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "rtd-verify/2.0", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # Netz/Timeout
        return -1, str(e)


def wait_live(path: str, tries: int = 18, delay: int = 10):
    for i in range(tries):
        code, body = get(BASE + path)
        if code == 200:
            return code, body, i * delay
        time.sleep(delay)
    code, body = get(BASE + path)
    return code, body, tries * delay


def judge(code: int, body: str, needles=REQUIRED):
    """-> (status, detail) mit status in OK / DEFEKT / UNMESSBAR."""
    if code == -1:
        return "UNMESSBAR", "Netzfehler"
    if code in TRANSIENT_CODES:
        return "UNMESSBAR", "HTTP %s (Ratelimit/transient, kein Defekt-Beleg)" % code
    if code != 200:
        return "DEFEKT", "HTTP %s" % code
    if any(m in body for m in SOFT404_MARKER):
        return "DEFEKT", "Soft-404 (200 mit Fehlerseiten-Text)"
    miss = [n for n in needles if n not in body]
    if miss:
        return "DEFEKT", "Rechtslink fehlt: " + ",".join(miss)
    return "OK", "%d B" % len(body)


def _fetch_many(paths: list[str], needles=REQUIRED):
    def one(rel):
        code, body = get(BASE + rel)
        st, det = judge(code, body, needles)
        return rel, code, st, det
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(one, paths))


def main() -> int:
    fails: list[str] = []
    unmessbar: list[str] = []

    print("[1] Regressionsanker Ticket 13 (waren live 404):")
    for p in NEU:
        code, body, waited = wait_live(p)
        st, det = judge(code, body)
        print("    %-46s HTTP %s  nach %2ds  %s (%s)" % (p, code, waited, st, det))
        if st == "DEFEKT":
            fails.append("%s: %s" % (p, det))
        elif st == "UNMESSBAR":
            unmessbar.append(p)

    root = repo_root()
    rels = iter_html(root)
    pages = target_pages(root)

    # Deckungsabgleich (Merkregel Ticket 18): "vollzaehlig" ist eine BEHAUPTUNG,
    # solange die gelaufene Menge nicht gegen den ausgelieferten git-Tree
    # gegengemessen wurde. Drift macht das Ergebnis unmessbar, nicht gruen.
    drift_status, nur_tree, nur_walk = tree_drift(root, rels)
    deckung_unklar = ""
    if drift_status != "ok":
        deckung_unklar = drift_status
        print("[2a] Deckungsabgleich gegen git-Tree: %s" % drift_status)
        for p in nur_tree[:5]:
            print("     nur im Tree, nicht geprueft: %s" % p)
        for p in nur_walk[:5]:
            print("     nur gelaufen, nicht im Tree: %s" % p)
    else:
        print("[2a] Deckungsabgleich gegen git-Tree: ok (%d HTML-Dateien, 0 Drift)" % len(rels))

    print("[2] Rechtslinks im AUSGELIEFERTEN Body -- VOLLZAEHLIG (%d Seiten):" % len(pages))
    if not pages:
        # Leere-Schleife-Falle (Ticket 16): nichts zu pruefen ist kein gruenes Ergebnis.
        print("    KEINE Zielseite ermittelt -> es wurde NICHTS geprueft.")
        print("\nERGEBNIS: LIVE_UNGEPRUEFT")
        print("  ! leere Zielmenge -- Ableitung aus dem Baum lieferte 0 Seiten")
        return 2
    ok_n = 0
    for rel, code, st, det in _fetch_many(pages):
        if st == "OK":
            ok_n += 1
            continue
        print("    %-46s HTTP %s  %s (%s)" % (rel, code, st, det))
        if st == "DEFEKT":
            fails.append("%s: %s" % (rel, det))
        else:
            unmessbar.append(rel)
    print("    %d/%d Seiten OK (nur Abweichungen oben gelistet)" % (ok_n, len(pages)))

    print("[3] Kaufpfad erreichbar:")
    for rel, code, st, det in _fetch_many(KAUFPFAD, needles=()):
        print("    %-46s HTTP %s  %s (%s)" % (rel, code, st, det))
        if st == "DEFEKT":
            fails.append("%s: %s" % (rel, det))
        elif st == "UNMESSBAR":
            unmessbar.append(rel)

    print()
    if fails:
        print("ERGEBNIS: LIVE_DEFEKT")
        for f in fails:
            print("  ! " + f)
        return 1
    if unmessbar or deckung_unklar:
        print("ERGEBNIS: LIVE_UNGEPRUEFT")
        if deckung_unklar:
            print("  ! Prueflaeche nicht belastbar: %s" % deckung_unklar)
        if unmessbar:
            print("  ! nicht messbar (Netz): %d Seite(n) -- kein Gesundheits-Claim moeglich"
                  % len(unmessbar))
        return 2
    print("ERGEBNIS: LIVE_OK (%d Seiten vollzaehlig live geprueft)" % (len(pages) + len(KAUFPFAD)))
    return 0


# ----------------------------------------------------------------------------
# Fault Injection: nur die Aussenwelt (get / target_pages / sleep) wird ersetzt,
# gefahren wird die ECHTE main().
# ----------------------------------------------------------------------------

GOOD_BODY = ("<html><body>ok " + "x" * 900
             + " <a href='impressum.html'>Impressum</a>"
             + " <a href='datenschutz.html'>Datenschutz</a>"
             + " <a href='agb.html'>AGB</a></body></html>")
FAT404_BODY = "<html><title>Page not found &middot; GitHub Pages</title>" + "y" * 9300 + "</html>"


def _run_main(responder, pages=None, drift=None):
    """Faehrt die ECHTE main() gegen eine injizierte Aussenwelt."""
    import contextlib
    import io

    global get, target_pages, iter_html, tree_drift
    orig_get, orig_pages = get, target_pages
    orig_iter, orig_drift = iter_html, tree_drift
    orig_sleep = time.sleep
    get = responder
    if pages is not None:
        def target_pages(root):
            return list(pages)

        def iter_html(root):
            return list(pages)
    if drift is not None:
        def tree_drift(root, walked):
            return drift
    else:
        def tree_drift(root, walked):
            return "ok", [], []
    time.sleep = lambda s: None
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = main()
    finally:
        get, target_pages = orig_get, orig_pages
        iter_html, tree_drift = orig_iter, orig_drift
        time.sleep = orig_sleep
    return rc, buf.getvalue()


def _responder(mapping, default=(200, GOOD_BODY)):
    def r(url, timeout=25):
        for frag, resp in mapping.items():
            if frag in url:
                return resp
        return default
    return r


def selftest() -> int:
    fails: list[str] = []
    n = [0]

    def check(name, cond, detail=""):
        n[0] += 1
        print("  [%2d] %-58s %s %s" % (n[0], name, "OK" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    def rot(name, rc, out, wort="LIVE_DEFEKT", grund=None):
        """Rot heisst: erwartetes Ergebniswort UND kein Absturz (Exit-Code-Falle)."""
        cond = rc == 1 and wort in out and "Traceback" not in out
        if grund:
            # grund ist die ZEILE aus der Fehlerliste -- damit prueft der Test die
            # gestellte Diagnose, nicht bloss das Vorkommen eines Wortes irgendwo.
            cond = cond and grund in out
        check(name, cond, "rc=%s traceback=%s" % (rc, "Traceback" in out))

    ALLE = ["index.html", "rtd.html", "blog/a.html", "blog/b.html"]

    print("== verify_ticket13_live --selftest (Fault Injection) ==")

    # --- gruener Referenzfall ---------------------------------------------
    rc, out = _run_main(_responder({}), pages=ALLE)
    check("Alles gesund -> LIVE_OK / rc=0",
          rc == 0 and "LIVE_OK" in out and "Traceback" not in out, "rc=%s" % rc)
    check("Gruener Lauf meldet Vollzaehligkeit (4+5 Seiten)",
          "9 Seiten vollzaehlig" in out, "")

    # --- Frage 1 des Tickets: wird es rot bei 404? -------------------------
    rc, out = _run_main(_responder({"blog/b.html": (404, "")}), pages=ALLE)
    rot("404 auf einer Zielseite wird rot", rc, out,
        grund="! blog/b.html: HTTP 404")

    rc, out = _run_main(_responder({"thanks.html": (404, "")}), pages=ALLE)
    rot("404 auf dem Kaufpfad wird rot", rc, out,
        grund="! thanks.html: HTTP 404")

    rc, out = _run_main(_responder({"hochzeitsrede": (404, "")}), pages=ALLE)
    rot("Regressionsanker wieder 404 wird rot", rc, out,
        grund="! blog/hochzeitsrede-schreiben-lassen.html: HTTP 404")

    # --- Frage 2: fehlender Datenschutz-Link im LIVE-Body ------------------
    ohne_ds = GOOD_BODY.replace("datenschutz.html", "x.html")
    rc, out = _run_main(_responder({"blog/a.html": (200, ohne_ds)}), pages=ALLE)
    rot("Datenschutz-Link fehlt im Body wird rot", rc, out,
        grund="! blog/a.html: Rechtslink fehlt: datenschutz.html")

    ohne_imp = GOOD_BODY.replace("impressum.html", "x.html")
    rc, out = _run_main(_responder({"index.html": (200, ohne_imp)}), pages=ALLE)
    rot("Impressum-Link fehlt im Body wird rot", rc, out,
        grund="! index.html: Rechtslink fehlt: impressum.html")

    ohne_agb = GOOD_BODY.replace("agb.html", "x.html")
    rc, out = _run_main(_responder({"blog/b.html": (200, ohne_agb)}), pages=ALLE)
    rot("AGB-Link fehlt im Body wird rot", rc, out,
        grund="! blog/b.html: Rechtslink fehlt: agb.html")

    # --- Frage 3: Fette-404-Falle -----------------------------------------
    rc, out = _run_main(_responder({"blog/a.html": (404, FAT404_BODY)}), pages=ALLE)
    rot("Fettes 404 (9379 B) wird rot, nicht durchgewunken", rc, out,
        grund="! blog/a.html: HTTP 404")

    rc, out = _run_main(_responder({"blog/a.html": (200, FAT404_BODY)}), pages=ALLE)
    rot("Soft-404 (HTTP 200 + Fehlerseiten-Text) wird rot", rc, out,
        grund="! blog/a.html: Soft-404")

    check("Groesse allein macht nicht gesund (fettes 404 > echte Seite)",
          len(FAT404_BODY) > len(GOOD_BODY), "%d > %d" % (len(FAT404_BODY), len(GOOD_BODY)))

    # --- Frage 4: Baum != Auslieferung ------------------------------------
    # Der Baum ist in Ordnung (target_pages liefert Seiten), die Auslieferung nicht.
    rc, out = _run_main(_responder({"blog/": (200, ohne_ds)}), pages=ALLE)
    rot("Baum gruen, Auslieferung ohne Link -> rot (Branch-Falle)", rc, out,
        grund="! blog/a.html: Rechtslink fehlt: datenschutz.html")

    # --- Leere-Schleife-Falle (Ticket 16) ---------------------------------
    rc, out = _run_main(_responder({}), pages=[])
    check("Leere Zielmenge ist NICHT gruen (rc=2 LIVE_UNGEPRUEFT)",
          rc == 2 and "LIVE_UNGEPRUEFT" in out and "LIVE_OK" not in out
          and "Traceback" not in out, "rc=%s" % rc)

    # --- Netzfehler: nicht messbar != gesund und != Defekt -----------------
    rc, out = _run_main(_responder({"blog/b.html": (-1, "timed out")}), pages=ALLE)
    check("Netzfehler -> LIVE_UNGEPRUEFT (rc=2), kein Gruen",
          rc == 2 and "LIVE_UNGEPRUEFT" in out and "LIVE_OK" not in out
          and "Traceback" not in out, "rc=%s" % rc)

    # Ein echter Defekt schlaegt Unmessbarkeit -- sonst versteckt ein Timeout einen Defekt.
    rc, out = _run_main(_responder({"blog/b.html": (-1, "timed out"),
                                    "blog/a.html": (404, "")}), pages=ALLE)
    rot("Defekt + Netzfehler -> Defekt gewinnt (rc=1)", rc, out,
        grund="! blog/a.html: HTTP 404")

    # --- Vollzaehligkeit: neue Seite wird automatisch mitgeprueft ----------
    rc, out = _run_main(_responder({"blog/neu.html": (200, ohne_ds)}),
                        pages=ALLE + ["blog/neu.html"])
    rot("Neue Traffic-Seite ohne Link wird mitgeprueft (keine Stichprobe)", rc, out,
        grund="! blog/neu.html: Rechtslink fehlt: datenschutz.html")

    # --- Zielmenge wirklich aus dem Baum abgeleitet ------------------------
    echte = target_pages(repo_root())
    check("target_pages leitet Zielmenge aus dem Baum ab (>7 Seiten)",
          len(echte) > 7, "%d Seiten" % len(echte))
    check("Rechtsseiten sind ausgenommen (nicht sich selbst pruefen)",
          not any(p in REQUIRED for p in echte), "")

    # --- Ticket 29: die eingefrorene VERZEICHNIS-Liste ---------------------
    # Der alte Pruefer sah nur "*.html" + "blog/*.html". Eine Seite in einem
    # neu entstandenen Unterverzeichnis MUSS in der Zielmenge auftauchen.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tief = os.path.join(td, "seo", "neues-buch", "kapitel", "7")
        os.makedirs(tief)
        with open(os.path.join(tief, "index.html"), "w", encoding="utf-8") as fh:
            fh.write("<html><body>" + "x" * 900 + "</body></html>")
        with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as fh:
            fh.write("<html><body>" + "x" * 900 + "</body></html>")
        abgeleitet = target_pages(td)
    check("T29: Seite in NEUEM tiefen Unterverzeichnis ist in der Zielmenge",
          "seo/neues-buch/kapitel/7/index.html" in abgeleitet, str(len(abgeleitet)))
    check("T29: Wurzelseite bleibt in der Zielmenge (keine Regression)",
          "index.html" in abgeleitet, "")

    # Gegen den ECHTEN Baum: genau die zwei Verzeichnisbaeume, die der alte
    # Pruefer nie gesehen hat, muessen jetzt drin sein.
    check("T29: seo/-Seiten sind in der echten Zielmenge",
          sum(1 for p in echte if p.startswith("seo/")) > 100,
          "%d Seiten" % sum(1 for p in echte if p.startswith("seo/")))
    check("T29: t/-Seiten sind in der echten Zielmenge",
          sum(1 for p in echte if p.startswith("t/")) > 100,
          "%d Seiten" % sum(1 for p in echte if p.startswith("t/")))
    check("T29: dl/ (bezahlte Kundenware) ist NICHT Zielmenge",
          not any(p.startswith("dl/") for p in echte), "")

    # --- Ticket 29: beide Pruefer, EINE Ableitungsregel --------------------
    import legal_link_audit as _audit

    import legal_targets as _lt
    check("T29: Live-Pruefer nutzt legal_targets.is_exempt (Objektidentitaet)",
          is_exempt is _lt.is_exempt, "")
    check("T29: Baum-Pruefer nutzt dieselbe Funktion (kein Drift moeglich)",
          _audit.is_exempt is _lt.is_exempt, "")
    check("T29: beide Pruefer teilen das Pflicht-SET",
          tuple(REQUIRED) == tuple(_audit.REQUIRED) == tuple(_lt.REQUIRED), str(REQUIRED))

    # --- Ticket 29: Deckungsabgleich (Merkregel Ticket 18) -----------------
    rc, out = _run_main(_responder({}), pages=ALLE,
                        drift=("drift", ["seo/uebersehen/index.html"], []))
    check("T29: Drift der Prueflaeche ist NICHT gruen (rc=2)",
          rc == 2 and "LIVE_UNGEPRUEFT" in out and "LIVE_OK" not in out
          and "Traceback" not in out, "rc=%s" % rc)
    check("T29: Drift benennt die ungepruefte Seite",
          "nur im Tree, nicht geprueft: seo/uebersehen/index.html" in out, "")

    rc, out = _run_main(_responder({}), pages=ALLE,
                        drift=("unmessbar: git nicht ausfuehrbar", [], []))
    check("T29: unlesbarer git-Tree -> unmessbar, nicht gruen",
          rc == 2 and "LIVE_UNGEPRUEFT" in out and "LIVE_OK" not in out, "rc=%s" % rc)

    rc, out = _run_main(_responder({"blog/a.html": (404, "")}), pages=ALLE,
                        drift=("drift", ["x/y.html"], []))
    rot("T29: echter Defekt schlaegt Deckungsluecke (rc=1)", rc, out,
        grund="! blog/a.html: HTTP 404")

    # --- Ticket 29: Ratelimit ist kein Defekt-Beleg ------------------------
    # Bei 1258 statt 61 URLs pro Lauf wird 429 real. Ein Ratelimit darf weder
    # als "Seite tot" (Falsch-Rot) noch als gesund (Falsch-Gruen) enden.
    rc, out = _run_main(_responder({"blog/b.html": (429, "")}), pages=ALLE)
    check("T29: HTTP 429 -> LIVE_UNGEPRUEFT (rc=2), kein Defekt-Claim",
          rc == 2 and "LIVE_UNGEPRUEFT" in out and "LIVE_DEFEKT" not in out
          and "LIVE_OK" not in out and "Traceback" not in out, "rc=%s" % rc)
    rc, out = _run_main(_responder({"blog/b.html": (503, "")}), pages=ALLE)
    check("T29: HTTP 503 -> LIVE_UNGEPRUEFT (rc=2), kein Defekt-Claim",
          rc == 2 and "LIVE_UNGEPRUEFT" in out and "LIVE_DEFEKT" not in out, "rc=%s" % rc)
    rc, out = _run_main(_responder({"blog/b.html": (429, ""), "blog/a.html": (404, "")}),
                        pages=ALLE)
    rot("T29: Defekt schlaegt Ratelimit (rc=1)", rc, out,
        grund="! blog/a.html: HTTP 404")
    check("T29: 404 bleibt Defekt (Ratelimit-Regel hat es nicht aufgeweicht)",
          judge(404, "")[0] == "DEFEKT", judge(404, "")[1])

    print()
    print("%d/%d bestanden -> %s"
          % (n[0] - len(fails), n[0], "SELFTEST_OK" if not fails else "SELFTEST_ROT"))
    for f in fails:
        print("  ! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        raise SystemExit(selftest())
    raise SystemExit(main())
