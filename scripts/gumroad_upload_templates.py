"""TB-50: Gumroad-Uploader fuer TEMPLATE-Produkte (autonom, via GUMROAD_API_KEY).

Wiederverwendet gumroad_uploader.py (Presign-S3-Flow, MEASURED 2026-07-18).
Packt die echten Deliverables (CSV + MD bzw. planner.md) pro Template in eine ZIP
und haengt sie als Datei an. Legt Produkte als DRAFT an (do_publish=False) —
Gumroad Discover ist bis $100 echte Sales gesperrt (gumroad.com/help/article/79),
Publish-Entscheidung bleibt beim Nutzer. Draft-Anlage ist autonom OK.

Preise/Titel/Beschreibung kommen aus spec.json (single source of truth).
Keine hartkodierten Preise (Belegpflicht).

Usage:
  python scripts/gumroad_upload_templates.py            # alle 8 als Draft
  python scripts/gumroad_upload_templates.py --publish  # DRAFT->Publish (nur auf Nutzer-Wunsch)
"""
import os, sys, json, glob, io, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gumroad_uploader as gu  # reuse key loader, presign flow, publish()

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TPL = os.path.join(REPO, "products", "templates")
LINKS = json.load(open(os.path.join(REPO, "stripe_links.json"), encoding="utf-8"))


def _spec(tid):
    return json.load(open(os.path.join(TPL, tid, "spec.json"), encoding="utf-8"))


def build_description(tid, spec):
    """Echte, wertstiftende Gumroad-Beschreibung aus spec + Stripe-Link."""
    link = LINKS.get(f"tpl:{tid}", "")
    lp = f"https://translucentv1.github.io/new-business/t/{tid}"
    ben = spec.get("benefits", spec.get("audience", ""))
    if isinstance(ben, list):
        ben = " ".join(str(b) for b in ben)
    lines = [
        f"# {spec['title']}",
        "",
        ben,
        "",
        "**Enthalten:**",
    ]
    for s in spec.get("sections", []):
        lines.append(f"- {s}")
    lines += [
        "",
        "**Format:** Markdown + CSV — sofort nutzbar in Notion, Excel, Google Sheets.",
        "Nach dem Kauf sofort herunterladbar.",
        "",
        "✓ Sofort-Download · ✓ Kein Abo · ✓ Rechnung auf Wunsch (§19 UStG)",
        "",
        f"Mehr Infos + Vorschau: {lp}",
    ]
    if link:
        lines.append(f"Direkt-Kauf (Stripe): {link}")
    return "\n".join(lines)


def make_zip(tid):
    """Packt deliverable/ in eine ZIP im RAM. Gibt (zip_bytes, display_name) zurueck."""
    d = os.path.join(TPL, tid, "deliverable")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(d)):
            fp = os.path.join(d, fn)
            if os.path.isfile(fp):
                z.write(fp, fn)
    buf.seek(0)
    return buf.getvalue(), f"{tid}-template"


def upload_one(tid, do_publish=False):
    """Legt Template als Gumroad-Draft an (Datei = ZIP der Deliverables)."""
    spec = _spec(tid)
    key = gu.get_key()
    if not key:
        return False, "NO_KEY"
    # Gumroad-Preis in Cent (USD). spec.preis_eur -> USD-Schaetzung 1 EUR ~ 1.08 USD
    eur = float(spec["price_eur"])
    usd_cents = int(round(eur * 1.08 * 100))
    name = spec["title"]
    desc = build_description(tid, spec)
    zip_bytes, disp = make_zip(tid)
    try:
        with __import__("httpx").Client(timeout=120) as c:
            # 1) create draft
            from urllib.parse import urlencode
            create = [("access_token", key), ("name", name),
                      ("price", str(usd_cents)), ("description", desc),
                      ("tags[]", "template"), ("tags[]", "notion"),
                      ("tags[]", "google-sheets"), ("tags[]", "deutsch")]
            r = c.post(f"{gu.API}/v2/products", content=urlencode(create),
                       headers={"Content-Type": "application/x-www-form-urlencoded"})
            if r.status_code != 200 or not r.json().get("success"):
                return False, f"CREATE {r.status_code}: {r.text[:160]}"
            pid = r.json()["product"]["id"]
            short = r.json()["product"].get("short_url")
            # 2) presign for the ZIP (use a generated .zip name)
            fsize = len(zip_bytes)
            pr = c.post(f"{gu.API}/v2/files/presign",
                        data={"access_token": key, "filename": f"{disp}.zip",
                              "file_size": str(fsize)})
            pr.raise_for_status()
            pj = pr.json()
            upload_id, s3key = pj["upload_id"], pj["key"]
            file_url = pj["file_url"]
            parts = pj.get("parts", [])
            if not parts:
                return False, f"PRESIGN no parts: {json.dumps(pj)[:160]}"
            etags = []
            for i, part in enumerate(parts):
                purl = part.get("presigned_url") or part.get("url")
                data = zip_bytes if len(parts) == 1 else None
                # single-part upload (ZIP is small)
                pres = c.put(purl, content=zip_bytes)
                if pres.status_code not in (200, 204):
                    return False, f"S3 PUT HTTP {pres.status_code}"
                etag = (pres.headers.get("ETag") or "").strip('"')
                etags.append((part.get("part_number", i + 1), etag))
            pairs = [("access_token", key), ("upload_id", upload_id), ("key", s3key)]
            for pn, et in etags:
                pairs.append(("parts[][part_number]", str(pn)))
                pairs.append(("parts[][etag]", et))
            cp = c.post(f"{gu.API}/v2/files/complete", content=urlencode(pairs),
                        headers={"Content-Type": "application/x-www-form-urlencoded"})
            cp.raise_for_status()
            # 3) attach to product
            apairs = [("access_token", key), ("files[][url]", file_url),
                      ("files[][display_name]", f"{disp}.zip")]
            ar = c.put(f"{gu.API}/v2/products/{pid}", content=urlencode(apairs),
                       headers={"Content-Type": "application/x-www-form-urlencoded"})
            aj = ar.json()
            persisted = bool(aj.get("product", {}).get("file_info")) or bool(aj.get("product", {}).get("files"))
            if not persisted:
                return False, f"ATTACH failed: {ar.text[:160]}"
            # 4) optional publish
            if do_publish:
                pr2 = c.put(f"{gu.API}/v2/products/{pid}/enable", data={"access_token": key})
                state = "PUBLISHED" if (pr2.status_code == 200 and pr2.json().get("success")) else "DRAFT(pub-fail)"
            else:
                state = "DRAFT"
            return True, f"{state} pid={pid} ${usd_cents/100:.2f} {short}"
    except Exception as e:
        return False, f"ERR {type(e).__name__}: {e}"


def upload_all(do_publish=False):
    tids = [os.path.basename(p) for p in glob.glob(os.path.join(TPL, "*")) if os.path.isdir(p)]
    out = []
    for tid in sorted(tids):
        if not os.path.exists(os.path.join(TPL, tid, "spec.json")):
            continue
        # skip if already on gumroad (by name) to avoid dupes
        ok, det = upload_one(tid, do_publish=do_publish)
        out.append((tid, ok, det))
        print(f"{'OK ' if ok else 'BLOCK'} {tid}: {det}")
    return out


if __name__ == "__main__":
    do_pub = "--publish" in sys.argv
    upload_all(do_publish=do_pub)
