"""
Request-to-Delivery Skeleton (ADR-0035).

Stdlib-only HTTP server (no Flask dependency, matches repo convention).
Flow:
  1. GET  /              -> request form (customer describes what they need)
  2. POST /request       -> validate, create Stripe Payment Link via REST API,
                            store order, return checkout URL
  3. GET  /status/<id>   -> order status (pending / paid / fulfilled)
  4. POST /webhook       -> Stripe webhook: mark order paid, trigger generation+delivery

Stripe secret is read from .stripe_secrets (STRIPE_SECRET_KEY=...). If empty,
the app runs in DEMO mode: it returns a fake checkout URL and logs the order,
so the flow is testable without credentials. NEVER hardcode or invent keys.

Legal: this is a paid service. Operator must add Impressum + AGB + (if regular
income) Gewerbeanmeldung before public launch. See ADR-0035.
"""
import os
import json
import time
import uuid
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ORDERS = os.path.join(HERE, "orders.json")
SECRETS = os.path.join(ROOT, ".stripe_secrets")
PRICE_DEFAULT = 399  # cents (3,99 EUR) -- adjustable per request later

# ---- secrets ----------------------------------------------------------------
def _is_real_key(v):
    # reject obvious placeholders
    if not v:
        return False
    v = v.lstrip("\ufeff")  # strip UTF-8 BOM
    if v in ("***", "REDACTED", "CHANGEME", ""):
        return False
    if v.startswith("'") or v.startswith('"'):
        return False
    return True

def get_stripe_key():
    env = os.environ.get("STRIPE_SECRET_KEY")
    if _is_real_key(env):
        return env
    if os.path.exists(SECRETS):
        for line in open(SECRETS, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if s.startswith("STRIPE_SECRET_KEY") and "=" in s:
                v = s.split("=", 1)[1].strip().strip('"').strip("'")
                if _is_real_key(v):
                    return v
    return None

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

def add_order(req_text, price_cents, checkout_url, demo=False):
    d = load_orders()
    oid = uuid.uuid4().hex[:12]
    d[oid] = {
        "id": oid,
        "request": req_text,
        "price_cents": price_cents,
        "checkout_url": checkout_url,
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
    if not key or not key.startswith("sk_live_"):
        oid = uuid.uuid4().hex[:12]
        demo_url = f"https://buy.stripe.com/demo/{oid}"
        add_order(req_text, price_cents, demo_url, demo=True)
        return demo_url, True

    # Real path: create a Price then a Payment Link via Stripe REST API.
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/x-www-form-urlencoded"}

    # 1) create product
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

    # 2) create price
    price_body = urllib.parse.urlencode({
        "product": prod["id"],
        "unit_amount": price_cents,
        "currency": "eur",
    }).encode()
    req = urllib.request.Request("https://api.stripe.com/v1/prices",
                                 data=price_body, headers=headers, method="POST")
    price = json.load(urllib.request.urlopen(req, timeout=20))

    # 3) create payment link
    link_body = urllib.parse.urlencode({
        "line_items[0][price]": price["id"],
        "line_items[0][quantity]": "1",
        "after_completion[type]": "redirect",
        "after_completion[redirect][url]": "https://translucentv1.github.io/thanks.html",
    }).encode()
    req = urllib.request.Request("https://api.stripe.com/v1/payment_links",
                                 data=link_body, headers=headers, method="POST")
    link = json.load(urllib.request.urlopen(req, timeout=20))
    oid = add_order(req_text, price_cents, link["url"], demo=False)
    return link["url"], False

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
        import hmac as _hmac
        import hashlib as _hash
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        sig = self.headers.get("Stripe-Signature", "")
        secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        if not secret and os.path.exists(os.path.join(ROOT, ".stripe_secrets")):
            for line in open(os.path.join(ROOT, ".stripe_secrets"), encoding="utf-8", errors="ignore"):
                if line.strip().startswith("STRIPE_WEBHOOK_SECRET") and "=" in line:
                    secret = line.split("=", 1)[1].strip().strip('"').strip("'")
        if secret:
            exp = _hmac.new(secret.encode(), body, _hash.sha256).hexdigest()
            if not _hmac.compare_digest(exp, sig or ""):
                self._send(400, "bad signature")
                return
        try:
            event = json.loads(body.decode("utf-8"))
        except Exception:
            self._send(400, "bad json")
            return
        if event.get("type") in ("payment_link.created", "checkout.session.completed"):
            obj = event.get("data", {}).get("object", {})
            oid = obj.get("metadata", {}).get("order_id")
            if oid:
                d = load_orders()
                if oid in d:
                    d[oid]["status"] = "paid"
                    d[oid]["paid_at"] = datetime.now().isoformat()
                    try:
                        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                        from generator import generate
                        d[oid]["deliverable"] = generate(d[oid]["request"])
                    except Exception as e:
                        d[oid]["deliverable"] = f"GENERATION_ERR: {e}"
                    save_orders(d)
        self._send(200, "ok")

def main():
    port = int(os.environ.get("PORT", "8080"))
    srv = HTTPServer(("127.0.0.1", port), H)
    print(f"request_delivery listening on http://127.0.0.1:{port}")
    srv.serve_forever()

if __name__ == "__main__":
    main()
