"""Payment-gate probe: exit 0 if Gumroad publish is currently possible, else 1.

Used by cron/autonomous_sell_loop.py to decide whether to run publish_all.
Tries to enable one existing draft; a payment-method error means NOT YET.
No drafts left to probe (all already published or store empty) counts as
READY since there is nothing left for the gate to block.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gumroad_uploader as gu
import publish_all as pa


def check() -> tuple[bool, str]:
    key = gu.get_key()
    if not key:
        return False, "NO_KEY"
    try:
        prods = pa.list_products(key)
    except Exception as e:
        return False, f"REQ_ERR {type(e).__name__}: {e}"
    drafts = [p for p in prods if not p.get("published")]
    if not drafts:
        return True, "NO_DRAFTS (nothing to gate on, treat as connected)"
    pid = drafts[0]["id"]
    ok, detail = pa.enable(pid, key)
    if ok:
        return True, f"PAYMENT_CONNECTED probe={pid[:8]}"
    if pa.is_payment_error(detail):
        return False, f"WAIT_FOR_PAYMENT: {detail[:160]}"
    return False, f"PROBE_FAIL: {detail[:160]}"


if __name__ == "__main__":
    ok, detail = check()
    print(f"[{'READY' if ok else 'WAIT'}] {detail}")
    sys.exit(0 if ok else 1)
