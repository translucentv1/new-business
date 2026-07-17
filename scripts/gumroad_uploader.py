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

def _read_secrets_file():
    """Projekt-lokale Secrets (gitignored), damit Hermes-.env (write-protected)
    nicht angefasst werden muss. Format: KEY=VALUE pro Zeile."""
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".gumroad_secrets"))
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if "=" in s and not s.startswith("#"):
                k, v = s.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def get_key():
    # 1) env
    k = os.environ.get("GUMROAD_API_KEY")
    if k:
        return k
    # 2) projekt-lokale secrets
    sec = _read_secrets_file()
    if sec.get("GUMROAD_API_KEY"):
        return sec["GUMROAD_API_KEY"]
    # 3) Hermes-.env (read-only, falls dort gepflegt)
    envp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "AppData", "Local", "hermes", ".env"))
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
    # echter API-Call
    try:
        files = {}
        content = os.path.join(prod, "content.md")
        if os.path.exists(content):
            files["file"] = (f"{payload['name']}.md", open(content, "rb"), "text/markdown")
        data = {k: v for k, v in payload.items() if k != "tags"}
        data["tags"] = payload["tags"]
        r = httpx.post(GUMROAD_API, headers={"Authorization": f"Bearer {key}"},
                       data=data, files=files, timeout=60)
        if r.status_code == 200 and r.json().get("success"):
            pid = r.json().get("product", {}).get("id")
            return True, f"PUBLISHED pid={pid} {payload['name']} price={payload['price']}"
        return False, f"API {r.status_code}: {r.text[:160]}"
    except Exception as e:
        return False, f"REQ_ERR {e}"

if __name__ == "__main__":
    import glob
    ids = [os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*")) if os.path.isdir(p)]
    for bid in ids:
        if os.path.exists(os.path.join(CORPUS, bid, "product", "meta.json")):
            ok, det = publish(bid)
            print(f"{'OK ' if ok else 'BLOCK'} {bid}: {det}")
