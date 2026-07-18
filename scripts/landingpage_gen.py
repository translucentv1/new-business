"""Landingpage-Generator (ADR-0012): Stripe-Payment-Links + Fulfillment-Seite.

Liest jedes product-Bundle und erzeugt statisches, SEO-optimiertes HTML:
  <SITE>/<id>/index.html   (pro Produkt: voller Buchtext + Stripe-Kaufbutton)
  <SITE>/index.html        (Uebersicht aller Produkte)
GitHub-Pages-faehig (root-level, relativer Pfad). Kein externer Call.

Der Kauflink kommt aus stripe_links.json; fehlt er (Key noch nicht da),
wird ein klarer "Bald erhaeltlich"-Platzhalter gesetzt (kein toter Gumroad-Link).
"""
import os, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "corpus")
SITE = os.path.join(HERE, "..", "docs")
LINKS = os.path.join(HERE, "..", "stripe_links.json")
LANG = "de"


def _load_links():
    if os.path.exists(LINKS):
        try:
            return json.load(open(LINKS, encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def _product_bundles():
    out = []
    for d in sorted(glob.glob(os.path.join(CORPUS, "*"))):
        bid = os.path.basename(d)
        meta_p = os.path.join(d, "product", "meta.json")
        desc_p = os.path.join(d, "product", "description.md")
        content_p = os.path.join(d, "product", "content.md")
        if os.path.exists(meta_p) and os.path.exists(desc_p):
            meta = json.load(open(meta_p, encoding="utf-8"))
            desc = open(desc_p, encoding="utf-8").read()
            content = open(content_p, encoding="utf-8").read() if os.path.exists(content_p) else ""
            out.append((bid, meta, desc, content))
    return out


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def product_html(bid, meta, desc, content, buy_url):
    title = _esc(meta["title"])
    author = _esc(meta.get("author", "Unbekannt"))
    year = meta.get("year", "")
    year_s = f" ({year})" if year else ""
    blurb = _esc(desc.strip().split("\n")[0][:300])
    chapters = meta.get("chapters", "?")
    chars = meta.get("chars", 0)
    if buy_url:
        buy_btn = (
            f'    <p class="buy"><a class="buy-btn" href="{buy_url}">'
            f'Jetzt als eBook kaufen (&euro;{_price_eur()})</a></p>'
        )
    else:
        buy_btn = (
            '    <p class="buy"><strong>Bald erhaeltlich.</strong> '
            'Die Bestelllinks werden gerade aktiviert &mdash; komm in '
            'Kuerze zurueck.</p>'
        )
    # Full book text as the fulfillment deliverable (public domain).
    body_text = _esc(content) if content else _esc(desc)
    return f"""<!DOCTYPE html>
<html lang="{LANG}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} von {author}{year_s} – eBook (Public Domain)</title>
  <meta name="description" content="{title} von {author} – aufbereitete Public-Domain-Ausgabe als eBook. {blurb}">
  <meta property="og:title" content="{title} von {author}">
  <meta property="og:description" content="Aufbereitete Public-Domain-Ausgabe – als eBook erhaeltlich.">
  <meta property="og:type" content="website">
  <meta name="robots" content="index,follow">
  <style>
    body{{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6;color:#1a1a1a}}
    h1{{font-size:1.9em}} .byline{{color:#666;font-style:italic;margin-top:-.4em}}
    .buy{{margin:1.4em 0;padding:1em;background:#f4f7ff;border-left:4px solid #2962ff;border-radius:6px}}
    .buy-btn{{display:inline-block;background:#2962ff;color:#fff;padding:.7em 1.3em;border-radius:6px;text-decoration:none;font-weight:bold}}
    .buy-btn:hover{{background:#1c44b2}}
    pre.book{{white-space:pre-wrap;font-family:inherit;font-size:.98em}}
    .back{{margin-top:2em;font-size:.9em}}
  </style>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <p class="byline">von {author}{year_s}</p>
    <p>{blurb}</p>
    {buy_btn}
    <h2>Ueber diese Ausgabe</h2>
    <p>Diese Ausgabe ist gemeinfrei (Public Domain) und wurde neu gegliedert
       und mit einem Register versehen. {chapters} Kapitel, ca. {chars:,} Zeichen.
       Nach dem Kauf wirst du hierher zurueckgeleitet und kannst den vollen Text
       sofort lesen.</p>
    <h2>Leseprobe / Volltext</h2>
    <pre class="book">{body_text[:120000]}</pre>
    <p class="back"><a href="../index.html">Zurueck zur Uebersicht</a></p>
  </article>
</body>
</html>
"""


def _price_eur() -> str:
    try:
        import pricing
        return f"{pricing.get_price_cents()/100:.2f}".replace(".", ",")
    except Exception:
        return "3,99"


def _sitemap(entries):
    base = "https://translucentv1.github.io/new-business"
    urls = [f"  <url><loc>{base}/</loc></url>"]
    for bid, m, g, c, url in entries:
        urls.append(f"  <url><loc>{base}/{bid}/</loc></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def _robots():
    return ("User-agent: *\nAllow: /\n\n"
            "Sitemap: https://translucentv1.github.io/new-business/sitemap.xml\n")


def index_html(entries):
    rows = "\n".join(
        f'    <li><a href="{bid}/index.html">{_esc(m["title"])}</a> – {_esc(m.get("author",""))}'
        + (f' ({m["year"]})' if m.get("year") else '')
        + '</li>'
        for bid, m, g, c, url in entries
    )
    return f"""<!DOCTYPE html>
<html lang="{LANG}">
<head>
  <meta charset="utf-8">
  <title>Public-Domain eBooks – kostenlos lesen</title>
  <meta name="description" content="Aufbereitete Public-Domain-Klassiker als eBook.">
  <meta name="robots" content="index,follow">
</head>
<body>
  <h1>Public-Domain eBooks</h1>
  <ul>
{rows}
  </ul>
</body>
</html>
"""


def build():
    links = _load_links()
    bundles = _product_bundles()
    entries = []
    for bid, meta, desc, content in bundles:
        url = links.get(bid)
        os.makedirs(os.path.join(SITE, bid), exist_ok=True)
        with open(os.path.join(SITE, bid, "index.html"), "w", encoding="utf-8") as f:
            f.write(product_html(bid, meta, desc, content, url))
        entries.append((bid, meta, desc, content, url))
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html(entries))
    # SEO: sitemap + robots for faster/broader indexing (traffic = sales).
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(_sitemap(entries))
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(_robots())
    wired = [b for b, *_ in entries if _[-1]]
    print(f"Generated {len(entries)} product pages + index at {SITE}")
    print(f"Stripe-Links wired for: {wired} | placeholders for rest: {[b for b in [e[0] for e in entries] if b not in wired]}")
    return len(entries)


if __name__ == "__main__":
    n = build()
    print(f"Done ({n}).")
