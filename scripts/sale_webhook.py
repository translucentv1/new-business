"""
TB-4: Sale-Webhook + Reinvestitions-Logik.

Flask-frei (stdlib http.server), damit keine Pip-Abhaengigkeit.
Endpoint /gumroad/webhook:
  - empfaengt POST (Gumroad Sale-Ping, AWS-Signatur)
  - verifiziert Signatur (HMAC via GUMROAD_WEBHOOK_SECRET)
  - belegt MEASURED Sale in sales.log
  - triggert Reinvestition (Gewinn -> Scraper/LLM-Tokens) laut ADR-0005

Nahtstelle aus spec.md: hier wird "echtes Geld" sichtbar.
"""
import os, json, hmac, hashlib, time
from http.server import BaseHTTPRequestHandler, HTTPServer

SALES_LOG = os.path.join(os.path.dirname(__file__), "..", "sales.log")
REINVEST_LOG = os.path.join(os.path.dirname(__file__), "..", "reinvest.log")

def get_secret():
    k = os.environ.get("GUMROAD_WEBHOOK_SECRET")
    if k:
        return k
    envp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "AppData", "Local", "hermes", ".env"))
    if os.path.exists(envp):
        for line in open(envp, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if s.startswith("GUMROAD_WEBHOOK_SECRET"):
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def verify_signature(body: bytes, sig: str) -> bool:
    secret = get_secret()
    if not secret:
        return False  # ohne Secret kein Vertrauen
    exp = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(exp, sig or "")

def record_sale(payload: dict):
    price = payload.get("price", 0)
    sale = {"ts": int(time.time()), "price": price, "email": payload.get("email", ""), "raw": payload}
    with open(SALES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(sale, ensure_ascii=False) + "\n")
    return sale

def reinvest(price: int):
    """ADR-0005: Gewinn -> Scraper/LLM-Tokens. Nur Logging (kein echter Kauf ohne OK)."""
    with open(REINVEST_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": int(time.time()), "amount_cents": price, "plan": "reinvest_scraper_llm"}, ensure_ascii=False) + "\n")
    return price

def handle_ping(payload: dict) -> tuple[bool, str]:
    price = payload.get("price", 0)
    record_sale(payload)
    if price > 0:
        reinvest(price)
    return True, f"sale recorded price={price}"

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/gumroad/webhook":
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        sig = self.headers.get("X-Gumroad-Signature", "")
        if not verify_signature(body, sig):
            self.send_response(403); self.end_headers(); return
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400); self.end_headers(); return
        ok, msg = handle_ping(payload)
        self.send_response(200 if ok else 500)
        self.end_headers()
        self.wfile.write(msg.encode())

    def log_message(self, *a):
        pass  # still

if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_PORT", "8080"))
    print(f"webhook listening on :{port}/gumroad/webhook")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
