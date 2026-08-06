"""Sonde Ticket 20: beweist, dass ein dl/-Patch NUR den noindex-Tag ergaenzt hat.

Zieht den Tag aus jeder geaenderten Datei wieder ab und vergleicht gegen den
Blob der Basis-Revision. Zeilenenden werden normalisiert - git/Windows uebersetzt
sie ohnehin, die Frage ist der INHALT.

    python _probe_patch_integrity_t20.py                 # Working Tree vs HEAD
    python _probe_patch_integrity_t20.py --base c931e44~1  # Commit nachpruefen

Ergebniswoerter:
    PATCH_INTEGRITAET_OK          rc=0
    PATCH_INTEGRITAET_DEFEKT      rc=1
    PATCH_INTEGRITAET_UNGEPRUEFT  rc=2   leere Zielmenge - nichts belegt

Leere Zielmenge ist NICHT gruen: nach dem Commit ist `git diff` leer, und ein
"OK" ueber 0 Dateien haette genau dann bestaetigt, wenn nichts geprueft wurde.
"""

import subprocess
import sys

TAG = '<meta name="robots" content="noindex,nofollow">'
CANDS = (b"\r\n  " + TAG.encode(), b"\n  " + TAG.encode(), TAG.encode())


def norm(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def strip_tag(new: bytes) -> bytes:
    for cand in CANDS:
        if cand in new:
            return new.replace(cand, b"", 1)
    return new


def main() -> int:
    argv = sys.argv[1:]
    base = argv[argv.index("--base") + 1] if "--base" in argv else None
    # Ohne --base: Working Tree gegen HEAD. Mit --base: base gegen base+Commit.
    diff = ["diff", "--name-only", *( [base] if base else [] ), "--", "dl"]
    files = git(*diff).decode().split()
    ref = base or "HEAD"
    print(f"Basis             = {ref}")

    if not files:
        print("\nERGEBNIS: PATCH_INTEGRITAET_UNGEPRUEFT (keine geaenderten "
              "dl-Dateien - es ist nichts belegt; mit --base <ref> pruefen)")
        return 2

    bad, ok = [], 0
    for rel in files:
        old = git("show", f"{ref}:{rel}")
        with open(rel, "rb") as fh:
            new = fh.read()
        clean = norm(strip_tag(new)) == norm(old)
        tagged = TAG.encode() in new
        if clean and tagged:
            ok += 1
        else:
            bad.append((rel, clean, tagged))
        print(f"{'OK  ' if clean and tagged else 'DIFF'}  "
              f"delta={len(new) - len(old):+3d}B  tag={tagged}  {rel}")

    print(f"\nnur-Tag-ergaenzt: {ok}/{len(files)}")
    if bad:
        print("ABWEICHER:")
        for rel, clean, tagged in bad:
            # Beide Befunde nennen, nicht den ersten - sonst verdeckt
            # "Inhalt veraendert" still, dass auch der Tag fehlt.
            why = ", ".join(w for w, hit in (
                ("Inhalt veraendert", not clean),
                ("noindex-Tag fehlt", not tagged)) if hit)
            print(f"  - {rel}: {why}")
        print("\nERGEBNIS: PATCH_INTEGRITAET_DEFEKT")
        return 1
    print("\nERGEBNIS: PATCH_INTEGRITAET_OK "
          "(Inhalt unveraendert, nur meta robots ergaenzt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
