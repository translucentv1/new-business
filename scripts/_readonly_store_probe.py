"""READ-ONLY STORE probe — replicates only the final verify GET of
upload_missing_drafts.py. Produces identical STORE line, makes NO writes.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gumroad_uploader as gu
import httpx

key = gu.get_key()
assert key, "NO_KEY — abort"
with httpx.Client(timeout=60) as c:
    r = c.get(f"{gu.API}/v2/products", params={"access_token": key})
    r.raise_for_status()
    prods = r.json().get("products", [])
print(f"STORE: total={len(prods)} drafts={sum(1 for p in prods if not p.get('published', True))} published={sum(1 for p in prods if p.get('published'))}")
