#!/usr/bin/env python3
"""Ticket 11 — beweist die LETZTE ungemessene Etappe des Geldpfads.

Frage: Landet ein von auto_fulfill erzeugtes Deliverable wirklich LIVE unter
der URL, die thanks.html abfragt?

Bisher ASSUMED: dl/rtd/ ist lokal UND in git leer -> write->commit->push->Pages
ist noch NIE end-to-end gelaufen. Genau diese Klasse Defekt (falscher Branch /
falsches Verzeichnis) hat IndexNow 11 Tage gekostet.

Besonderheit: thanks.html pollt mit HEAD (nicht GET). Ein reiner GET-Test wuerde
den Kundenpfad NICHT beweisen -> hier werden GET und HEAD getrennt gemessen.

Ticket 20 (2026-08-06): zusaetzlich wird der AUSGELIEFERTE Body geprueft.
Grund (MEASURED): der einzige robots.txt, den ein Crawler liest, ist der des
Origins - https://translucentv1.github.io/robots.txt - und der ist HTTP 404.
Das repo-eigene new-business/robots.txt (HTTP 200, mit "Disallow: /dl/") wird
von KEINEM Crawler gelesen (REP gilt pro Origin, nicht pro Unterverzeichnis).
Damit ist /dl/ crawlbar und das meta-robots-noindex in der erzeugten Seite der
EINZIGE Schutz der bezahlten Kundenware. Genau dieser Schutz war ungemessen:
bis hierher wurden nur GET/HEAD-Statuscodes geprueft, nie der Inhalt.

Der Test benutzt die ECHTEN Produktivfunktionen (write_page/git_publish), nicht
eine Nachbildung. Kein Stripe-Call, keine sales.log-Zeile, kein State.
Raeumt sich selbst auf (Datei geloescht + gepusht + 404 verifiziert).

Aufruf: python scripts/request_delivery/verify_publish_leg.py
        python scripts/request_delivery/verify_publish_leg.py --keep      (kein Cleanup)
        python scripts/request_delivery/verify_publish_leg.py --selftest  (Fault Injection, offline)
"""
import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_fulfill as af  # noqa: E402

CANARY_SID = "cs_canary_publishleg_ticket11"

# Aus der Quelle abgeleitet statt hartkodiert: welchen Schutz verspricht die
# Produktivfunktion ueberhaupt? (Merkregel Ticket 17: Zielmengen ableiten.)
ROBOTS_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)', re.I
)


def http(url, method):
    """Gibt (status, body) zurueck; body ist Text ("" bei HEAD/Fehler).

    Liefert bewusst den ganzen Body (keine Kuerzung) - eine Attrappe muss
    denselben Vertrag nachbilden (Attrappen-Falle, Ticket 19).
    """
    req = urllib.request.Request(url, method=method)
    req.add_header("Cache-Control", "no-store")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return f"ERR:{e}", ""


def poll_until(url, method, want, tries=20, pause=10):
    """Wartet auf einen Statuscode. Gibt (ok, status, sekunden) zurueck."""
    t0 = time.time()
    for _ in range(tries):
        st, _body = http(url, method)
        if st == want:
            return True, st, round(time.time() - t0)
        time.sleep(pause)
    return False, st, round(time.time() - t0)


def git(*args):
    p = subprocess.run(["git", *args], cwd=af.ROOT,
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def main():
    keep = "--keep" in sys.argv
    fails = []

    print("== Ticket 11: Publish-Etappe des Geldpfads ==")
    rc, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    print(f"branch            = {branch}")
    if branch != "gh-pages":
        fails.append(f"falscher Branch: {branch} (Pages liefert gh-pages-ROOT)")

    # 1) Schreiben ueber die ECHTE Produktivfunktion
    path, url = af.write_page(CANARY_SID, "TICKET-11 CANARY (kein Kundenauftrag)",
                              "Technischer Zustellungstest. Diese Datei wird "
                              "nach der Messung wieder entfernt.")
    size = os.path.getsize(path)
    h = af.sid_hash(CANARY_SID)
    print(f"geschrieben       = {path} ({size} B)")
    print(f"erwartete URL     = {url}")
    if not url.endswith(f"/dl/rtd/{h}.html"):
        fails.append("URL-Aufbau weicht vom thanks.html-Pfad ab")

    # 2) Vor dem Push MUSS es 404 sein - sonst misst man einen Altstand
    st_before, _ = http(url, "GET")
    print(f"vor dem Push      = HTTP {st_before} (404 erwartet)")
    if st_before == 200:
        fails.append("URL war schon vor dem Push 200 - Messung wertlos")

    # 3) Publizieren ueber die ECHTE Produktivfunktion
    ok_push = af.git_publish("test(Ticket 11): Canary fuer Publish-Etappe")
    rc, head = git("log", "-1", "--oneline")
    print(f"git_publish()     = {ok_push} | HEAD: {head}")
    if not ok_push:
        fails.append("git_publish() meldete Fehler")

    # 3b) Ist der Commit wirklich auf dem REMOTE? (Branch-Falle)
    rc, cnt = git("rev-list", "--count", "origin/gh-pages..HEAD")
    print(f"unpushed commits  = {cnt} (0 erwartet)")
    if cnt != "0":
        fails.append(f"{cnt} Commit(s) NICHT auf origin/gh-pages")

    # 3c) Liegt die Datei wirklich im Remote-Tree?
    rc, tree = git("ls-tree", "-r", "--name-only", "origin/gh-pages",
                   f"dl/rtd/{h}.html")
    print(f"im origin-Tree    = {tree or '(LEER!)'}")
    if not tree:
        fails.append("Datei fehlt im origin/gh-pages-Tree")

    # 4) LIVE: GET (Kunde oeffnet) und HEAD (thanks.html pollt) GETRENNT
    ok_get, st_get, s_get = poll_until(url, "GET", 200)
    print(f"LIVE GET          = HTTP {st_get} nach {s_get}s")
    if not ok_get:
        fails.append(f"GET wurde nicht 200 (letzter Status {st_get})")

    st_head, _ = http(url, "HEAD")
    print(f"LIVE HEAD         = HTTP {st_head}  <- das pollt thanks.html")
    if st_head != 200:
        fails.append(f"HEAD ist {st_head} - thanks.html wuerde ewig pollen")

    # 4c) Traegt die AUSGELIEFERTE Seite den Indexier-Schutz? (Ticket 20)
    # Gemessen wird der LIVE-Body, nicht die lokale Datei - eine lokale Datei
    # beweist nach der Branch-Falle gar nichts ueber die Auslieferung.
    _st_body, body = http(url, "GET")
    m = ROBOTS_RE.search(body)
    robots = m.group(1).strip().lower() if m else None
    print(f"LIVE meta robots  = {robots or '(FEHLT)'}"
          "  <- einziger Schutz (Origin-robots.txt ist 404)")
    if robots is None:
        fails.append("ausgeliefertes Deliverable hat KEIN meta robots - "
                     "bezahlte Kundenware ist indexierbar")
    elif "noindex" not in robots:
        fails.append(f"ausgeliefertes meta robots ohne noindex ({robots}) - "
                     "bezahlte Kundenware ist indexierbar")

    # 5) Cleanup: Datei weg, gepusht, 404 verifiziert
    if keep:
        print("cleanup           = uebersprungen (--keep)")
    else:
        os.remove(path)
        for cmd in (["add", "-A", "dl/rtd"],
                    ["commit", "-m", "chore(Ticket 11): Canary entfernt"],
                    ["push"]):
            rc, out = git(*cmd)
            if rc != 0 and "nothing to commit" not in out:
                fails.append(f"Cleanup-Fehler bei git {cmd[0]}: {out}")
        ok_404, st_404, s_404 = poll_until(url, "GET", 404)
        print(f"nach Cleanup      = HTTP {st_404} nach {s_404}s (404 erwartet)")
        if not ok_404:
            fails.append(f"Canary bleibt erreichbar (HTTP {st_404})")

    print()
    if fails:
        print("PUBLISH-ETAPPE DEFEKT:")
        for f in fails:
            print("  -", f)
        return 1
    print("PUBLISH_LEG_OK — write -> commit -> push -> Pages -> GET+HEAD 200 "
          "end-to-end MEASURED.")
    return 0


def _selftest():
    """Fault Injection: erkennt main() Defekte wirklich, oder sagt es nur 'OK'?

    Ein Pruefer, der nie rot wird, winkt einen kaputten Geldpfad durch. Alle
    Aussenabhaengigkeiten werden gestubbt -> kein Push, kein Netz, kein Repo.
    """
    g = globals()
    h = af.sid_hash(CANARY_SID)
    good = f"{af.SITE}/dl/rtd/{h}.html"
    good_body = ('<html><head><meta name="robots" content="noindex,nofollow">'
                 "</head><body>x</body></html>")

    def run(branch="gh-pages", url=good, before=404, publish=True,
            unpushed="0", tree=f"dl/rtd/{h}.html", get200=True, head=200,
            body=good_body):
        fd, tmp = tempfile.mkstemp(prefix="rtd-selftest-", suffix=".html")
        os.write(fd, b"x")
        os.close(fd)
        n = [0]

        def _http(_u, m):
            # Vertrag der echten http(): (status, body-TEXT), ungekuerzt.
            if m == "HEAD":
                return head, ""
            n[0] += 1
            return (before, "") if n[0] == 1 else (200, body)

        keep = {k: g[k] for k in ("git", "http", "poll_until")}
        wp, gp, argv = af.write_page, af.git_publish, sys.argv
        af.write_page = lambda *_a: (tmp, url)
        af.git_publish = lambda _m: publish
        g["git"] = lambda *a: (0, {"rev-parse": branch, "log": "stub",
                                   "rev-list": unpushed, "ls-tree": tree}[a[0]])
        g["http"] = _http
        g["poll_until"] = lambda _u, _m, w, **_k: ((True, w, 0)
                                                   if w != 200 or get200
                                                   else (False, 500, 0))
        sys.argv = ["x", "--keep"]          # Cleanup-Zweig aus: keine git-Writes
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = main()
        finally:
            g.update(keep)
            af.write_page, af.git_publish, sys.argv = wp, gp, argv
            if os.path.exists(tmp):
                os.remove(tmp)
        return rc, buf.getvalue()

    cases = [
        # (Name, erwartetes rc, kwargs, erwartete EXAKTE Diagnose-Teilzeile)
        # Merkregel Ticket 17: Rot-Faelle gegen die Diagnosezeile assertieren,
        # sonst besteht der Test auch bei Rot aus dem falschen Grund.
        ("alles gesund",              0, {}, None),
        ("falscher Branch",           1, {"branch": "master"},
         "falscher Branch: master"),
        ("git_publish Fehler",        1, {"publish": False},
         "git_publish() meldete Fehler"),
        ("Commit nicht auf origin",   1, {"unpushed": "1"},
         "1 Commit(s) NICHT auf origin/gh-pages"),
        ("Datei fehlt im Tree",       1, {"tree": ""},
         "Datei fehlt im origin/gh-pages-Tree"),
        ("GET nie 200",               1, {"get200": False},
         "GET wurde nicht 200"),
        ("GET 200 aber HEAD 404",     1, {"head": 404},
         "HEAD ist 404"),
        ("URL schon vor Push live",   1, {"before": 200},
         "URL war schon vor dem Push 200"),
        ("URL-Aufbau falsch",         1, {"url": "https://x.invalid/y.html"},
         "URL-Aufbau weicht vom thanks.html-Pfad ab"),
        # Ticket 20: der Indexier-Schutz der Kundenware
        ("Deliverable ohne meta robots", 1, {"body": "<html>ungeschuetzt</html>"},
         "hat KEIN meta robots"),
        ("meta robots ohne noindex",  1,
         {"body": '<meta name="robots" content="index,follow">'},
         "ohne noindex (index,follow)"),
        ("noindex vorhanden = gruen", 0,
         {"body": '<meta name="robots" content="noindex">'}, None),
    ]
    print("== Fault Injection gegen main() (offline, ohne Nebenwirkung) ==")
    bad = 0
    for name, want, kw, expect in cases:
        rc, out = run(**kw)
        why = "; ".join(l.strip(" -") for l in out.splitlines()
                        if l.startswith("  - "))
        good_rc = rc == want
        # Exit-Code-Falle (Ticket 14): rc=1 kann auch ein Absturz sein.
        crashed = "Traceback" in out
        diag_ok = expect is None or expect in out
        passed = good_rc and diag_ok and not crashed
        bad += not passed
        if crashed:
            why = "TRACEBACK statt Diagnose"
        elif not diag_ok:
            why = f"falsche Diagnose (erwartet: {expect!r})"
        print(f"  [{'OK ' if passed else 'FAIL'}] {name:<30} rc={rc}"
              + (f" | {why}" if why else ""))
    if bad:
        print(f"SELFTEST FEHLGESCHLAGEN: {bad} Defekt(e) NICHT erkannt.")
        return 1
    print(f"SELFTEST OK: {len(cases)}/{len(cases)} Defekte erkannt "
          "(kritisch: GET 200 + HEAD 404 = Kunde pollt ewig; "
          "Deliverable ohne noindex = Kundenware indexierbar).")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else main())
