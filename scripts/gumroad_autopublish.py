"""Gumroad auto-publish watcher (autonomous, no_agent cron).

Tries to publish all products every tick. Gumroad blocks publishing until the
payout method is fully activated server-side, so this just retries until it
works. Reports the live published count. Safe: pure API calls, no gateway cmds.
"""
import os
import json
import subprocess

REPO = r"C:\Users\phili\new-business"
SECRETS = os.path.join(REPO, ".gumroad_secrets")


def token():
    out = subprocess.run(
        ["grep", "-oE", "GUMROAD_API_KEY=.*", SECRETS],
        capture_output=True, text=True, timeout=30).stdout.strip()
    return out.split("=", 1)[1].strip() if out else None


def main():
    GUM = token()
    if not GUM:
        print("NO TOKEN")
        return
    # fetch
    raw = subprocess.run(
        ["curl", "-s", f"https://api.gumroad.com/v2/products?access_token={GUM}"],
        capture_output=True, text=True, timeout=40).stdout
    try:
        prods = json.loads(raw).get("products", [])
    except Exception:
        print("PARSE ERR", raw[:120])
        return
    published = 0
    for p in prods:
        if p.get("published"):
            published += 1
            continue
        r = subprocess.run(
            ["curl", "-s", "-X", "PUT",
             f"https://api.gumroad.com/v2/products/{p['id']}?access_token={GUM}",
             "-F", "published=true"],
            capture_output=True, text=True, timeout=40).stdout
        try:
            if json.loads(r).get("product", {}).get("published"):
                published += 1
        except Exception:
            pass
    total = len(prods)
    if published == total:
        print(f"ALL PUBLISHED {published}/{total} — Gumroad freigegeben, Verkauf live möglich")
    else:
        print(f"PUBLISHED {published}/{total} — Gumroad blockt weiter (Payout noch nicht aktiv)")


if __name__ == "__main__":
    main()
