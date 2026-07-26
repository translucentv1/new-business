"""
Request-to-Delivery Skeleton (ADR-0035).

Stdlib-only HTTP server (no Flask dependency, matches repo convention).
Flow:
  1. GET  /              -> request form (customer describes what they need)
  2. POST /request       -> validate, create Stripe Payment Link via REST API,
                            store order, return checkout URL
  3. GET  /status/<id>   -> order status (pending / paid / fulfilled)
  4. POST /webhook       -> Stripe webhook: verify signature (Stripe scheme
                            t=..,v1=.. over "{t}.{body}"), mark order paid,
                            run generator, save deliverable, set fulfilled.

Stripe secret is read from .stripe_secrets (STRIPE_SECRET_KEY=...). If empty,
the app runs in DEMO mode: it returns a fake checkout URL and logs the order,
so the flow is testable without credentials. NEVER hardcode or invent keys.
DEMO orders carry "demo": true in orders.json (label travels with the data).

Legal: this is a paid service. Operator must add Impressum + AGB + (if regular
income) Gewerbeanmeldung before public launch. See ADR-0035.
"""
import os
import re
import sys
import json
import time
import uuid
import hmac
import hashlib
import urllib.parse
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ORDERS = os.path.join(HERE, "orders.json")
DELIVERABLES = os.path.join(HERE, "deliverables")
SECRETS = os.path.join(ROOT, ".stripe_secrets")
PRICE_DEFAULT = 399  # cents (3,99 EUR) -- adjustable per request later

# ---- secrets ----------------------------------------------------------------
_PLACEHOLDER_WORDS = ("FUELL", "FÜLL", "EINF", "VERF", "HIER", "XXXX",
                      "CHANGE", "REDACT", "PLATZHALTER", "TODO", "DEIN")

def _is_real_key(v):
    # reject obvious placeholders
    if not v:
        return False
    v = v.lstrip("\ufeff")  # strip UTF-8 BOM
    if v in ("***", "REDACTED", "CHANGEME", ""):
        return False
    if v.startswith("'") or v.startswith('"'):
        return False
    # Real Stripe keys/secrets are pure ASCII [A-Za-z0-9_]. Anything with
    # umlauts, spaces or placeholder words (sk_live_HIER_EINFUELLEN...) is
    # a template value -> treat as absent so DEMO mode engages cleanly.
    if not re.fullmatch(r"[A-Za-z0-9_]+", v):
        return False
    vu = v.upper()
    if any(w in vu for w in _PLACEHOLDER_WORDS):
        return False
    return True

def _secret_from_file(name):
    if os.path.exists(SECRETS):
        for line in open(SECRETS, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if s.startswith(name) and "=" in s:
                v = s.split("=", 1)[1].strip().strip('"').strip("'")
                if _is_real_key(v):
                    return v
    return None

def get_stripe_key():
    env = os.environ.get("STRIPE_SECRET_KEY")
    if _is_real_key(env):
        return env
    return _secret_from_file("STRIPE_SECRET_KEY")

def get_webhook_secret():
    env = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if _is_real_key(env):
        return env
    return _secret_from_file("STRIPE_WEBHOOK_SECRET")

# ---- order store ------------------------------------------------------------
def load_orders():
    if os.path.exists(ORDERS):
        try:
            return json.load(open(ORDERS, encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_orders(d):
    json.dump(d, open(ORDERS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def add_order(oid, req_text, price_cents, checkout_url, demo=False, payment_link_id=None):
    d = load_orders()
    d[oid] = {
        "id": oid,
        "request": req_text,
        "price_cents": price_cents,
        "checkout_url": checkout_url,
        "payment_link_id": payment_link_id,
        "status": "pending",
        "demo": demo,
        "created": datetime.now().isoformat(),
        "paid_at": None,
        "deliverable": None,
    }
    save_orders(d)
    return oid

# ---- stripe payment link (REST, no SDK) ------------------------------------
def create_payment_link(req_text, price_cents):
    key = get_stripe_key()
    # Only a real LIVE key may hit the API. Test keys (sk_test_*), placeholders
    # (***), or empty -> DEMO mode. We never use keys we cannot verify belong
    # to the operator (Hard Stop: no foreign credentials).
    oid = uuid.uuid4().hex[:12]
    if not key or not key.startswith("sk_live_"):
        demo_url = f"https://buy.stripe.com/demo/{oid}"  # [DEMO] not a real link
        add_order(oid, req_text, price_cents, demo_url, demo=True)
        return demo_url, True

    # Real path: create Product -> Price -> Payment Link via Stripe REST API.
    # order_id goes into the Payment Link metadata; Stripe copies Payment-Link
    # metadata onto the Checkout Session, so checkout.session.completed events
    # carry it back to us (plus payment_link id as fallback match).
    headers = {"Authorization": f"Bearer {key}",
               "Content-Type": "application/x-www-form-urlencoded"}

    prod_body = urllib.parse.urlencode({
        "name": f"Custom deliverable: {req_text[:40]}",
        "metadata[request]": req_text[:500],
    }).encode()
    try:
        req = urllib.request.Request("https://api.stripe.com/v1/products",
                                     data=prod_body, headers=headers, method="POST")
        prod = json.load(urllib.request.urlopen(req, timeout=20))
    except urllib.error.HTTPError as e:
        return f"STRIPE_ERR_PRODUCT:{e.read().decode()[:200]}", False

    price_body = urllib.parse.urlencode({
        "product": prod["id"],
        "unit_amount": price_cents,
        "currency": "eur",
    }).encode()
    req = urllib.request.Request("https://api.stripe.com/v1/prices",
                                 data=price_body, headers=headers, method="POST")
    price = json.load(urllib.request.urlopen(req, timeout=20))

    link_body = urllib.parse.urlencode({
        "line_items[0][price]": price["id"],
        "line_items[0][quantity]": "1",
        "metadata[order_id]": oid,
        "after_completion[type]": "redirect",
        "after_completion[redirect][url]": "https://translucentv1.github.io/thanks.html",
    }).encode()
    req = urllib.request.Request("https://api.stripe.com/v1/payment_links",
                                 data=link_body, headers=headers, method="POST")
    link = json.load(urllib.request.urlopen(req, timeout=20))
    add_order(oid, req_text, price_cents, link["url"], demo=False,
              payment_link_id=link.get("id"))
    return link["url"], False

# ---- webhook signature (Stripe scheme) --------------------------------------
def verify_stripe_signature(body: bytes, sig_header: str, secret: str,
                            tolerance: int = 300) -> bool:
    """Stripe-Signature: t=<ts>,v1=<hexsig>[,v1=...].
    Signed payload is b"{t}." + body, HMAC-SHA256 with the endpoint secret."""
    if not sig_header:
        return False
    t = None
    sigs = []
    for part in sig_header.split(","):
        k, _, v = part.strip().partition("=")
        if k == "t":
            t = v
        elif k == "v1":
            sigs.append(v)
    if not t or not sigs:
        return False
    try:
        ts = int(t)
    except ValueError:
        return False
    if tolerance and abs(time.time() - ts) > tolerance:
        return False
    expected = hmac.new(secret.encode(), f"{t}.".encode() + body,
                        hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)

# ---- fulfillment -------------------------------------------------------------
def fulfill(oid: str) -> dict:
    """Mark order paid, generate deliverable, save it, set fulfilled."""
    d = load_orders()
    order = d.get(oid)
    if not order:
        return {}
    order["status"] = "paid"
    order["paid_at"] = datetime.now().isoformat()
    try:
        sys.path.insert(0, HERE)
        from generator import generate
        content = generate(order["request"])
        os.makedirs(DELIVERABLES, exist_ok=True)
        path = os.path.join(DELIVERABLES, f"{oid}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        order["deliverable"] = path
        order["status"] = "fulfilled"
    except Exception as e:
        order["deliverable"] = f"GENERATION_ERR: {e}"  # stays "paid" for retry
    save_orders(d)
    return order

def find_order_for_event(obj: dict) -> str | None:
    """Match a checkout.session object to an order: metadata.order_id first,
    then payment_link id fallback."""
    oid = (obj.get("metadata") or {}).get("order_id")
    d = load_orders()
    if oid and oid in d:
        return oid
    plink = obj.get("payment_link")
    if plink:
        for k, v in d.items():
            if v.get("payment_link_id") == plink:
                return k
    return None

# ---- HTTP handler -----------------------------------------------------------
FORM = """<!doctype html><html lang=de><head><meta charset=utf-8>
<title>Wunsch erfüllen</title></head><body style="font-family:sans-serif;max-width:600px;margin:40px auto">
<h1>Was brauchst du?</h1>
<p>Beschreibe, was wir dir liefern sollen (Text, Template, Code-Snippet, Study-Guide, Design-Idee).</p>
<form method=post action=/request>
<textarea name=req rows=6 style="width:100%" placeholder="z.B. Ein 3-Seiten Study-Guide zu Kapitel 5 von Frankenstein"></textarea><br>
<label>Preis (EUR): <input name=price value="3.99" size=6></label><br><br>
<button type=submit>Anfrage senden</button>
</form></body></html>"""

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, fmt, *args):  # quiet in tests
        if os.environ.get("RTD_QUIET") != "1":
            super().log_message(fmt, *args)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self._send(200, FORM)
        elif self.path.startswith("/status/"):
            oid = self.path.split("/")[-1]
            d = load_orders()
            if oid in d:
                self._send(200, json.dumps(d[oid], ensure_ascii=False, indent=2), "application/json")
            else:
                self._send(404, "order not found")
        else:
            self._send(404, "not found")

    def do_POST(self):
        if self.path == "/request":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            data = urllib.parse.parse_qs(raw)
            req = (data.get("req", [""])[0]).strip()
            if not req:
                self._send(400, "leer")
                return
            try:
                price = int(float(data.get("price", ["3.99"])[0]) * 100)
            except Exception:
                price = PRICE_DEFAULT
            url, demo = create_payment_link(req, price)
            if demo:
                msg = f"DEMO-MODUS (kein Stripe-Key). Checkout: {url}<br>Tragen Sie den echten STRIPE_SECRET_KEY in .stripe_secrets ein, dann wird ein echter Link erzeugt."
            else:
                msg = f"Bezahlen Sie hier: <a href='{url}'>{url}</a>"
            self._send(200, f"<p>{msg}</p><p><a href='/'>zurueck</a></p>")
        elif self.path == "/webhook":
            self._handle_webhook()
        else:
            self._send(404, "not found")

    def _handle_webhook(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        secret = get_webhook_secret()
        if secret:
            sig = self.headers.get("Stripe-Signature", "")
            if not verify_stripe_signature(body, sig, secret):
                self._send(400, "bad signature")
                return
        # No secret configured -> accept unverified (pre-launch/local only).
        # Before public launch STRIPE_WEBHOOK_SECRET MUST be set.
        try:
            event = json.loads(body.decode("utf-8"))
        except Exception:
            self._send(400, "bad json")
            return
        # Only checkout.session.completed means "customer paid".
        # (payment_link.created fires on link creation, NOT on payment.)
        if event.get("type") == "checkout.session.completed":
            obj = event.get("data", {}).get("object", {})
            oid = find_order_for_event(obj)
            if oid:
                fulfill(oid)
        self._send(200, "ok")

def main():
    port = int(os.environ.get("PORT", "8080"))
    srv = HTTPServer(("127.0.0.1", port), H)
    print(f"request_delivery listening on http://127.0.0.1:{port}")
    srv.serve_forever()

if __name__ == "__main__":
    main()
