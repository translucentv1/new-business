"""Backfill der drei Pflicht-Rechtslinks auf allen ausgelieferten Seiten (Ticket 29).

Warum:
  legal_link_audit.py (seit Ticket 29 rekursiv) meldet 1201 von 1258 geprueften
  Seiten OHNE Impressum-/Datenschutz-/AGB-Link. Betroffen sind genau die Seiten,
  auf denen ein Suchbesucher landen soll (seo/ 693, t/ 468) plus die
  numerischen Produkt-Landingpages MIT Kaufbutton. § 5 DDG verlangt das
  Impressum "leicht erkennbar, unmittelbar erreichbar und staendig verfuegbar",
  Art. 13 DSGVO die Datenschutzinformation -- nicht nur auf der Startseite.

Merkregel Ticket 20 (Massen-Patch braucht einen Rueckbau-Beweis):
  Der eingefuegte Block ist durch ein Markerpaar exakt begrenzt und wird
  BYTEWEISE eingefuegt (keine Text-Normalisierung, CRLF bleibt CRLF).
  `--revert` entfernt genau diese Bytes wieder. `--probe` faehrt apply+revert
  ueber den ECHTEN Baum und vergleicht sha256 jeder Datei vorher/nachher --
  erst wenn dieser Rueckbau bitgenau ist, darf `--apply` laufen.

Nutzung:
  python scripts/request_delivery/backfill_legal_links.py            # dry-run
  python scripts/request_delivery/backfill_legal_links.py --probe    # Rueckbau-Beweis
  python scripts/request_delivery/backfill_legal_links.py --apply
  python scripts/request_delivery/backfill_legal_links.py --revert
  python scripts/request_delivery/backfill_legal_links.py --selftest
"""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from legal_targets import (  # noqa: E402
    REQUIRED,
    is_exempt,
    iter_html,
    missing_links,
    repo_root,
)

START = b"<!-- LEGAL:v1 -->"
END = b"<!-- /LEGAL:v1 -->"

# Absolute Pfade: die Seiten liegen auf bis zu drei Ebenen (t/<produkt>/<stadt>/),
# ein relativer Pfad waere je Ebene anders und damit eine neue Fehlerquelle.
BLOCK = (
    START
    + b'<p id="legal-footer" style="margin-top:2em;padding-top:1em;'
    + b'border-top:1px solid #eee;font-size:.85rem;color:#666">'
    + b'<a href="/new-business/impressum.html">Impressum</a> &middot; '
    + b'<a href="/new-business/datenschutz.html">Datenschutz</a> &middot; '
    + b'<a href="/new-business/agb.html">AGB</a></p>'
    + END
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def insert_block(data: bytes) -> bytes:
    """Block vor dem LETZTEN </body> einfuegen, sonst anhaengen.

    Arbeitet auf Bytes: die Datei wird an genau einer Stelle aufgetrennt und
    wieder zusammengesetzt. Alles andere (Zeilenenden, Encoding, BOM) bleibt
    unveraendert -- Voraussetzung fuer den bitgenauen Rueckbau.
    """
    if START in data:
        return data
    idx = data.lower().rfind(b"</body>")
    if idx < 0:
        return data + BLOCK
    return data[:idx] + BLOCK + data[idx:]


def remove_block(data: bytes) -> bytes:
    """Alle Marker-Bloecke entfernen (auch mehrfach eingefuegte)."""
    out = data
    while True:
        s = out.find(START)
        if s < 0:
            return out
        e = out.find(END, s)
        if e < 0:
            return out
        out = out[:s] + out[e + len(END):]


def targets(root: str) -> list[str]:
    """Seiten, denen mindestens ein Pflichtlink fehlt (ohne die Ausnahmen)."""
    out = []
    for rel in iter_html(root):
        path = os.path.join(root, rel)
        try:
            raw = open(path, "rb").read()
        except OSError:
            continue
        text = raw.decode("utf-8", errors="replace")
        exempt, _why = is_exempt(rel, text)
        if exempt:
            continue
        if missing_links(text):
            out.append(rel)
    return out


def run(root: str, mode: str, verbose: bool = True) -> dict:
    """mode: 'dry' | 'apply' | 'revert'."""
    if mode == "revert":
        rels = [r for r in iter_html(root) if START in open(os.path.join(root, r), "rb").read()]
    else:
        rels = targets(root)
    changed = 0
    for rel in rels:
        path = os.path.join(root, rel)
        raw = open(path, "rb").read()
        new = remove_block(raw) if mode == "revert" else insert_block(raw)
        if new == raw:
            continue
        changed += 1
        if mode != "dry":
            with open(path, "wb") as fh:
                fh.write(new)
    if verbose:
        print("Modus           = %s" % mode)
        print("Kandidaten      = %d Seiten" % len(rels))
        print("veraendert      = %d Seiten" % changed)
    return {"rels": rels, "changed": changed}


def probe(root: str) -> int:
    """Rueckbau-Beweis auf dem ECHTEN Baum: apply -> revert -> sha256-Vergleich."""
    rels = targets(root)
    before = {}
    for rel in rels:
        before[rel] = _sha(open(os.path.join(root, rel), "rb").read())
    print("Integritaetssonde ueber %d Seiten" % len(rels))
    run(root, "apply", verbose=False)
    veraendert = sum(
        1 for rel in rels if _sha(open(os.path.join(root, rel), "rb").read()) != before[rel]
    )
    print("  nach apply veraendert   = %d/%d" % (veraendert, len(rels)))
    run(root, "revert", verbose=False)
    abweichler = [
        rel for rel in rels if _sha(open(os.path.join(root, rel), "rb").read()) != before[rel]
    ]
    print("  nach revert abweichend  = %d" % len(abweichler))
    for rel in abweichler[:10]:
        print("    NICHT bitgenau: %s" % rel)
    if veraendert != len(rels) or abweichler:
        print("\nERGEBNIS: BACKFILL_PROBE_DEFEKT")
        return 1
    print("\nERGEBNIS: BACKFILL_PROBE_OK (Rueckbau bitgenau)")
    return 0


HTML_CRLF = (
    b"<!DOCTYPE html>\r\n<html><head><title>x</title></head>\r\n<body>\r\n"
    + b"<p>" + b"Inhalt " * 60 + b"</p>\r\n</body></html>\r\n"
)
HTML_LF = HTML_CRLF.replace(b"\r\n", b"\n")
HTML_UPPER = HTML_CRLF.replace(b"</body>", b"</BODY>")
HTML_NOBODY = b"<html><p>" + b"kein body tag " * 40 + b"</p></html>"
HTML_GOOD = HTML_CRLF.replace(
    b"</body>",
    b'<a href="/new-business/impressum.html">I</a>'
    b'<a href="/new-business/datenschutz.html">D</a>'
    b'<a href="/new-business/agb.html">A</a></body>',
)
HTML_REDIRECT = b'<html><head><meta http-equiv="refresh" content="0;url=/x"></head><body>' + b"x" * 500 + b"</body></html>"


def selftest() -> int:
    import legal_link_audit

    res: list[tuple[bool, str]] = []

    def chk(cond, label):
        res.append((bool(cond), label))

    with tempfile.TemporaryDirectory() as tmp:
        files = {
            "seo/tief/index.html": HTML_CRLF,
            "t/a/b/index.html": HTML_LF,
            "upper.html": HTML_UPPER,
            "nobody.html": HTML_NOBODY,
            "gut.html": HTML_GOOD,
            "redirect.html": HTML_REDIRECT,
            "dl/rtd/kunde.html": HTML_CRLF,
            "impressum.html": HTML_CRLF,
            "datenschutz.html": HTML_CRLF,
            "agb.html": HTML_CRLF,
        }
        for rel, data in files.items():
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p) or tmp, exist_ok=True)
            open(p, "wb").write(data)
        orig = {rel: _sha(data) for rel, data in files.items()}

        # ROT-Vorbedingung: der Pruefer muss die Lage VORHER als Defekt sehen,
        # sonst beweist ein gruenes Nachher nichts (Merkregel Ticket 16).
        vorher = legal_link_audit.audit_tree(tmp, check_drift=False)
        chk(len(vorher["missing"]) == 4, "Vorher: 4 Seiten unvollstaendig (rote Ausgangslage)")
        chk("gut.html" not in vorher["missing"], "Vorher: gute Seite nicht bemaengelt")
        chk("dl/rtd/kunde.html" not in vorher["checked"], "dl/ gar nicht erst geprueft")

        tgt = targets(tmp)
        chk(len(tgt) == 4, "Zielmenge = 4 (Ausnahmen und gute Seite raus), ist %d" % len(tgt))
        chk("seo/tief/index.html" in tgt, "tiefe seo-Seite in der Zielmenge")
        chk("t/a/b/index.html" in tgt, "dreistufige t-Seite in der Zielmenge")
        chk("dl/rtd/kunde.html" not in tgt, "dl/ NICHT in der Zielmenge")
        chk("redirect.html" not in tgt, "Redirect NICHT in der Zielmenge")
        chk("gut.html" not in tgt, "Seite mit allen Links NICHT in der Zielmenge")

        run(tmp, "apply", verbose=False)
        crlf = open(os.path.join(tmp, "seo/tief/index.html"), "rb").read()
        lf = open(os.path.join(tmp, "t/a/b/index.html"), "rb").read()
        upper = open(os.path.join(tmp, "upper.html"), "rb").read()
        nobody = open(os.path.join(tmp, "nobody.html"), "rb").read()
        chk(all(r.encode() in crlf for r in REQUIRED), "alle 3 Pflichtlinks im Block")
        chk(crlf.index(BLOCK) < crlf.lower().rindex(b"</body>"), "Block steht VOR </body>")
        chk(b"\r\n" in crlf and b"\n\r" not in crlf, "CRLF-Datei behaelt CRLF")
        chk(b"\r\n" not in lf, "LF-Datei bekommt KEIN CRLF")
        chk(b"</BODY>" in upper and BLOCK in upper, "Grossschreibung </BODY> erkannt+erhalten")
        chk(upper.index(BLOCK) < upper.index(b"</BODY>"), "Block vor </BODY> (Grossschreibung)")
        chk(nobody.endswith(BLOCK), "Datei ohne </body>: Block angehaengt")
        chk(_sha(open(os.path.join(tmp, "gut.html"), "rb").read()) == orig["gut.html"],
            "gute Seite bitgenau unveraendert")
        chk(_sha(open(os.path.join(tmp, "dl/rtd/kunde.html"), "rb").read()) == orig["dl/rtd/kunde.html"],
            "dl/-Seite bitgenau unveraendert")
        chk(_sha(open(os.path.join(tmp, "redirect.html"), "rb").read()) == orig["redirect.html"],
            "Redirect bitgenau unveraendert")

        nach = legal_link_audit.audit_tree(tmp, check_drift=False)
        chk(len(nach["missing"]) == 0, "Nachher: 0 unvollstaendig (rc-Wechsel 1->0)")

        zweit = run(tmp, "apply", verbose=False)
        chk(zweit["changed"] == 0, "idempotent: zweiter Lauf veraendert 0 Dateien")
        chk(_sha(open(os.path.join(tmp, "seo/tief/index.html"), "rb").read()) == _sha(crlf),
            "idempotent: Datei nach 2. Lauf identisch")

        run(tmp, "revert", verbose=False)
        exakt = [rel for rel, sha in orig.items()
                 if _sha(open(os.path.join(tmp, rel), "rb").read()) != sha]
        chk(not exakt, "Rueckbau bitgenau fuer ALLE %d Dateien (Abweichler: %s)" % (len(orig), exakt))
        zurueck = legal_link_audit.audit_tree(tmp, check_drift=False)
        chk(len(zurueck["missing"]) == 4, "nach Rueckbau wieder rot (Pruefer haengt nicht am Marker)")

        # Doppelt eingefuegter Block wird vollstaendig zurueckgebaut.
        p = os.path.join(tmp, "seo/tief/index.html")
        # ACHTUNG: open(p,"wb") truncatet SOFORT -- erst lesen, dann oeffnen.
        vorhanden = open(p, "rb").read()
        open(p, "wb").write(BLOCK + vorhanden + BLOCK)
        run(tmp, "revert", verbose=False)
        chk(_sha(open(p, "rb").read()) == orig["seo/tief/index.html"],
            "doppelter Block vollstaendig entfernt")

    ok = sum(1 for good, _ in res if good)
    print("\n== SELFTEST %d/%d ==" % (ok, len(res)))
    for good, label in res:
        print("  [%s] %s" % ("OK" if good else "FAIL", label))
    if ok != len(res):
        print("\nERGEBNIS: SELFTEST_DEFEKT")
        return 1
    print("\nERGEBNIS: SELFTEST_OK")
    return 0


def main(argv: list[str]) -> int:
    root = repo_root()
    if "--selftest" in argv:
        return selftest()
    if "--probe" in argv:
        return probe(root)
    if "--apply" in argv:
        run(root, "apply")
        return 0
    if "--revert" in argv:
        run(root, "revert")
        return 0
    run(root, "dry")
    print("(dry-run: nichts geschrieben; --probe fuer den Rueckbau-Beweis, dann --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
