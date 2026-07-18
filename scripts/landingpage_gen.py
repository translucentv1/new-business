"""
TB-6: Landingpage-Generator (ADR-0007 distribution).
Liest jedes product-Bundle und erzeugt statisches, SEO-optimiertes HTML:
  docs/site/<id>/index.html  (pro Produkt, mit Gumroad-Link + OG-Tags)
  docs/site/index.html       (Uebersicht aller Produkte)
GitHub-Pages-faehig (relativ-pfadfaehig). Kein externer Call.
"""
import os, json, glob

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
SITE = os.path.join(os.path.dirname(__file__), "..", "docs", "site")

GUMROAD_BASE = "https://philippbehnisch.gumroad.com/l/"  # short_url-Praefix; im Loop durch echte URL ersetzt
LANG = "de"


def _product_bundles():
    out = []
    for d in sorted(glob.glob(os.path.join(CORPUS, "*"))):
        bid = os.path.basename(d)
        meta_p = os.path.join(d, "product", "meta.json")
        desc_p = os.path.join(d, "product", "description.md")
        if os.path.exists(meta_p) and os.path.exists(desc_p):
            with open(meta_p, encoding="utf-8") as mh:
                meta = json.load(mh)
            with open(desc_p, encoding="utf-8") as fh:
                desc = fh.read()
            out.append((bid, meta, desc))
    return out


def product_html(bid, meta, desc, gumroad_url):
    title = meta["title"]
    author = meta.get("author", "Unbekannt")
    year = meta.get("year", "")
    blurb = desc.strip().split("\n")[0][:300]
    return f"""<!DOCTYPE html>
<html lang="{LANG}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} von {author} – kostenlos lesen / gratis eBook (Public Domain)</title>
  <meta name="description" content="{title} von {author} – aufbereitete Public-Domain-Ausgabe. Jetzt als eBook herunterladen.">
  <meta property="og:title" content="{title} von {author}">
  <meta property="og:description" content="Aufbereitete Public-Domain-Ausgabe – als eBook erh\u00e4ltlich.">
  <meta property="og:type" content="website">
  <meta name="robots" content="index,follow">
</head>
<body>
  <article>
    <h1>{title}</h1>
    <p class="byline">von {author}{(' (' + str(year) + ')') if year else ''}</p>
    <p>{blurb}</p>
    <p>Diese Ausgabe ist gemeinfrei (Public Domain) und vom Agenten neu gegliedert und
       modernisiert worden. Als bequemes eBook erh\u00e4ltlich:</p>
    <p><a class="buy" href="{gumroad_url}">Jetzt als eBook erh\u00e4ltlich ({GUMROAD_BASE and 'Gumroad'})</a></p>
  </article>
</body>
</html>
"""


def index_html(entries):
    rows = "\n".join(
        f'    <li><a href="{bid}/index.html">{m["title"]}</a> – {m.get("author","")}</li>'
        for bid, m, g in entries
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


def build(gumroad_urls=None):
    """gumroad_urls: dict bid->url. Ohne Angabe wird Platzhalter-Link gesetzt."""
    gumroad_urls = gumroad_urls or {}
    bundles = _product_bundles()
    entries = []
    for bid, meta, desc in bundles:
        url = gumroad_urls.get(bid, f"{GUMROAD_BASE}{bid}")
        os.makedirs(os.path.join(SITE, bid), exist_ok=True)
        with open(os.path.join(SITE, bid, "index.html"), "w", encoding="utf-8") as f:
            f.write(product_html(bid, meta, desc, url))
        entries.append((bid, meta, url))
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html(entries))
    return len(entries)


if __name__ == "__main__":
    n = build()
    print(f"Generated {n} product pages + index at {SITE}")
