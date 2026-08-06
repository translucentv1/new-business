#!/usr/bin/env python3
"""Ticket 20 — Indexier-Schutz der BEZAHLTEN Kundenware unter /dl/.

WARUM DAS UEBERHAUPT NOETIG IST (MEASURED 2026-08-06):
Der einzige robots.txt, den ein Crawler liest, ist der des ORIGINS:
    https://translucentv1.github.io/robots.txt  -> HTTP 404
Das repo-eigene .../new-business/robots.txt (HTTP 200, mit "Disallow: /dl/")
liegt NICHT im top-level path und wird deshalb von keinem Crawler gelesen.
Primaerquelle RFC 9309 (rfc-editor.org, HTTP 200 abgerufen):
  §2.3    "The rules MUST be accessible in a file named '/robots.txt' (all
           lowercase) in the top-level path of the service."
  §2.3.1.3 4xx = "Unavailable" -> "the crawler MAY access any resources".
=> /dl/ ist crawlbar. Der EINZIGE verbliebene Schutz der bezahlten Ware ist
   <meta name="robots" content="noindex..."> in der ausgelieferten Seite.

Ergebniswoerter (Merkregel Ticket 16/17/18: "nicht messbar" braucht ein eigenes
Wort, sonst wird es als gruen oder als Defekt fehlgelesen):
    DL_NOINDEX_OK        rc=0
    DL_NOINDEX_DEFEKT    rc=1   (echter Defekt schlaegt Unmessbarkeit)
    DL_UNGEPRUEFT        rc=2   (Netzfehler, oder leere Zielmenge)

Aufruf:
    python scripts/request_delivery/dl_noindex_audit.py            # Baum
    python scripts/request_delivery/dl_noindex_audit.py --live     # Auslieferung
    python scripts/request_delivery/dl_noindex_audit.py --fix      # patchen
    python scripts/request_delivery/dl_noindex_audit.py --selftest
"""

import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SITE = "https://translucentv1.github.io/new-business"

ROBOTS_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)', re.IGNORECASE
)
# Anker fuer den Patch: die charset-Zeile gibt es in BEIDEN im Baum real
# vorkommenden head-Formen (mehrzeilig eingerueckt und einzeilig).
CHARSET_RE = re.compile(r'<meta\s+charset=["\']?utf-8["\']?\s*/?>',
                        re.IGNORECASE)
NOINDEX_TAG = '<meta name="robots" content="noindex,nofollow">'


def dl_dir():
    return os.path.join(ROOT, "dl")


def targets():
    """Zielmenge aus der QUELLE abgeleitet, nie hartkodiert (Merkregel T17)."""
    base = dl_dir()
    out = []
    for dirpath, _dirnames, filenames in os.walk(base):
        for fname in filenames:
            if fname.lower().endswith(".html"):
                full = os.path.join(dirpath, fname)
                out.append(os.path.relpath(full, ROOT).replace("\\", "/"))
    return sorted(out)


def binaries():
    """Dateien, die per meta robots GRUNDSAETZLICH nicht schuetzbar sind."""
    base = dl_dir()
    out = []
    for dirpath, _dirnames, filenames in os.walk(base):
        for fname in filenames:
            if not fname.lower().endswith((".html", ".md", ".txt")):
                full = os.path.join(dirpath, fname)
                out.append(os.path.relpath(full, ROOT).replace("\\", "/"))
    return sorted(out)


def has_noindex(text):
    m = ROBOTS_RE.search(text)
    if not m:
        return False, None
    val = m.group(1).strip().lower()
    return ("noindex" in val), val


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def http(url):
    """(status, body). Ungekuerzt - eine Attrappe muss denselben Vertrag
    nachbilden (Attrappen-Falle, Ticket 19)."""
    req = urllib.request.Request(url, method="GET")
    req.add_header("Cache-Control", "no-store")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return f"ERR:{e}", ""


def patch_text(text):
    """(neuer_text, ok). ok=False -> Anker fehlt, NICHT blind einfuegen."""
    ok, _val = has_noindex(text)
    if ok:
        return text, True
    m = CHARSET_RE.search(text)
    if not m:
        return text, False
    end = m.end()
    # Einrueckung/Zeilenform der Umgebung uebernehmen
    nl = "\r\n" if "\r\n" in text[:end] else "\n"
    indent = ""
    line_start = text.rfind("\n", 0, m.start()) + 1
    lead = text[line_start:m.start()]
    if lead.strip() == "":
        indent = lead
    if text[end:end + 1] in ("\r", "\n"):
        ins = nl + indent + NOINDEX_TAG
        return text[:end] + ins + text[end:], True
    return text[:end] + NOINDEX_TAG + text[end:], True


def main():
    live = "--live" in sys.argv
    fix = "--fix" in sys.argv
    scope = "LIVE-Auslieferung" if live else "lokaler Baum (kein Netz)"
    print("== Ticket 20: Indexier-Schutz der Kundenware unter /dl/ ==")
    print(f"Geltungsbereich   = {scope}")
    print("Grund             = Origin-robots.txt ist 404 -> /dl/ crawlbar "
          "(RFC 9309 §2.3)")

    files = targets()
    bins = binaries()
    if not files:
        # Leere Zielmenge ist NICHT gruen (Merkregel Ticket 17).
        print("\nERGEBNIS: DL_UNGEPRUEFT (keine dl/*.html gefunden - "
              "Zielmenge leer, es ist nichts belegt)")
        return 2

    patched, deviants = [], []
    if fix:
        for rel in files:
            text = read(rel)
            new, ok = patch_text(text)
            if not ok:
                deviants.append(rel)
                continue
            if new != text:
                with open(os.path.join(ROOT, rel), "w", encoding="utf-8",
                          newline="") as fh:
                    fh.write(new)
                patched.append(rel)
        print(f"gepatcht          = {len(patched)}")
        if deviants:
            print(f"ABWEICHER (kein charset-Anker, NICHT angefasst) = "
                  f"{len(deviants)}")
            for rel in deviants:
                print("   ", rel)

    unprotected, unmeasured = [], []
    if live:
        def check(rel):
            st, body = http(f"{SITE}/{rel}")
            if isinstance(st, str) or st != 200:
                return rel, None, st
            ok, val = has_noindex(body)
            return rel, ok, val

        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(check, files))
        for rel, ok, info in results:
            if ok is None:
                unmeasured.append((rel, info))
            elif not ok:
                unprotected.append(rel)
    else:
        for rel in files:
            ok, _val = has_noindex(read(rel))
            if not ok:
                unprotected.append(rel)

    print(f"\ngeprueft          = {len(files)} dl-HTML-Dateien")
    print(f"OHNE noindex      = {len(unprotected)}")
    if unmeasured:
        print(f"nicht messbar     = {len(unmeasured)}")
        for rel, info in unmeasured[:10]:
            print(f"    {rel}  {info}")
    for rel in unprotected[:25]:
        print(f"    OFFEN  {rel}")

    if bins:
        print(f"\nHINWEIS: {len(bins)} Nicht-HTML-Dateien unter /dl/ "
              "(z.B. .epub) koennen KEIN meta robots tragen.")
        print("  Sie bleiben crawlbar, solange der Origin kein robots.txt hat"
              " - per meta nicht schliessbar (eigenes Ticket).")

    if unprotected:
        print(f"\nERGEBNIS: DL_NOINDEX_DEFEKT ({len(unprotected)} bezahlte "
              "Deliverables sind indexierbar)")
        return 1
    if unmeasured:
        print(f"\nERGEBNIS: DL_UNGEPRUEFT ({len(unmeasured)} Dateien nicht "
              "abrufbar - kein Defekt behauptet)")
        return 2
    print(f"\nERGEBNIS: DL_NOINDEX_OK ({len(files)} Deliverables tragen "
          "noindex, Geltungsbereich: " + scope + ")")
    return 0


# --------------------------------------------------------------------------
def _selftest():
    """Fault Injection durch die ECHTE main() - kein Reimplementat."""
    import contextlib
    import io
    import shutil
    import tempfile

    g = globals()
    results = []

    def t(cond, name, detail=""):
        results.append((cond, name))
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}"
              + (f" | {detail}" if detail else ""))

    HEAD_MULTI = ('<!DOCTYPE html>\r\n<html lang="de">\r\n<head>\r\n'
                  '  <meta charset="utf-8">\r\n'
                  '  <title>T</title>\r\n</head><body>x</body></html>')
    HEAD_ONELINE = ('<!DOCTYPE html><html lang="de"><head>'
                    '<meta charset="utf-8"><title>T</title>'
                    "</head><body>x</body></html>")
    NO_ANCHOR = "<html><head><title>kein charset</title></head><body>x</body>"

    def build(tmp, files, bins=()):
        base = os.path.join(tmp, "dl")
        for i, content in enumerate(files):
            d = os.path.join(base, f"h{i}")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"f{i}.html"), "w", encoding="utf-8",
                      newline="") as fh:
                fh.write(content)
        for i, _b in enumerate(bins):
            d = os.path.join(base, f"b{i}")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"b{i}.epub"), "wb") as fh:
                fh.write(b"PK\x03\x04")
        return base

    def run(files, bins=(), argv=(), fake_http=None):
        tmp = tempfile.mkdtemp(prefix="dlaudit-")
        build(tmp, files, bins)
        keep_root, keep_http, keep_argv = g["ROOT"], g["http"], sys.argv
        g["ROOT"] = tmp
        if fake_http is not None:
            g["http"] = fake_http
        sys.argv = ["x", *argv]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = main()
        except Exception as e:  # noqa: BLE001
            buf.write(f"\nTraceback-ersatz: {e!r}")
            rc = 99
        finally:
            g["ROOT"], g["http"], sys.argv = keep_root, keep_http, keep_argv
            shutil.rmtree(tmp, ignore_errors=True)
        return rc, buf.getvalue(), tmp

    def word(out):
        for line in out.splitlines():
            if line.startswith("ERGEBNIS:"):
                return line.split()[1]
        return "(kein Ergebniswort)"

    print("== dl_noindex_audit --selftest (Fault Injection, offline) ==")

    good = HEAD_MULTI.replace("  <title>", f"  {NOINDEX_TAG}\r\n  <title>")
    rc, out, _ = run([good])
    t(rc == 0 and word(out) == "DL_NOINDEX_OK", "alles geschuetzt -> gruen",
      f"rc={rc} {word(out)}")

    rc, out, _ = run([HEAD_MULTI])
    t(rc == 1 and word(out) == "DL_NOINDEX_DEFEKT",
      "eine Datei ohne noindex -> rot", f"rc={rc} {word(out)}")
    t("indexierbar" in out, "Diagnose nennt die Folge (indexierbar)")

    rc, out, _ = run([good, HEAD_MULTI, good])
    t(rc == 1 and "OHNE noindex      = 1" in out,
      "Mischbestand: genau 1 Luecke gezaehlt", f"rc={rc}")

    # Teil-Vollstaendigkeits-Falle: viele gruene duerfen eine Luecke nicht decken
    rc, out, _ = run([good] * 20 + [HEAD_MULTI])
    t(rc == 1, "20 gruene + 1 Luecke -> trotzdem rot", f"rc={rc}")

    rc, out, _ = run([])
    t(rc == 2 and word(out) == "DL_UNGEPRUEFT",
      "leere Zielmenge ist NICHT gruen", f"rc={rc} {word(out)}")

    # noindex vorhanden, aber wertlos ("index,follow")
    idx = HEAD_MULTI.replace(
        "  <title>", '  <meta name="robots" content="index,follow">\r\n  <title>')
    rc, out, _ = run([idx])
    t(rc == 1, "meta robots ohne noindex -> rot", f"rc={rc}")

    # --fix auf beiden real vorkommenden head-Formen
    rc, out, _ = run([HEAD_MULTI, HEAD_ONELINE], argv=["--fix"])
    t(rc == 0 and "gepatcht          = 2" in out,
      "--fix repariert beide head-Formen -> danach gruen", f"rc={rc}")

    rc, out, _ = run([NO_ANCHOR], argv=["--fix"])
    t(rc == 1 and "ABWEICHER" in out,
      "--fix fasst Datei ohne Anker NICHT an, meldet sie", f"rc={rc}")

    # Idempotenz
    rc, out, _ = run([good], argv=["--fix"])
    t(rc == 0 and "gepatcht          = 0" in out,
      "--fix ist idempotent (nichts doppelt einfuegen)", f"rc={rc}")

    # Binaerdateien werden benannt, nicht verschwiegen
    rc, out, _ = run([good], bins=("x",))
    t("KEIN meta robots tragen" in out,
      ".epub wird als nicht schuetzbar ausgewiesen")

    # --live: Netzfehler != Defekt
    rc, out, _ = run([good], argv=["--live"],
                     fake_http=lambda _u: ("ERR:dns", ""))
    t(rc == 2 and word(out) == "DL_UNGEPRUEFT",
      "--live Netzausfall -> unmessbar, KEIN Defekt-Vorwurf",
      f"rc={rc} {word(out)}")

    # --live: echter Defekt schlaegt Unmessbarkeit
    state = {"n": 0}

    def mixed(_u):
        state["n"] += 1
        if state["n"] == 1:
            return 200, "<html><head></head><body>nackt</body></html>"
        return "ERR:dns", ""

    rc, out, _ = run([good, good], argv=["--live"], fake_http=mixed)
    t(rc == 1, "--live: echter Defekt schlaegt Unmessbarkeit", f"rc={rc}")

    # --live misst die AUSLIEFERUNG, nicht die lokale Datei
    rc, out, _ = run([good], argv=["--live"],
                     fake_http=lambda _u: (200, "<html><head></head></html>"))
    t(rc == 1, "--live: lokal gruen + live nackt -> rot (Branch-Falle)",
      f"rc={rc}")

    rc, out, _ = run([good], argv=["--live"],
                     fake_http=lambda _u: (200, good))
    t(rc == 0 and "LIVE-Auslieferung" in out,
      "--live gruen druckt Geltungsbereich LIVE", f"rc={rc}")

    rc, out, _ = run([good])
    t("lokaler Baum (kein Netz)" in out,
      "offline druckt Geltungsbereich BAUM (nicht als Live lesbar)")

    bad = [n for ok, n in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} Faelle bestanden.")
    if bad:
        print("SELFTEST_DEFEKT:")
        for n in bad:
            print("  -", n)
        return 1
    print("SELFTEST_OK")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
