"""
End-to-end local test for the Request-to-Delivery webhook (ADR-0035).

Runs the stdlib server on a test port with a TEST webhook secret
(whsec_test_local — synthetic, only for signing our own test events;
no Stripe API is contacted). Checks:

  1. POST /request (DEMO mode, no live key)      -> order pending, demo=True
  2. POST /webhook, WRONG signature              -> 400, order unchanged
  3. POST /webhook, payment_link.created event   -> order stays pending
  4. POST /webhook, checkout.session.completed
     with correct Stripe-style signature         -> order fulfilled,
                                                    deliverable file exists

Exit code 0 = all assertions passed.
"""
import hashlib
import hmac
import json
import os
import sys
import threading
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TEST_SECRET = "whsec_test_local"  # synthetic, test-only
PORT = 8971
BASE = f"http://127.0.0.1:{PORT}"

os.environ["STRIPE_WEBHOOK_SECRET"] = TEST_SECRET
os.environ["PORT"] = str(PORT)
os.environ["RTD_QUIET"] = "1"
os.environ.pop("STRIPE_SECRET_KEY", None)  # force DEMO mode

# use a scratch orders file so we don't pollute the real store
import app  # noqa: E402
app.ORDERS = os.path.join(HERE, "orders_test.json")
# CRITICAL test isolation: get_stripe_key() falls back to the .stripe_secrets
# FILE when the env var is missing. Without this override a valid live key on
# disk makes the test create REAL Stripe payment links (happened 2026-07-28,
# plink_1TxyIqFajs0YddhP...). Point SECRETS at a nonexistent path so the test
# can never reach the live API.
app.SECRETS = os.path.join(HERE, ".stripe_secrets_DOES_NOT_EXIST_test_only")
assert app.get_stripe_key() is None, (
    "test isolation broken: a live Stripe key is still reachable")
if os.path.exists(app.ORDERS):
    os.remove(app.ORDERS)

from http.server import HTTPServer  # noqa: E402
srv = HTTPServer(("127.0.0.1", PORT), app.H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.3)


def post(path, data: bytes, headers=None):
    req = urllib.request.Request(BASE + path, data=data,
                                 headers=headers or {}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def sign(body: bytes, secret: str, ts: int | None = None) -> str:
    ts = ts or int(time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + body,
                   hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


failures = []

def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not cond:
        failures.append(name)


# 1) create demo order
code, body = post("/request", b"req=Test+Study-Guide+Frankenstein+K5&price=3.99")
check("POST /request returns 200", code == 200, f"(HTTP {code})")
check("response flags DEMO mode", "DEMO-MODUS" in body)

orders = app.load_orders()
check("exactly 1 order stored", len(orders) == 1)
oid = next(iter(orders))
o = orders[oid]
check("order pending + demo flag", o["status"] == "pending" and o["demo"] is True,
      f"(status={o['status']}, demo={o['demo']})")

event = json.dumps({
    "type": "checkout.session.completed",
    "data": {"object": {"metadata": {"order_id": oid}}},
}).encode()

# 2) wrong signature -> 400
code, body = post("/webhook", event,
                  {"Stripe-Signature": f"t={int(time.time())},v1=" + "0" * 64})
check("bad signature rejected with 400", code == 400, f"(HTTP {code}: {body})")
check("order still pending after bad sig",
      app.load_orders()[oid]["status"] == "pending")

# 3) payment_link.created must NOT fulfill
plc = json.dumps({"type": "payment_link.created",
                  "data": {"object": {"metadata": {"order_id": oid}}}}).encode()
code, _ = post("/webhook", plc, {"Stripe-Signature": sign(plc, TEST_SECRET)})
check("payment_link.created accepted but ignored",
      code == 200 and app.load_orders()[oid]["status"] == "pending")

# 4) correctly signed checkout.session.completed -> fulfilled
code, body = post("/webhook", event, {"Stripe-Signature": sign(event, TEST_SECRET)})
o = app.load_orders()[oid]
check("valid webhook returns 200", code == 200, f"(HTTP {code})")
check("order fulfilled", o["status"] == "fulfilled", f"(status={o['status']})")
dpath = o.get("deliverable") or ""
check("deliverable file exists", os.path.isfile(dpath), f"({dpath})")
if os.path.isfile(dpath):
    content = open(dpath, encoding="utf-8").read()
    check("deliverable non-empty", len(content) > 50, f"({len(content)} chars)")

srv.shutdown()
print()
print("RESULT:", "ALL PASS" if not failures else f"FAILED: {failures}")
sys.exit(0 if not failures else 1)
