#!/usr/bin/env python3
"""Tick-Verifikation: Gig-Preise, Stripe-Live-Links, Kernseiten. Nur MEASURED-Ausgaben."""
import re
import subprocess

ROOT = "https://translucentv1.github.io/new-business"


def http(url):
    try:
        out = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-m", "25", "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=40)
        return out.stdout.strip()
    except Exception as exc:  # pragma: no cover
        return f"ERR:{exc}"


gig = open("gig.html", encoding="utf-8").read()
doc = open("docs/fiverr_gig.md", encoding="utf-8").read()

print("=== Preise in gig.html ===")
for p in ("3,99", "7,99", "14,99"):
    print(f"  {p} EUR: {gig.count(p)}x")

print("=== Preise in docs/fiverr_gig.md ===")
for p in ("3,99", "7,99", "14,99"):
    print(f"  {p} EUR: {doc.count(p)}x")

print("=== Pflichtabschnitte docs/fiverr_gig.md ===")
for s in ("## Gig-Titel", "## Gig-Beschreibung", "## Pakete", "## FAQ",
          "## Anforderungen an den Käufer"):
    print(f"  {'OK ' if s in doc else 'FEHLT'} {s}")

links = sorted(set(re.findall(r"https://buy\.stripe\.com/[A-Za-z0-9]+", gig)))
print(f"=== Stripe-Live-Checkout-Links ({len(links)}) ===")
fails = 0
for u in links:
    c = http(u)
    if c != "200":
        fails += 1
    print(f"  {c}  {u}")
print(f"STRIPE_LINKS_OK={len(links) - fails} STRIPE_LINKS_FAIL={fails}")

core = ["index.html", "gig.html", "rtd.html", "thanks.html", "sitemap.xml",
        "lead_magnet.html", "impressum.html", "agb.html", "datenschutz.html",
        "ki-text-service/index.html"]
print(f"=== Kernseiten live ({len(core)}) ===")
cf = 0
for u in core:
    c = http(f"{ROOT}/{u}")
    if c != "200":
        cf += 1
    print(f"  {c}  {u}")
print(f"CORE_OK={len(core) - cf} CORE_FAIL={cf}")
