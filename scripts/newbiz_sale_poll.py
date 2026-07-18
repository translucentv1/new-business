"""Stripe sale-poller wrapper for cron (no agent).

Polls Stripe charges; reports the first price>0 sale (or remains silent).
Charta: a sale needs a real external buyer -> this only REPORTS, never fakes.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stripe_uploader as su

if __name__ == "__main__":
    key = su.get_key()
    if not key:
        print("NO_KEY: waiting for STRIPE_SECRET_KEY.")
        sys.exit(0)
    n, det = su.poll_sales()
    if n > 0:
        print(f"SALE! {det} -> see sales.log")
    else:
        print(f"no new sale | {det}")
