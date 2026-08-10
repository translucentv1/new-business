"""Ad-hoc-Sonde (Ticket 29), Teil 2: Kollateralschaden-Claim des Fremdlaufs pruefen.

Claim aus Commit 6dd6238: "468 entfernte URLs alle /t/", "1232 -> 764".
Hier wird die Mengendifferenz zwischen Vor- und Nachstand WIRKLICH gebildet.
"""
import re
import subprocess
import sys

REV_VORHER = "6dd6238^:sitemap.xml"
REV_NACHHER = "HEAD:sitemap.xml"


def loc_from_git(rev):
    out = subprocess.run(["git", "show", rev], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        print("git show fehlgeschlagen:", rev, out.stderr[:200])
        sys.exit(2)
    return set(re.findall(r"<loc>([^<]+)</loc>", out.stdout))


vorher = loc_from_git(REV_VORHER)
nachher = loc_from_git(REV_NACHHER)
entfernt = vorher - nachher
neu = nachher - vorher

print(f"vorher={len(vorher)} nachher={len(nachher)} entfernt={len(entfernt)} neu={len(neu)}")

nicht_t = sorted(u for u in entfernt if "/t/" not in u)
print("entfernt OHNE /t/ =", len(nicht_t))
for u in nicht_t[:20]:
    print("   KOLLATERAL:", u)

if nicht_t:
    print("ERGEBNIS: KOLLATERAL_GEFUNDEN")
    sys.exit(1)
print("ERGEBNIS: KOLLATERAL_KEINER (Claim des Fremdlaufs bestaetigt)")
sys.exit(0)
