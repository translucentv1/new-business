"""Einmal-Sonde Ticket 20: beweist, dass der Patch NUR den Tag ergaenzt hat.

Vergleicht jede gepatchte Datei mit ihrem HEAD-Blob, nachdem der eingefuegte
Tag wieder entfernt wurde. Zeilenenden werden fuer den Vergleich normalisiert,
weil git/Windows sie ohnehin uebersetzt - Inhalt ist die Frage, nicht CRLF.
Ad-hoc-Sonde (Einmalmessung) -> braucht keinen --selftest.
"""

import subprocess
import sys

TAG = '<meta name="robots" content="noindex,nofollow">'


def norm(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def main() -> int:
    out = subprocess.run(
        ["git", "diff", "--name-only", "--", "dl"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    bad, ok = [], 0
    for rel in out:
        old = subprocess.run(
            ["git", "show", f"HEAD:{rel}"], capture_output=True, check=True
        ).stdout
        new = open(rel, "rb").read()
        stripped = new
        for cand in (b"\r\n  " + TAG.encode(), b"\n  " + TAG.encode(),
                     TAG.encode()):
            if cand in new:
                stripped = new.replace(cand, b"", 1)
                break
        same = norm(stripped) == norm(old)
        tag_present = TAG.encode() in new
        if same and tag_present:
            ok += 1
        else:
            bad.append(rel)
        print(f"{'OK  ' if same and tag_present else 'DIFF'}  "
              f"delta={len(new) - len(old):+3d}B  tag={tag_present}  {rel}")
    print(f"\nnur-Tag-ergaenzt: {ok}/{len(out)}")
    if bad:
        print("ABWEICHER:")
        for rel in bad:
            print("  -", rel)
        print("\nERGEBNIS: PATCH_INTEGRITAET_DEFEKT")
        return 1
    print("\nERGEBNIS: PATCH_INTEGRITAET_OK "
          "(Inhalt unveraendert, nur meta robots ergaenzt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
