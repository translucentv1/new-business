#!/usr/bin/env python3
"""Ticket 29 - RUECKBAU-PROBE (unabhaengig vom Backfill-Skript).

Frage: Ist der Massen-Patch auf ~1200 Dateien WIRKLICH nur das Einfuegen der
Sentinel-Bloecke - oder hat er nebenbei etwas anderes veraendert?

Methode (kein Vertrauen in backfill_legal_links.py / enrich_blog.py):
  Fuer jede geaenderte Datei: Arbeitsstand holen, die bekannten Sentinel-Bloecke
  per Regex ENTFERNEN, sha256 gegen die HEAD-Fassung (git show) vergleichen.
  Byte-Gleichheit == der Patch hat NICHTS ausser den Bloecken angefasst.

FALLSTRICK (v1 dieser Sonde lief hier auf Falsch-Rot, 704/1210):
  core.autocrlf=true -> Arbeitsstand hat CRLF, `git show` liefert LF.
  Roher Byte-Vergleich meldet dann JEDE Datei als veraendert. Deshalb wird
  fuer den Inhaltsvergleich auf LF normalisiert; reine Zeilenende-Drift wird
  SEPARAT gezaehlt und ausgewiesen statt stillschweigend geschluckt.

Rot ist:
  - Rueckbau != HEAD (Fremdaenderung im selben Patch)
  - Datei ohne bekannten Sentinel-Block, aber trotzdem geaendert
  - mehr als ein Block derselben Sorte (doppelter Lauf)
  - LEGAL-Block nicht vor </body> (kaputte Platzierung)
Exit: 0 = RUECKBAU_OK, 1 = RUECKBAU_DEFEKT, 2 = UNMESSBAR
"""
import hashlib
import re
import subprocess
import sys

LEGAL = re.compile(rb"<!-- LEGAL:v1 -->.*?<!-- /LEGAL:v1 -->", re.S)
# Der ENRICH-Block wird als eigene ZEILE eingefuegt. Wird nur der Block selbst
# entfernt, bleibt sein Zeilenumbruch stehen und der Rueckbau weicht um genau
# ein \n von HEAD ab (Falsch-Rot, v2 dieser Sonde lief so auf 9/9). Deshalb
# wird der vorangehende Umbruch mitkonsumiert.
ENRICH = re.compile(rb"(?:\r?\n)?<!-- ENRICH:v1 START -->.*?<!-- ENRICH:v1 END -->", re.S)
REPO = "."


def sh(args):
    return subprocess.run(args, cwd=REPO, capture_output=True)


def norm(b):
    return b.replace(b"\r\n", b"\n")


def h(b):
    return hashlib.sha256(b).hexdigest()


def main():
    r = sh(["git", "diff", "--name-only", "--diff-filter=M"])
    if r.returncode != 0:
        print("UNMESSBAR: git diff rc=%d" % r.returncode)
        return 2
    files = [f for f in r.stdout.decode("utf-8", "replace").splitlines() if f.strip()]
    if not files:
        print("UNMESSBAR: keine geaenderten Dateien - nichts zu pruefen")
        return 2

    html = [f for f in files if f.endswith(".html")]
    other = [f for f in files if not f.endswith(".html")]

    ok_legal = ok_enrich = ok_both = 0
    eol_drift = 0
    fails = []
    no_block = []

    for f in html:
        g = sh(["git", "show", "HEAD:" + f])
        if g.returncode != 0:
            fails.append((f, "HEAD-Fassung nicht lesbar"))
            continue
        head = g.stdout
        try:
            with open(f, "rb") as fh:
                work = fh.read()
        except OSError as e:
            fails.append((f, "Arbeitsstand nicht lesbar: %s" % e))
            continue

        n_l = len(LEGAL.findall(work))
        n_e = len(ENRICH.findall(work))
        if n_l == 0 and n_e == 0:
            no_block.append(f)
            continue
        if n_l > 1:
            fails.append((f, "%d LEGAL:v1-Bloecke (Doppel-Backfill)" % n_l))
            continue
        if n_e > 1:
            fails.append((f, "%d ENRICH:v1-Bloecke (Doppel-Lauf)" % n_e))
            continue

        if n_l == 1:
            m = LEGAL.search(work)
            rest = work[m.end():]
            if b"<body" in rest:
                fails.append((f, "LEGAL-Block steht VOR <body>"))
                continue
            if b"</body>" not in rest.lower():
                fails.append((f, "kein </body> nach dem LEGAL-Block"))
                continue

        rueck = ENRICH.sub(b"", LEGAL.sub(b"", work))

        if h(rueck) == h(head):
            exact = True
        elif h(norm(rueck)) == h(norm(head)):
            exact = True
            eol_drift += 1
        else:
            fails.append((f, "Rueckbau != HEAD (sha %s vs %s)" % (
                h(norm(rueck))[:12], h(norm(head))[:12])))
            continue

        if exact:
            if n_l and n_e:
                ok_both += 1
            elif n_l:
                ok_legal += 1
            else:
                ok_enrich += 1

    total_ok = ok_legal + ok_enrich + ok_both
    print("== RUECKBAU-PROBE Ticket 29 (v2, CRLF-normalisiert) ==")
    print("geaenderte Dateien gesamt   : %d" % len(files))
    print("  davon HTML                : %d" % len(html))
    print("  davon Nicht-HTML (Code)   : %d -> %s" % (len(other), other))
    print("rueckbaubar NUR LEGAL:v1    : %d" % ok_legal)
    print("rueckbaubar NUR ENRICH:v1   : %d" % ok_enrich)
    print("rueckbaubar BEIDE Bloecke   : %d" % ok_both)
    print("  davon reine CRLF/LF-Drift : %d (Inhalt identisch, git normalisiert)" % eol_drift)
    print("geaendert OHNE bekannten Block: %d" % len(no_block))
    for f in no_block[:10]:
        print("   [?] %s" % f)
    print("DEFEKT                      : %d" % len(fails))
    for f, why in fails[:20]:
        print("   [FAIL] %s -- %s" % (f, why))

    if fails or no_block:
        print("ERGEBNIS: RUECKBAU_DEFEKT")
        return 1
    if total_ok == 0:
        print("ERGEBNIS: UNMESSBAR (0 HTML geprueft)")
        return 2
    print("ERGEBNIS: RUECKBAU_OK (%d/%d HTML nur um Sentinel-Bloecke ergaenzt, "
          "0 Fremdaenderung)" % (total_ok, len(html)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
