"""Ad-hoc-Sonde (Ticket 29): Deindex-Eingriff eines Fremdlaufs gegen den Geldpfad pruefen.
Keine Produktivfunktion, kein stehendes Tor -> kein --selftest noetig.
"""
import re
import sys


def loc(path):
    with open(path, encoding="utf-8") as fh:
        return set(re.findall(r"<loc>([^<]+)</loc>", fh.read()))


local = loc("sitemap.xml")
live = loc("evidence/_live_sitemap.xml")
print("sitemap lokal =", len(local), " live =", len(live))
print("nur_lokal =", len(local - live), " nur_live =", len(live - local))
for u in sorted(local ^ live)[:10]:
    print("   DRIFT:", u)
print("t/-URLs lokal =", sum(1 for u in local if "/t/" in u),
      " live =", sum(1 for u in live if "/t/" in u))

geld = ["rtd.html", "gig.html", "index.html", "agb.html", "datenschutz.html",
        "impressum.html", "lead_magnet.html", "ki-text-service.html", "thanks.html"]
fehlend = []
for g in geld:
    drin = any(u.endswith("/" + g) for u in live)
    print(f"  SITEMAP {g:<24} {'ja' if drin else 'NEIN'}")
    if not drin:
        fehlend.append(g)
print("GELDSEITEN_NICHT_IN_SITEMAP =", fehlend)
sys.exit(0)
