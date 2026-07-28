"""
KDP Cover + Interior Generator (GELD_STACKING #4).

Prepares Amazon KDP low-content / notebook products:
  1. Cover concept (title, subtitle, author, color scheme) -> image gen prompt
  2. Interior template spec (lined/grid/dotted, page count, bleed)
  3. A manifest.json per product for batch upload later

Amazon KDP requires manual upload via kdp.amazon.com (no public API for
creation). This script prepares everything; you upload + connect account.

NO credentials needed to RUN (prep only). NO hardcoded keys.
"""
import os
import json
import uuid

# KDP specs (public, documented): 6x9" / A5 common, 0.25" bleed, 24-108 pages
KDP_SIZES = {"6x9": "6x9in", "A5": "A5", "8x10": "8x10in"}


def cover_prompt(title: str, subtitle: str = "", theme: str = "minimal") -> str:
    return (
        f"Book cover design, {theme} style, title '{title}'"
        + (f", subtitle '{subtitle}'" if subtitle else "")
        + ". Clean typography, high contrast, no copyrighted elements. "
        "Matte finish look, centered composition."
    )


def build_product(title: str, subtitle: str = "", niche: str = "journal",
                  size: str = "6x9", pages: int = 120,
                  interior: str = "lined") -> dict:
    pid = uuid.uuid4().hex[:10]
    spec = {
        "id": pid,
        "title": title,
        "subtitle": subtitle,
        "niche": niche,
        "size": KDP_SIZES.get(size, size),
        "pages": pages,
        "interior": interior,  # lined | grid | dotted | blank
        "bleed": True,
        "cover_prompt": cover_prompt(title, subtitle, niche),
        "price_usd": 7.99,
        "status": "prepared",  # -> uploaded (manual)
        "created": os.environ.get("NOW", "2026-07-26"),
    }
    return spec


def save_product(spec: dict, outdir: str = "kdp_products") -> str:
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{spec['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    return path


def generate(title: str, subtitle: str = "", niche: str = "journal",
             size: str = "6x9", pages: int = 120, interior: str = "lined") -> dict:
    spec = build_product(title, subtitle, niche, size, pages, interior)
    path = save_product(spec)
    return {"spec": spec, "saved_to": path}


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "Mein Lesetagebuch"
    n = sys.argv[2] if len(sys.argv) > 2 else "journal"
    out = generate(t, niche=n)
    print(json.dumps(out["spec"], ensure_ascii=False, indent=2))
    print("saved:", out["saved_to"])
