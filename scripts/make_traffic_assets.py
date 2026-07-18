"""Generate traffic-ready assets (Pinterest images + Reddit/title posts) per book.

Autonomous prep: when products are PUBLISHED (after payment method connected) and
social creds exist, these drop straight into Pinterest/Reddit. No network, no post.
Output: assets/<book_id>/{pin.png, reddit.txt}
"""
import os, json, glob
from PIL import Image, ImageDraw, ImageFont

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
PAGE_BASE = "https://translucentv1.github.io/new-business"


def font(sz):
    try:
        return ImageFont.truetype("arial.ttf", sz)
    except Exception:
        return ImageFont.load_default()


def make_pin(book_id, title, url):
    os.makedirs(os.path.join(ASSETS, book_id), exist_ok=True)
    W, H = 1000, 1500
    img = Image.new("RGB", (W, H), (18, 18, 22))
    d = ImageDraw.Draw(img)
    # title block
    d.text((60, 180), "PUBLIC-DOMAIN", font=font(48), fill=(255, 210, 80))
    # wrap title
    words = title.split()
    lines, cur = [], ""
    for w in words:
        if len(cur + " " + w) < 16:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    y = 280
    for ln in lines[:5]:
        d.text((60, y), ln, font=font(72), fill=(255, 255, 255))
        y += 90
    d.text((60, H - 360), "Kostenlos lesen", font=font(56), fill=(120, 220, 160))
    d.text((60, H - 280), url, font=font(34), fill=(180, 180, 200))
    out = os.path.join(ASSETS, book_id, "pin.png")
    img.save(out)
    return out


def make_reddit(book_id, title, url):
    txt = (
        f"{title} — kostenlos als Public-Domain-eBook\n\n"
        f"Vollständiger Text, keine Paywall, einfach lesen. "
        f"Public Domain, also rechtlich sauber.\n\n"
        f"Lese-Seite: {url}\n"
    )
    out = os.path.join(ASSETS, book_id, "reddit.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(txt)
    return out


def main():
    for bid in sorted(os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*")) if os.path.isdir(p)):
        mj = os.path.join(CORPUS, bid, "product", "meta.json")
        if not os.path.exists(mj):
            continue
        meta = json.load(open(mj, encoding="utf-8"))
        title = meta.get("title", bid)
        url = f"{PAGE_BASE}/{bid}/"
        p = make_pin(bid, title, url)
        r = make_reddit(bid, title, url)
        print(f"  {bid}: {os.path.basename(p)} + {os.path.basename(r)}")


if __name__ == "__main__":
    main()
