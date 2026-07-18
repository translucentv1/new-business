"""
TB-3b: Gumroad-Uploader via CURRENT presign-S3 flow (ADR-0008).
Primary source: antiwork/gumroad issue #4477 (Gumroad team answer, Apr 2026),
end-to-end MEASURED 2026-07-18 ("file PERSISTED = True").

Flow: create draft product -> presign -> S3 PUT -> complete -> attach files[][url]
      -> optional publish.
Preis: pricing.get_price_cents() (ADR-0006, default 399 = $3.99).
Hard stop: without GUMROAD_API_KEY -> clean refusal (NO_KEY), no crash, no fake call.
"""
import os, json, glob
from urllib.parse import urlencode
import httpx

import sys
sys.path.insert(0, os.path.dirname(__file__))
import pricing

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
API = "https://api.gumroad.com"


def _read_secrets_file():
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".gumroad_secrets"))
    out = {}
    if os.path.exists(p):
        with open(p, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                s = line.strip()
                if "=" in s and not s.startswith("#"):
                    k, v = s.split("=", 1)
                    out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def get_key():
    k = os.environ.get("GUMROAD_API_KEY")
    if k:
        return k
    sec = _read_secrets_file()
    if sec.get("GUMROAD_API_KEY"):
        return sec["GUMROAD_API_KEY"]
    envp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                        "AppData", "Local", "hermes", ".env"))
    if os.path.exists(envp):
        with open(envp, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                s = line.strip()
                if s.startswith("GUMROAD_API_KEY"):
                    return s.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def build_payload(book_id: str):
    """Liest product-Bundle, baut Metadaten. Wirft bei fehlendem Bundle."""
    prod = os.path.join(CORPUS, book_id, "product")
    if not os.path.isdir(prod):
        raise FileNotFoundError(f"no product for {book_id}")
    with open(os.path.join(prod, "description.md"), encoding="utf-8") as fh:
        desc = fh.read()
    with open(os.path.join(prod, "meta.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    price_cents = pricing.get_price_cents()
    return {
        "name": meta["title"],
        "description": desc,
        "price": price_cents,
        "tags": "public-domain,ebook,klassiker",
    }, prod


def _presign_and_upload(client, key, prod_dir, display_name):
    """Presign -> S3 PUT -> complete. Returns file_url or raises."""
    content_path = os.path.join(prod_dir, "content.md")
    fsize = os.path.getsize(content_path)
    fname = f"{display_name}.md"
    r = client.post(f"{API}/v2/files/presign",
                    data={"access_token": key, "filename": fname, "file_size": str(fsize)})
    r.raise_for_status()
    pj = r.json()
    upload_id, s3key = pj["upload_id"], pj["key"]
    file_url, parts = pj["file_url"], pj.get("parts", [])
    if not parts:
        raise RuntimeError(f"presign returned no parts: {json.dumps(pj)[:200]}")
    data = open(content_path, "rb").read()
    etags = []
    for i, part in enumerate(parts):
        purl = part.get("presigned_url") or part.get("url")
        pnum = part.get("part_number", i + 1)
        pr = client.put(purl, content=data)
        if pr.status_code not in (200, 204):
            raise RuntimeError(f"S3 PUT part#{pnum} HTTP {pr.status_code}")
        etag = (pr.headers.get("ETag") or pr.headers.get("etag") or "").strip('"')
        etags.append((pnum, etag))
    pairs = [("access_token", key), ("upload_id", upload_id), ("key", s3key)]
    for pnum, etag in etags:
        pairs.append(("parts[][part_number]", str(pnum)))
        pairs.append(("parts[][etag]", etag))
    r = client.post(f"{API}/v2/files/complete", content=urlencode(pairs),
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    r.raise_for_status()
    return file_url


def publish(book_id: str, do_publish: bool = False):
    """Legt Produkt an + haengt Datei via Presign-Flow. Blockt sauber ohne Key.
    do_publish=False -> Draft (Default, sicher). Returns (ok, detail)."""
    key = get_key()
    if not key:
        return False, "NO_KEY: GUMROAD_API_KEY fehlt (harter Stopp — Nutzer muss Key bereitstellen)"
    try:
        payload, prod = build_payload(book_id)
    except Exception as e:
        return False, f"BUNDLE_ERR {e}"
    try:
        with httpx.Client(timeout=120) as c:
            # 1) create draft product
            r = c.post(f"{API}/v2/products",
                       data={"access_token": key, "name": payload["name"],
                             "price": str(payload["price"]), "description": payload["description"],
                             "tags": payload["tags"]})
            if r.status_code != 200 or not r.json().get("success"):
                return False, f"CREATE API {r.status_code}: {r.text[:160]}"
            pid = r.json()["product"]["id"]
            short = r.json()["product"].get("short_url")
            # 2) presign + upload + complete
            file_url = _presign_and_upload(c, key, prod, payload["name"])
            # 3) attach file to product
            apairs = [("access_token", key), ("files[][url]", file_url),
                      ("files[][display_name]", payload["name"])]
            r = c.put(f"{API}/v2/products/{pid}", content=urlencode(apairs),
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
            aj = r.json()
            persisted = bool(aj.get("product", {}).get("file_info")) or bool(aj.get("product", {}).get("files"))
            if not persisted:
                return False, f"ATTACH did not persist: {r.text[:160]}"
            # 4) optional publish
            if do_publish:
                pr = c.put(f"{API}/v2/products/{pid}/enable",
                           data={"access_token": key})
                pub_ok = pr.status_code == 200 and pr.json().get("success")
                state = "PUBLISHED" if pub_ok else "DRAFT(publish-failed)"
            else:
                state = "DRAFT"
            return True, f"{state} pid={pid} price={payload['price']} short_url={short}"
    except httpx.HTTPStatusError as e:
        return False, f"HTTP_ERR {e.response.status_code}: {e.response.text[:160]}"
    except Exception as e:
        return False, f"REQ_ERR {type(e).__name__}: {e}"


if __name__ == "__main__":
    ids = [os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*")) if os.path.isdir(p)]
    for bid in sorted(ids):
        if os.path.exists(os.path.join(CORPUS, bid, "product", "meta.json")):
            ok, det = publish(bid, do_publish=False)
            print(f"{'OK ' if ok else 'BLOCK'} {bid}: {det}")
