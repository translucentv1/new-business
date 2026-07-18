"""Idempotent: legt nur fehlende Drafts an, stoppt sauber bei Tageslimit.
Cron-getrieben (no_agent), kein Consent-Gate. Respektiert Gumroad 10/Tag-Limit.
"""
import sys, os, glob, time, httpx
sys.path.insert(0, os.path.dirname(__file__))
import gumroad_uploader as gu

API = gu.API
key = gu.get_key()
assert key, "NO_KEY — abort"

# Welche Bundles haben ein product-Bundle?
ids = sorted(os.path.basename(p) for p in glob.glob(os.path.join(gu.CORPUS, "*")) if os.path.isdir(p))
ids = [i for i in ids if os.path.exists(os.path.join(gu.CORPUS, i, "product", "meta.json"))]

# Live: welche Drafts existieren schon (name -> kurzer Titel-Check via meta)?
with httpx.Client(timeout=60) as c:
    r = c.get(f"{API}/v2/products", params={"access_token": key})
    existing = {p.get("name") for p in r.json().get("products", [])}

# Map bundle-id -> title
import json
def title_of(bid):
    with open(os.path.join(gu.CORPUS, bid, "product", "meta.json"), encoding="utf-8") as fh:
        return json.load(fh)["title"]

missing = []
for bid in ids:
    t = title_of(bid)
    if t not in existing:
        missing.append((bid, t))

if not missing:
    print("ALL DRAFTS PRESENT — nothing to do.")
    sys.exit(0)

print(f"MISSING drafts ({len(missing)}): {[m[1] for m in missing]}")
created = 0
for bid, t in missing:
    ok, det = gu.publish(bid, do_publish=False)
    if ok:
        created += 1
        print(f"OK   {bid} ({t}): {det}")
    else:
        print(f"BLOCK {bid} ({t}): {det}")
        if "10 products per day" in det:
            print("DAILY LIMIT HIT — stop, retry next cron tick.")
            break
    time.sleep(1)

# Final store verify
with httpx.Client(timeout=60) as c:
    r = c.get(f"{API}/v2/products", params={"access_token": key})
    prods = r.json().get("products", [])
    print(f"STORE: total={len(prods)} drafts={sum(1 for p in prods if not p.get('published',True))} published={sum(1 for p in prods if p.get('published'))}")
