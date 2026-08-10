#!/usr/bin/env python3
"""Prueft, ob JEDE ausgelieferte HTML-Seite die Pflicht-Rechtslinks traegt.

Hintergrund (Ticket 13): datenschutz.html/agb.html/impressum.html existieren seit
Ticket 6, aber "existiert" ist nicht "von jeder Seite erreichbar". § 5 DDG und
Art. 13 DSGVO verlangen staendige Verfuegbarkeit -- ein Besucher landet per SEO
auf einer Blogseite, nicht auf der Startseite.

Nutzung:
    python scripts/request_delivery/legal_link_audit.py            # lokaler Baum
    python scripts/request_delivery/legal_link_audit.py --live     # zusaetzlich HTTP
    python scripts/request_delivery/legal_link_audit.py --selftest # Fault Injection
"""
from __future__ import annotations

import os
import sys
import tempfile

from legal_targets import (  # noqa: E402  (Pfad wird unten gesetzt)
    REQUIRED,
    is_exempt,
    iter_html,
    missing_links,
    repo_root,
    tree_drift,
)

# Ausnahmen und Ziel-Ableitung liegen seit Ticket 29 in legal_targets.py --
# gemeinsame Quelle mit verify_ticket13_live.py, damit die beiden Pruefer nicht
# auseinanderdriften (Merkregel Ticket 17).


def audit_tree(root: str, check_drift: bool = True) -> dict:
    """Zielmenge REKURSIV aus dem Baum ableiten (Ticket 29).

    Vorher: glob("*.html") + glob("blog/*.html") -> 61 von 1287 Seiten.
    Die 693 `seo/`- und 468 `t/`-Seiten lagen ausserhalb jeder Glob-Zeile und
    waren damit unsichtbar, obwohl sie 90,7 % der Sitemap stellen.
    """
    rels = iter_html(root)
    result: dict = {"checked": [], "exempt": [], "missing": {}, "drift": None}
    if check_drift:
        status, nur_tree, nur_walk = tree_drift(root, rels)
        if status != "ok":
            result["drift"] = (status, nur_tree, nur_walk)
    for rel in rels:
        path = os.path.join(root, rel)
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError as exc:  # pragma: no cover
            result["missing"][rel] = ["UNREADABLE: %s" % exc]
            continue
        exempt, why = is_exempt(rel, text)
        if exempt:
            result["exempt"].append((rel, why))
            continue
        result["checked"].append(rel)
        miss = missing_links(text)
        if miss:
            result["missing"][rel] = miss
    return result


def print_report(res: dict) -> int:
    print("== Rechtslink-Audit (lokaler Baum) ==")
    print("geprueft        = %d Seiten" % len(res["checked"]))
    print("ausgenommen     = %d (Rechtsseiten/Redirects/Stubs)" % len(res["exempt"]))
    print("unvollstaendig  = %d" % len(res["missing"]))
    drift = res.get("drift")
    if drift:
        status, nur_tree, nur_walk = drift
        print("\nDECKUNGSABGLEICH gegen git-Tree: %s" % status)
        for rel in nur_tree[:10]:
            print("  nur im ausgelieferten Tree, NICHT geprueft: %s" % rel)
        for rel in nur_walk[:10]:
            print("  gelaufen, aber nicht im Tree: %s" % rel)
    if res["missing"]:
        by_missing: dict[str, int] = {}
        for miss in res["missing"].values():
            for m in miss:
                by_missing[m] = by_missing.get(m, 0) + 1
        print("\nfehlende Links (Haeufigkeit):")
        for k, v in sorted(by_missing.items(), key=lambda kv: -kv[1]):
            print("  %-20s fehlt auf %d Seiten" % (k, v))
        print("\nerste 15 betroffene Seiten:")
        for rel in sorted(res["missing"])[:15]:
            print("  %-52s -> fehlt: %s" % (rel, ", ".join(res["missing"][rel])))
        print("\nERGEBNIS: LEGAL_LINKS_UNVOLLSTAENDIG")
        return 1
    if drift:
        # Weder gruen noch Defekt-Claim: die Prueflaeche selbst ist unklar.
        # Ein echter Defekt schlaegt Unmessbarkeit (Merkregel Ticket 17),
        # deshalb steht dieser Zweig NACH dem Defekt-Zweig.
        print("\nERGEBNIS: LEGAL_LINKS_UNGEPRUEFT (Prueflaeche nicht deckungsgleich)")
        return 2
    print("\nERGEBNIS: LEGAL_LINKS_OK")
    return 0


HTML_OK = (
    "<html><body>" + "x" * 500 +
    "<a href='/new-business/impressum.html'>Impressum</a>"
    "<a href='/new-business/datenschutz.html'>Datenschutz</a>"
    "<a href='/new-business/agb.html'>AGB</a></body></html>"
)
HTML_BAD = (
    "<html><body>" + "x" * 500 +
    "<a href='/new-business/impressum.html'>Impressum</a></body></html>"
)
HTML_REDIRECT = "<html><head><meta http-equiv=\"refresh\" content=\"0; url=/x\"></head></html>"


def selftest() -> int:
    """Fault Injection: der Pruefer MUSS rot werden koennen (Map-Notiz 'Pruefer pruefen')."""
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        checks.append((name, bool(cond), detail))

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "blog"), exist_ok=True)
        # 1 gute Seite
        open(os.path.join(tmp, "gut.html"), "w", encoding="utf-8").write(HTML_OK)
        res = audit_tree(tmp, check_drift=False)
        check("gute Seite -> kein Fund", not res["missing"], str(res["missing"]))
        check("gute Seite wird geprueft", res["checked"] == ["gut.html"], str(res["checked"]))

        # 1 kaputte Seite MUSS gefunden werden
        open(os.path.join(tmp, "blog", "kaputt.html"), "w", encoding="utf-8").write(HTML_BAD)
        res = audit_tree(tmp, check_drift=False)
        check("kaputte Seite erkannt", "blog/kaputt.html" in res["missing"], str(res["missing"]))
        miss = res["missing"].get("blog/kaputt.html", [])
        check("fehlende Links korrekt benannt",
              sorted(miss) == ["agb.html", "datenschutz.html"], str(miss))

        # Redirect wird ausgenommen, nicht als Defekt gemeldet
        open(os.path.join(tmp, "redir.html"), "w", encoding="utf-8").write(HTML_REDIRECT)
        res = audit_tree(tmp, check_drift=False)
        check("Redirect ausgenommen", "redir.html" not in res["missing"], str(res["missing"]))
        check("Redirect als exempt gelistet",
              any(r[0] == "redir.html" for r in res["exempt"]), str(res["exempt"]))

        # Rechtsseite selbst wird ausgenommen
        open(os.path.join(tmp, "impressum.html"), "w", encoding="utf-8").write("<html>" + "y" * 600 + "</html>")
        res = audit_tree(tmp, check_drift=False)
        check("Rechtsseite ausgenommen", "impressum.html" not in res["missing"], str(res["missing"]))

        # Exit-Code-Falle (Map-Notiz): rc muss 1 sein, solange ein Defekt existiert
        check("rc=1 bei Defekt", print_report(res) == 1)

        # und 0, wenn der Defekt weg ist
        os.remove(os.path.join(tmp, "blog", "kaputt.html"))
        res = audit_tree(tmp, check_drift=False)
        check("rc=0 wenn sauber", print_report(res) == 0)

        # --- Ticket 29: die Zielmenge muss MIT DEM BAUM WACHSEN -------------
        # Genau hier war der Prueferblind: ein neues Unterverzeichnis entsteht
        # (traffic_engine erzeugt laufend welche) und liegt ausserhalb jeder
        # hartkodierten Glob-Zeile.
        tief = os.path.join(tmp, "seo", "ein-buch", "analyse")
        os.makedirs(tief, exist_ok=True)
        open(os.path.join(tief, "index.html"), "w", encoding="utf-8").write(HTML_BAD)
        res = audit_tree(tmp, check_drift=False)
        check("T29: Seite in NEUEM Unterverzeichnis wird gefunden",
              "seo/ein-buch/analyse/index.html" in res["missing"], str(sorted(res["missing"])))
        check("T29: rc=1 fuer tiefe kaputte Seite", print_report(res) == 1)

        # Dieselbe Seite MIT Links muss gruen sein (sonst waere der Fund oben
        # nur ein Artefakt der Verzeichnistiefe).
        open(os.path.join(tief, "index.html"), "w", encoding="utf-8").write(HTML_OK)
        res = audit_tree(tmp, check_drift=False)
        check("T29: tiefe Seite mit Links -> gruen", not res["missing"], str(res["missing"]))
        check("T29: tiefe Seite steht in checked",
              "seo/ein-buch/analyse/index.html" in res["checked"], str(res["checked"]))

        # dl/ = bezahlte Kundenware -> ausgenommen, aber BENANNT
        os.makedirs(os.path.join(tmp, "dl", "rtd"), exist_ok=True)
        open(os.path.join(tmp, "dl", "rtd", "abc.html"), "w", encoding="utf-8").write(HTML_BAD)
        res = audit_tree(tmp, check_drift=False)
        check("T29: dl/ ausgenommen", "dl/rtd/abc.html" not in res["missing"], str(res["missing"]))
        check("T29: dl/-Ausnahme ist begruendet",
              any(r[0] == "dl/rtd/abc.html" and "dl/" in r[1] for r in res["exempt"]),
              str(res["exempt"]))

        # Deckungsabgleich: tmp ist KEIN git-Repo -> unmessbar, nicht gruen
        res = audit_tree(tmp, check_drift=True)
        check("T29: Drift-Status gesetzt, wenn Tree nicht lesbar", res["drift"] is not None,
              str(res["drift"]))
        rc_unmessbar = print_report(res)
        check("T29: unmessbare Prueflaeche -> rc=2, NICHT 0", rc_unmessbar == 2, "rc=%s" % rc_unmessbar)

        # tree_drift hat ZWEI Unmessbar-Zweige. Die Fixture erreicht nur den
        # einen (git rc!=0); der andere (git-Binary fehlt) blieb ungetestet --
        # aufgefallen erst durch _mutation_probe_t29.py, dessen Mutant dort
        # gruen durchkam. Ein Zweig, der nie ausgefuehrt wird, ist ein
        # Falsch-Gruen-Kandidat, also wird er hier injiziert.
        import legal_targets as _lt
        status_rc, _, _ = _lt.tree_drift(tmp, [])
        check("T29: kein git-Repo -> unmessbar", status_rc.startswith("unmessbar"), status_rc)
        _orig_run = _lt.subprocess.run
        try:
            def _boom(*a, **k):
                raise OSError("git-Binary fehlt (injiziert)")
            _lt.subprocess.run = _boom
            status_missing, _, _ = _lt.tree_drift(tmp, [])
        finally:
            _lt.subprocess.run = _orig_run
        check("T29: fehlendes git-Binary -> unmessbar, nicht 'ok'",
              status_missing.startswith("unmessbar"), status_missing)

        # Echter Defekt schlaegt Unmessbarkeit (Merkregel Ticket 17)
        open(os.path.join(tmp, "blog", "kaputt2.html"), "w", encoding="utf-8").write(HTML_BAD)
        res = audit_tree(tmp, check_drift=True)
        rc_beides = print_report(res)
        check("T29: Defekt schlaegt Unmessbarkeit -> rc=1", rc_beides == 1, "rc=%s" % rc_beides)
        os.remove(os.path.join(tmp, "blog", "kaputt2.html"))

    ok = sum(1 for _, c, _ in checks if c)
    print("\n== SELFTEST %d/%d ==" % (ok, len(checks)))
    for name, cond, detail in checks:
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, "" if cond else "  -> " + detail))
    return 0 if ok == len(checks) else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    res = audit_tree(repo_root())
    return print_report(res)


if __name__ == "__main__":
    raise SystemExit(main())
