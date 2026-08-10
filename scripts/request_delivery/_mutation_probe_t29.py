"""Mutationsprobe Ticket 29 -- Rechtslink-Prueferblindheit.

Zwei Teile, beide AUSGEFUEHRT statt argumentiert:

[A] ALT-STAND-PROBE: die HEAD-Fassung von legal_link_audit.py wird gegen eine
    Fixture gefahren, in der eine Seite in einem NEUEN Unterverzeichnis liegt
    und keinen einzigen Rechtslink traegt. Erwartet: rc=0 / LEGAL_LINKS_OK
    -> der Pruefer war blind. Die neue Fassung gegen dieselbe Fixture: rc=1.

[B] MUTANTEN: der PRODUKTIVCODE (legal_targets.py) wird mutiert; der Selftest
    von legal_link_audit.py MUSS jedesmal rot werden, ohne Traceback. Danach
    wird die Datei sha256-genau wiederhergestellt.

Hinweis zur Namensgleichheit: evidence/_t29_probe*.py gehoeren zum parallelen
SEO-Tick (Doorway-Deindex), nicht zu diesem Ticket.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_REL = "scripts/request_delivery/legal_link_audit.py"
TARGETS_REL = "scripts/request_delivery/legal_targets.py"

HTML_OK = (
    "<html><body>" + "x" * 500
    + "<a href='/new-business/impressum.html'>Impressum</a>"
    + "<a href='/new-business/datenschutz.html'>Datenschutz</a>"
    + "<a href='/new-business/agb.html'>AGB</a></body></html>"
)
HTML_BAD = "<html><body>" + "x" * 500 + "<p>keine Rechtslinks</p></body></html>"

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, "" if cond else "  -> " + detail))


def sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def build_fixture(tmp: str, audit_src: bytes, with_targets: bool) -> str:
    """Fixture-Baum: root/gut.html (mit Links) + seo/ein-buch/analyse/index.html (ohne)."""
    pkg = os.path.join(tmp, "scripts", "request_delivery")
    os.makedirs(pkg, exist_ok=True)
    open(os.path.join(pkg, "legal_link_audit.py"), "wb").write(audit_src)
    if with_targets:
        shutil.copyfile(os.path.join(ROOT, TARGETS_REL), os.path.join(pkg, "legal_targets.py"))
    open(os.path.join(tmp, "gut.html"), "w", encoding="utf-8").write(HTML_OK)
    tief = os.path.join(tmp, "seo", "ein-buch", "analyse")
    os.makedirs(tief, exist_ok=True)
    open(os.path.join(tief, "index.html"), "w", encoding="utf-8").write(HTML_BAD)
    return os.path.join(pkg, "legal_link_audit.py")


def run(args: list[str], cwd: str | None = None) -> tuple[int, str]:
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True,
                       cwd=cwd, timeout=300)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def ergebniswort(out: str) -> str:
    """Erstes Token der ERGEBNIS-Zeile -- exakt, nicht per Substring (Ticket 19)."""
    for line in out.splitlines():
        if line.startswith("ERGEBNIS:"):
            return line.split(":", 1)[1].strip().split()[0]
    return "(keine ERGEBNIS-Zeile)"


def teil_a() -> None:
    print("\n[A] ALT-STAND-PROBE (HEAD-Fassung gegen neu entstandenes Unterverzeichnis)")
    alt = subprocess.run(["git", "show", "HEAD:" + AUDIT_REL], cwd=ROOT,
                         capture_output=True, timeout=60)
    check("HEAD-Fassung lesbar", alt.returncode == 0 and len(alt.stdout) > 1000,
          "rc=%d len=%d" % (alt.returncode, len(alt.stdout)))
    if alt.returncode != 0:
        return

    with tempfile.TemporaryDirectory() as tmp:
        script = build_fixture(tmp, alt.stdout, with_targets=False)
        rc, out = run([script])
        wort = ergebniswort(out)
        check("Alt-Stand laeuft ueberhaupt (kein Absturz)", "Traceback" not in out, out[-300:])
        check("Alt-Stand meldet GRUEN fuer eine Seite ohne Rechtslinks -> WAR BLIND",
              rc == 0 and wort == "LEGAL_LINKS_OK", "rc=%d wort=%s" % (rc, wort))
        # Beleg, dass die tiefe Seite gar nicht erst betrachtet wurde:
        check("Alt-Stand prueft nur die Wurzel (1 Seite)", "geprueft        = 1" in out,
              [ln for ln in out.splitlines() if "geprueft" in ln])

    with tempfile.TemporaryDirectory() as tmp:
        neu = open(os.path.join(ROOT, AUDIT_REL), "rb").read()
        script = build_fixture(tmp, neu, with_targets=True)
        rc, out = run([script])
        wort = ergebniswort(out)
        check("Neue Fassung, dieselbe Fixture -> ROT",
              rc == 1 and wort == "LEGAL_LINKS_UNVOLLSTAENDIG", "rc=%d wort=%s" % (rc, wort))
        check("Neue Fassung benennt die exakte Seite",
              "seo/ein-buch/analyse/index.html" in out, out[-400:])
        check("Neue Fassung prueft 2 Seiten statt 1", "geprueft        = 2" in out,
              [ln for ln in out.splitlines() if "geprueft" in ln])


MUTANTEN: list[tuple[str, str, str]] = [
    # (Name, Suchtext, Ersatz)
    ("iter_html liefert nur die Wurzel (Alt-Verhalten)",
     "        for name in filenames:",
     "        if dirpath != root:\n            continue\n        for name in filenames:"),
    ("seo/ faelschlich als Ausnahme deklariert",
     'EXEMPT_PREFIX = ("dl/",)',
     'EXEMPT_PREFIX = ("dl/", "seo/")'),
    ("missing_links meldet nie etwas",
     "    return [r for r in REQUIRED if r not in text]",
     "    return []"),
    ("Pflicht-SET auf ein Merkmal verkuerzt (Ticket-17-Klasse)",
     'REQUIRED = ("impressum.html", "datenschutz.html", "agb.html")',
     'REQUIRED = ("impressum.html",)'),
    # Falsch-Gruen-Generator: nicht lesbarer git-Tree wird als "gedeckt"
    # ausgegeben -- genau der Zweig, der Unmessbarkeit in Gruen muenden liesse
    # (Merkregel Ticket 27/28).
    ("Deckungsabgleich meldet 'ok', obwohl git nicht lesbar ist",
     '        return "unmessbar: git nicht ausfuehrbar (%s)" % exc, [], []',
     '        return "ok", [], []'),
    ("Deckungsabgleich meldet 'ok', obwohl git rc!=0 liefert",
     '        return "unmessbar: git rc=%d" % res.returncode, [], []',
     '        return "ok", [], []'),
]


def teil_b() -> None:
    print("\n[B] MUTANTEN im Produktivcode (legal_targets.py)")
    path = os.path.join(ROOT, TARGETS_REL)
    orig_bytes = open(path, "rb").read()
    orig_sha = sha256(path)

    rc, out = run([os.path.join(ROOT, AUDIT_REL), "--selftest"], cwd=ROOT)
    check("Selftest vor Mutation gruen (rc=0)", rc == 0, "rc=%d" % rc)

    try:
        for name, alt, neu in MUTANTEN:
            src = orig_bytes.decode("utf-8")
            if alt not in src:
                check("Mutant '%s' anwendbar" % name, False, "Suchtext nicht gefunden")
                continue
            open(path, "w", encoding="utf-8", newline="").write(src.replace(alt, neu, 1))
            rc, out = run([os.path.join(ROOT, AUDIT_REL), "--selftest"], cwd=ROOT)
            check("Mutant ROT: %s" % name, rc != 0, "rc=%d" % rc)
            check("Mutant ohne Absturz: %s" % name, "Traceback" not in out, out[-300:])
            check("Mutant meldet FAIL-Zeile: %s" % name, "[FAIL]" in out, out[-300:])
            open(path, "wb").write(orig_bytes)
    finally:
        open(path, "wb").write(orig_bytes)

    check("Produktivdatei sha256-genau wiederhergestellt", sha256(path) == orig_sha,
          "%s != %s" % (sha256(path)[:12], orig_sha[:12]))
    rc, out = run([os.path.join(ROOT, AUDIT_REL), "--selftest"], cwd=ROOT)
    check("Selftest nach Wiederherstellung wieder gruen (rc 0->1->0)", rc == 0, "rc=%d" % rc)
    print("  sha256(legal_targets.py) = %s" % orig_sha[:16])


def main() -> int:
    teil_a()
    teil_b()
    ok = sum(1 for _, c, _ in results if c)
    print("\n== MUTATION_PROBE %d/%d ==" % (ok, len(results)))
    if ok == len(results):
        print("ERGEBNIS: MUTATION_PROBE_OK")
        return 0
    print("ERGEBNIS: MUTATION_PROBE_DEFEKT")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
