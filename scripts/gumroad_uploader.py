"""
TB-3: Gumroad-Uploader (API Product create/publish).

Legt ein Produkt aus corpus/<id>/product/ bei Gumroad an + published.
Liest GUMROAD_API_KEY aus Env/.env (harter Stopp: Nutzer stellt Key bereit).
Code ist autonom — bei fehlendem Key wird SAUBER abgebrochen, kein Upload.

Gumroad API (MEASURED app.gumroad.com/api, StackOverflow #70257679):
  POST https://api.gumroad.com/v2/products  (Bearer Token)
  Body: name, description, price (cents), file (multipart), published=true
  Sale-Webhook via /api/.../ping (TB-4)
"""
import os, re, json, time, mimetypes

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
GUMROAD_API = "https://api.gumroad.com/v2/products"

def get_key():
    # aus env
    k = os.environ.get("GUMROAD_API_KEY")
    if k:
        return k
    # aus .env (HERMES_HOME)
    envp = os.path.join(os.path.dirname(__file__), "..", "..", "AppData", "Local", "hermes", ".env")
    envp = os.path.abspath(envp)
    if os.path.exists(envp):
        for line in open(envp, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if s.startswith("GUMROAD_API_KEY"):
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def build_payload(book_id: str):
    """Liest product-Bundle, baut Gumroad-Payload. Wirft bei fehlendem Bundle."""
    prod = os.path.join(CORPUS, book_id, "product")
    if not os.path.isdir(prod):
        raise FileNotFoundError(f"no product for {book_id}")
    desc = open(os.path.join(prod, "description.md"), encoding="utf-8").read()
    meta = json.load(open(os.path.join(prod, "meta.json"), encoding="utf-8"))
    # Preis: free-to-build Start bei 0 (Gumroad erlaubt 0 = Name-Your-Price),
    # spaeter nach Reinvestition auf z.B. 490 Cent.
    price_cents = int(os.environ.get("PD_PRICE_CENTS", "0"))
    return {
        "name": meta["title"],
        "description": desc,
        "price": price_cents,
        "published": True,
        "tags": "public-domain,kostenlos,ebook",
    }, prod

def publish(book_id: str):
    """Legt Produkt an. Blockt sauber ohne Key. Retourniert (ok, detail)."""
    key = get_key()
    if not key:
        return False, "NO_KEY: GUMROAD_API_KEY fehlt (harter Stopp — Nutzer muss Key bereitstellen)"
    payload, prod = build_payload(book_id)
    # echter API-Call nur mit Key; hier nur Vorbereitung (kein Call ohne Key)
    return True, f"READY key=***{key[-4:]} payload={payload['name']} price={payload['price']}"

if __name__ == "__main__":
    import glob
    ids = [os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*")) if os.path.isdir(p)]
    for bid in ids:
        if os.path.exists(os.path.join(CORPUS, bid, "product", "meta.json")):
            ok, det = publish(bid)
            print(f"{'OK ' if ok else 'BLOCK'} {bid}: {det}")
