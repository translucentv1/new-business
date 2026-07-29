"""Gumroad sale poller (autonomous, no_agent cron).

Reports total Gumroad sales_count every tick. Only alerts (non-silent) when a
NEW sale is detected vs. the last known count stored in gumroad_last_sale.txt.
"""
import os
import json
import subprocess

REPO = r"C:\Users\phili\new-business"
SECRETS = os.path.join(REPO, ".gumroad_secrets")
STATE = os.path.join(REPO, "gumroad_last_sale.txt")


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
    raw = subprocess.run(
        ["curl", "-s", f"https://api.gumroad.com/v2/products?access_token={GUM}"],
        capture_output=True, text=True, timeout=40).stdout
    try:
        prods = json.loads(raw).get("products", [])
    except Exception:
        print("PARSE ERR", raw[:120])
        return
    total = sum(p.get("sales_count", 0) for p in prods)
    published = sum(1 for p in prods if p.get("published"))

    prev = 0
    if os.path.exists(STATE):
        try:
            prev = int(open(STATE).read().strip() or 0)
        except Exception:
            prev = 0
    open(STATE, "w").write(str(total))

    if total > prev:
        print(f"*** NEUER VERKAUF! Gumroad Sales: {total} (vorher {prev}) | published {published}/{len(prods)} ***")
    else:
        print(f"Gumroad Sales: {total} | published {published}/{len(prods)} | kein neuer Verkauf")


if __name__ == "__main__":
    main()
