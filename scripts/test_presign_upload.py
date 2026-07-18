"""
Gumroad file-upload via the CURRENT (presign S3) flow.
Primary source: antiwork/gumroad issue #4477 (Gumroad team answer, Apr 2026).
Flow: presign -> S3 PUT -> complete -> attach via PUT /v2/products/{id} files[][url].

This is a STANDALONE TEST for ONE product (book_id passed as argv[1], default 1342).
It creates a DRAFT product (not published), attaches the file, and reports MEASURED
results at every step. It does NOT publish. Cleanup is manual/confirmed by user.
"""
import os, sys, json, glob
import httpx

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
API = "https://api.gumroad.com"

def get_key():
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".gumroad_secrets"))
    for line in open(p, encoding="utf-8"):
        s = line.strip()
        if s.startswith("GUMROAD_API_KEY="):
            return s.split("=", 1)[1].strip()
    raise SystemExit("NO KEY")

def main():
    book_id = sys.argv[1] if len(sys.argv) > 1 else "1342"
    key = get_key()
    prod_dir = os.path.join(CORPUS, book_id, "product")
    meta = json.load(open(os.path.join(prod_dir, "meta.json"), encoding="utf-8"))
    desc = open(os.path.join(prod_dir, "description.md"), encoding="utf-8").read()
    content_path = os.path.join(prod_dir, "content.md")
    fsize = os.path.getsize(content_path)
    fname = f"{meta['title']}.md"
    print(f"[0] book={book_id} title={meta['title']!r} file={fname} size={fsize}B", flush=True)

    with httpx.Client(timeout=120) as c:
        # STEP 1: presign
        r = c.post(f"{API}/v2/files/presign",
                   data={"access_token": key, "filename": fname, "file_size": str(fsize)})
        print(f"[1] presign HTTP={r.status_code}", flush=True)
        if r.status_code != 200 or not r.json().get("success", True):
            print("   BODY:", r.text[:300], flush=True); return
        pj = r.json()
        upload_id = pj.get("upload_id"); s3key = pj.get("key")
        file_url = pj.get("file_url"); parts = pj.get("parts", [])
        print(f"   upload_id={upload_id} key={s3key} file_url={file_url} parts={len(parts)}", flush=True)
        if not parts:
            print("   NO PARTS returned:", json.dumps(pj)[:400], flush=True); return

        # STEP 2: PUT bytes to each part's presigned S3 URL
        data = open(content_path, "rb").read()
        etags = []
        # single part (file < 100MB)
        for i, part in enumerate(parts):
            purl = part.get("presigned_url") or part.get("url")
            pnum = part.get("part_number", i + 1)
            pr = c.put(purl, content=data)
            etag = pr.headers.get("ETag") or pr.headers.get("etag")
            print(f"[2] part#{pnum} S3 PUT HTTP={pr.status_code} ETag={etag}", flush=True)
            if pr.status_code not in (200, 204):
                print("   S3 ERR:", pr.text[:200], flush=True); return
            etags.append({"part_number": pnum, "etag": (etag or "").strip('"')})

        # STEP 3: complete — build urlencoded body manually (httpx list-of-tuples bug)
        from urllib.parse import urlencode
        pairs = [("access_token", str(key)), ("upload_id", str(upload_id)), ("key", str(s3key))]
        for e in etags:
            pairs.append(("parts[][part_number]", str(e["part_number"])))
            pairs.append(("parts[][etag]", str(e["etag"])))
        body = urlencode(pairs)
        r = c.post(f"{API}/v2/files/complete", content=body,
                   headers={"Content-Type": "application/x-www-form-urlencoded"})
        print(f"[3] complete HTTP={r.status_code} body={r.text[:200]}", flush=True)

        # STEP 4: create product (draft) then attach file
        r = c.post(f"{API}/v2/products",
                   data={"access_token": key, "name": meta["title"],
                         "price": "0", "description": desc})
        print(f"[4a] create HTTP={r.status_code} success={r.json().get('success')}", flush=True)
        if not r.json().get("success"):
            print("   ERR:", r.text[:200], flush=True); return
        pid = r.json()["product"]["id"]
        short = r.json()["product"].get("short_url")
        print(f"   pid={pid} short_url={short}", flush=True)

        # attach file via PUT files[][url] (urlencoded body, same httpx workaround)
        apairs = [("access_token", str(key)),
                  ("files[][url]", str(file_url)),
                  ("files[][display_name]", str(meta["title"]))]
        abody = urlencode(apairs)
        r = c.put(f"{API}/v2/products/{pid}", content=abody,
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
        aj = r.json()
        file_info = aj.get("product", {}).get("file_info", {})
        files_arr = aj.get("product", {}).get("files", [])
        print(f"[4b] attach HTTP={r.status_code} success={aj.get('success')}", flush=True)
        print(f"   file_info={json.dumps(file_info)[:200]}", flush=True)
        print(f"   files={json.dumps(files_arr)[:300]}", flush=True)
        persisted = bool(file_info) or bool(files_arr)
        print(f"[RESULT] file PERSISTED = {persisted}  pid={pid}  short_url={short}", flush=True)
        print(f"[CLEANUP-CMD] delete with: curl -X DELETE '{API}/v2/products/{pid}?access_token=***'", flush=True)

if __name__ == "__main__":
    main()
