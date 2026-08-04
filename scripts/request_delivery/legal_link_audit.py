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

import glob
import os
import sys
import tempfile

REQUIRED = ("impressum.html", "datenschutz.html", "agb.html")

# Seiten, die bewusst keine Rechtslinks tragen (Weiterleitungen, Rechtsseiten selbst,
# generierte Kunden-Deliverables unter dl/).
EXEMPT_SUFFIX = ("impressum.html", "datenschutz.html", "agb.html")


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def is_exempt(path: str, text: str) -> tuple[bool, str]:
    base = os.path.basename(path).lower()
    if base in EXEMPT_SUFFIX:
        return True, "Rechtsseite selbst"
    low = text.lower()
    if "http-equiv=\"refresh\"" in low or "http-equiv='refresh'" in low:
        return True, "Redirect-Seite"
    if len(text) < 400:
        return True, "Stub (<400 B)"
    return False, ""


def audit_tree(root: str) -> dict:
    files = []
    for pat in ("*.html", "blog/*.html"):
        files.extend(sorted(glob.glob(os.path.join(root, pat))))
    result = {"checked": [], "exempt": [], "missing": {}}
    for f in files:
        rel = os.path.relpath(f, root).replace("\\", "/")
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except OSError as exc:  # pragma: no cover
            result["missing"][rel] = ["UNREADABLE: %s" % exc]
            continue
        exempt, why = is_exempt(f, text)
        if exempt:
            result["exempt"].append((rel, why))
            continue
        result["checked"].append(rel)
        miss = [r for r in REQUIRED if r not in text]
        if miss:
            result["missing"][rel] = miss
    return result


def print_report(res: dict) -> int:
    print("== Rechtslink-Audit (lokaler Baum) ==")
    print("geprueft        = %d Seiten" % len(res["checked"]))
    print("ausgenommen     = %d (Rechtsseiten/Redirects/Stubs)" % len(res["exempt"]))
    print("unvollstaendig  = %d" % len(res["missing"]))
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
        res = audit_tree(tmp)
        check("gute Seite -> kein Fund", not res["missing"], str(res["missing"]))
        check("gute Seite wird geprueft", res["checked"] == ["gut.html"], str(res["checked"]))

        # 1 kaputte Seite MUSS gefunden werden
        open(os.path.join(tmp, "blog", "kaputt.html"), "w", encoding="utf-8").write(HTML_BAD)
        res = audit_tree(tmp)
        check("kaputte Seite erkannt", "blog/kaputt.html" in res["missing"], str(res["missing"]))
        miss = res["missing"].get("blog/kaputt.html", [])
        check("fehlende Links korrekt benannt",
              sorted(miss) == ["agb.html", "datenschutz.html"], str(miss))

        # Redirect wird ausgenommen, nicht als Defekt gemeldet
        open(os.path.join(tmp, "redir.html"), "w", encoding="utf-8").write(HTML_REDIRECT)
        res = audit_tree(tmp)
        check("Redirect ausgenommen", "redir.html" not in res["missing"], str(res["missing"]))
        check("Redirect als exempt gelistet",
              any(r[0] == "redir.html" for r in res["exempt"]), str(res["exempt"]))

        # Rechtsseite selbst wird ausgenommen
        open(os.path.join(tmp, "impressum.html"), "w", encoding="utf-8").write("<html>" + "y" * 600 + "</html>")
        res = audit_tree(tmp)
        check("Rechtsseite ausgenommen", "impressum.html" not in res["missing"], str(res["missing"]))

        # Exit-Code-Falle (Map-Notiz): rc muss 1 sein, solange ein Defekt existiert
        check("rc=1 bei Defekt", print_report(res) == 1)

        # und 0, wenn der Defekt weg ist
        os.remove(os.path.join(tmp, "blog", "kaputt.html"))
        res = audit_tree(tmp)
        check("rc=0 wenn sauber", print_report(res) == 0)

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
