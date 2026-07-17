"""
TB-4 (revised): Sale-Poller + Reinvestitions-Logik.

KEIN Webhook-Server mehr (lokale Instanz hat keine oeffentliche URL).
Stattdessen: Gumroad /sales API pollen (alle Xh via Loop), neue Sales
belegen (MEASURED) in sales.log, triggert Reinvestition (ADR-0005).

API (MEASURED app.gumroad.com/api):
  GET https://api.gumroad.com/v2/sales  (Bearer Token)
  Antwort: { sales: [ { price, email, created_at, product_id, ... } ] }
"""
import os, json, time, httpx

SALES_LOG = os.path.join(os.path.dirname(__file__), "..", "sales.log")
REINVEST_LOG = os.path.join(os.path.dirname(__file__), "..", "reinvest.log")
GUMROAD_SALES = "https://api.gumroad.com/v2/sales"

def get_key():
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".gumroad_secrets"))
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if s.startswith("GUMROAD_API_KEY="):
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GUMROAD_API_KEY")

def _last_seen_ts():
    if not os.path.exists(SALES_LOG):
        return 0
    last = 0
    for line in open(SALES_LOG, encoding="utf-8"):
        try:
            s = json.loads(line)
            last = max(last, s.get("ts", 0))
        except json.JSONDecodeError:
            continue
    return last

def record_sale(sale: dict):
    with open(SALES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(sale, ensure_ascii=False) + "\n")
    return sale

def reinvest(price: int):
    """ADR-0005: Gewinn -> Scraper/LLM-Tokens. Nur Logging."""
    with open(REINVEST_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": int(time.time()), "amount_cents": price,
                            "plan": "reinvest_scraper_llm"}, ensure_ascii=False) + "\n")
    return price

def poll() -> tuple[int, str]:
    """Fragt Gumroad-Sales ab, belegt neue. Retourniert (neue_anzahl, detail)."""
    key = get_key()
    if not key:
        return 0, "NO_KEY"
    try:
        r = httpx.get(GUMROAD_SALES, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    except Exception as e:
        return 0, f"REQ_ERR {e}"
    if r.status_code != 200:
        return 0, f"HTTP {r.status_code}: {r.text[:120]}"
    data = r.json()
    sales = data.get("sales", [])
    last_ts = _last_seen_ts()
    new = 0
    for s in sales:
        # Gumroad created_at ist ISO-String; ts aus json-ts oder parse
        ts = int(time.mktime(time.strptime(s["created_at"], "%Y-%m-%dT%H:%M:%SZ"))) if s.get("created_at") else int(time.time())
        if ts > last_ts:
            price = int(float(s.get("price", 0)) * 100)
            rec = {"ts": ts, "price": price, "email": s.get("email", ""),
                   "product_id": s.get("product_id", ""), "sale_id": s.get("id", "")}
            record_sale(rec)
            if price > 0:
                reinvest(price)
            new += 1
    return new, f"poll ok, {new} new sales"

if __name__ == "__main__":
    n, det = poll()
    print(f"[{'OK' if n >= 0 else 'ERR'}] {det}")
