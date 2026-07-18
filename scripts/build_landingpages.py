"""Build landingpages for all 8 bundles.
5 DRAFTS already live on Gumroad -> real short_urls wired in.
3 not-yet-uploaded (daily-limit) -> placeholder link, replaced on retry.
"""
import sys, os
sys.path.insert(0, r"C:\Users\phili\new-business\scripts")
import landingpage_gen as lg

REAL = {
    "11":    "https://philippbehnisch.gumroad.com/l/pfsltw",
    "1342":  "https://philippbehnisch.gumroad.com/l/lfojyt",
    "158":   "https://philippbehnisch.gumroad.com/l/wptwly",
    "174":   "https://philippbehnisch.gumroad.com/l/vldguh",
    "25913": "https://philippbehnisch.gumroad.com/l/eqnwxe",
}
n = lg.build(gumroad_urls=REAL)
print(f"Generated {n} product pages + index at {lg.SITE}")
print("Real URLs wired for:", list(REAL.keys()), "| placeholders for the rest (retry pending)")
