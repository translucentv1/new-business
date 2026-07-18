"""Autonomous sell-loop: payment-gate -> publish -> poll sales.

cron entrypoint (replaces manually re-running publish_all.py). If Gumroad's
payment method isn't connected yet, prints the WAIT state and exits 0 --
nothing to retry locally, the seller action is still pending. Once connected:
enables existing drafts + creates/publishes the 3 missing bundles (10/day
limit respected by gumroad_uploader.publish), then polls for sales.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import check_payment_connected as cpc
import publish_all as pa
import sale_poller as sp


def main():
    ok, detail = cpc.check()
    if not ok:
        print(f"WAIT: {detail}")
        return
    print(f"READY: {detail}")
    pa.main()
    n, det = sp.poll()
    print(f"sales poll: {det}")


if __name__ == "__main__":
    main()
