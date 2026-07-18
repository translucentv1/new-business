"""Push all 8 product bundles as GUMROAD DRAFTS (do_publish=False).
Autonomous execution per user grant 2026-07-18 (all hard stops lifted).
Reports per-id result + verifies final store state via API.
"""
import sys, os, glob, time, httpx
sys.path.insert(0, os.path.dirname(__file__))
import gumroad_uploader as gu

CORPUS = gu.CORPUS
API = gu.API
key = gu.get_key()
assert key, "NO_KEY — abort"

ids = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*")) if os.path.isdir(p))
ids = [i for i in ids if os.path.exists(os.path.join(CORPUS, i, "product", "meta.json"))]
print(f"FOUND {len(ids)} product bundles: {ids}")

results = []
for bid in ids:
    ok, det = gu.publish(bid, do_publish=False)
    results.append((bid, ok, det))
    print(f"{'OK ' if ok else 'BLOCK'} {bid}: {det}")
    time.sleep(1)  # gentle rate-limit spacing

ok_n = sum(1 for _, ok, _ in results if ok)
print(f"\n=== LOCAL SUMMARY: {ok_n}/{len(ids)} drafts created ===")

# Verify against live store
with httpx.Client(timeout=60) as c:
    r = c.get(f"{API}/v2/products", params={"access_token": key})
    j = r.json()
    prods = j.get("products", [])
    drafts = [p for p in prods if not p.get("published", True)]
    pubd = [p for p in prods if p.get("published")]
    print(f"STORE: total={len(prods)} drafts={len(drafts)} published={len(pubd)}")
    print("STORE NAMES:", [p.get("name") for p in prods])
