"""Landingpage-Generator (ADR-0012 + ADR-0013 Download-Gate).

Liest jedes product-Bundle und erzeugt statisches, SEO-optimiertes HTML:
  <SITE>/<id>/index.html   (pro Produkt: PREVIEW + Stripe-Kaufbutton)
  <SITE>/index.html        (Uebersicht aller Produkte)
GitHub-Pages-faehig (root-level, relativer Pfad). Kein externer Call.

ADR-0013 (Download-Gate): Die oeffentliche Seite zeigt nur eine Leseprobe
(Titel, Autor, Klappentext, vollstaendiges Inhaltsverzeichnis, ERSTES
Kapitel) + Kaufbutton. Der vollstaendige eBook-Text liegt unter einem
gehashten, nicht verlinkten Pfad docs/dl/<hash>/<slug>.html und wird NUR
ueber den Stripe-after_completion-Redirect ausgeliefert (siehe
deliverable_gen.py + TB-10). Kein Volltext mehr auf der Landingpage.
"""
import os, re, json, glob, sys

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


# ---------------------------------------------------------------------------
# Preview extraction (ADR-0013): TOC + first chapter only, never full text.
# ---------------------------------------------------------------------------
def extract_preview(content: str):
    """Return (toc_text, first_chapter_text) parsed from a product content.md.

    TOC = the block under '# Inhaltsverzeichnis' up to the first '## ' heading.
    First chapter = from the first '## ' heading after the TOC to the next
    '## ' heading (i.e. exactly one chapter of body text).
    """
    lines = content.splitlines()
    toc_start = None
    for i, l in enumerate(lines):
        if l.strip().startswith("# Inhaltsverzeichnis"):
            toc_start = i
            break
    search_from = toc_start if toc_start is not None else 0
    first_ch_idx = None
    for i in range(search_from, len(lines)):
        if re.match(r"^##\s", lines[i]):
            first_ch_idx = i
            break
    if first_ch_idx is None:
        # No chapter structure: fall back to first ~1200 chars as preview.
        return "", content[:1200]
    toc_text = "\n".join(lines[toc_start + 1:first_ch_idx]).strip() if toc_start is not None else ""
    ch_end = len(lines)
    for i in range(first_ch_idx + 1, len(lines)):
        if re.match(r"^##\s", lines[i]):
            ch_end = i
            break
    chapter_text = "\n".join(lines[first_ch_idx:ch_end]).strip()
    return toc_text, chapter_text


def _render_preview(toc_text: str, chapter_text: str) -> str:
    parts = []
    if toc_text:
        items = []
        for line in toc_text.splitlines():
            line = line.strip()
            if not line:
                continue
            items.append(f"    <li>{_esc(line)}</li>")
        if items:
            parts.append(
                '    <h2>Inhaltsverzeichnis</h2>\n    <ul class="toc">\n'
                + "\n".join(items)
                + "\n    </ul>"
            )
    if chapter_text:
        blocks = re.split(r"\n\s*\n", chapter_text)
        for b in blocks:
            para = " ".join(l.strip() for l in b.splitlines() if l.strip())
            if para:
                parts.append(f"    <p>{_esc(para)}</p>")
    return "\n".join(parts)


def product_html(bid, meta, desc, content, buy_url):
    title = _esc(meta["title"])
    author = _esc(meta.get("author", "Unbekannt"))
    year = meta.get("year", "")
    year_s = f" ({year})" if year else ""
    blurb = _esc(desc.strip().split("\n")[0][:300])
    chapters = meta.get("chapters", "?")
    chars = meta.get("chars", 0)
    # TB-11: sharpened SEO title/description (long-tail aligned).
    seo_title = f"{title} von {author}{year_s} – eBook als Download (Public Domain)"
    seo_desc = (f"{title} von {author}{year_s}: aufbereitete Public-Domain-Ausgabe "
                f"als eBook kaufen. Mit Leseprobe (Inhaltsverzeichnis + erstes Kapitel). "
                f"{chapters} Kapitel, ca. {chars:,} Zeichen.")
    # TB-11: JSON-LD Product schema for rich results.
    price_eur = _price_eur().replace(",", ".")
    json_ld = (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org/",\n'
        '  "@type": "Product",\n'
        f'  "name": {json.dumps(meta["title"] + " – eBook (Public Domain)")},\n'
        f'  "author": {{"@type": "Person", "name": {json.dumps(meta.get("author", "Unbekannt"))}}},\n'
        f'  "description": {json.dumps(seo_desc)},\n'
        '  "offers": {\n'
        '    "@type": "Offer",\n'
        f'    "price": "{price_eur}",\n'
        '    "priceCurrency": "EUR",\n'
        '    "availability": "https://schema.org/InStock"\n'
        '  }\n'
        '}\n'
        '</script>'
    )
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
    # ADR-0013: PREVIEW only (TOC + first chapter), never full text.
    # Corrupt bundles (PG credit / no chapter structure) get a placeholder
    # preview instead of a leaky broken page.
    from deliverable_gen import is_corrupt
    if is_corrupt(content):
        preview = (
            '    <p><em>Diese Ausgabe wird derzeit noch einmal '
            'aufbereitet und ist demnaechst mit Leseprobe erhaeltlich.</em></p>'
        )
    else:
        toc_text, chapter_text = extract_preview(content)
        preview = _render_preview(toc_text, chapter_text)
    return f"""<!DOCTYPE html>
<html lang="{LANG}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{seo_title}</title>
  <meta name="description" content="{_esc(seo_desc)}">
  <meta property="og:title" content="{title} von {author}">
  <meta property="og:description" content="Aufbereitete Public-Domain-Ausgabe – als eBook erhaeltlich.">
  <meta property="og:type" content="website">
  <meta name="robots" content="index,follow">
  {json_ld}
  <style>
    body{{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6;color:#1a1a1a}}
    h1{{font-size:1.9em}} .byline{{color:#666;font-style:italic;margin-top:-.4em}}
    .buy{{margin:1.4em 0;padding:1em;background:#f4f7ff;border-left:4px solid #2962ff;border-radius:6px}}
    .buy-btn{{display:inline-block;background:#2962ff;color:#fff;padding:.7em 1.3em;border-radius:6px;text-decoration:none;font-weight:bold}}
    .buy-btn:hover{{background:#1c44b2}}
    ul.toc{{line-height:1.8}}
    .back{{margin-top:2em;font-size:.9em}}
    .gate-note{{margin-top:1.4em;padding:1em;background:#fff7e6;border-left:4px solid #ff9800;border-radius:6px;font-size:.92em}}
  </style>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <p class="byline">von {author}{year_s}</p>
    <p>{blurb}</p>
    {buy_btn}
    <h2>Leseprobe</h2>
{preview}
    <div class="gate-note">Das vollstaendige, offline lesbare eBook erhaelst du
       direkt nach dem Kauf &mdash; Stripe leitet dich zum Download weiter.</div>
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
    # ADR-0013: Download-Gate-Pfad fuer Crawler unsichtbar halten.
    return ("User-agent: *\nAllow: /\n\n"
            "# Download-Gate Deliverables nicht crawlen/indexieren (ADR-0013)\n"
            "Disallow: /dl/\n\n"
            "Sitemap: https://translucentv1.github.io/new-business/sitemap.xml\n")


def index_html(entries):
    rows = "\n".join(
        f'    <li><a href="{bid}/index.html">{_esc(m["title"])}</a> – {_esc(m.get("author",""))}'
        + (f' ({m["year"]})' if m.get("year") else '')
        + '</li>'
        for bid, m, g, c, url in entries
    )
    json_ld = (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org/",\n'
        '  "@type": "ItemList",\n'
        '  "itemListElement": [\n'
        + ",\n".join(
            f'    {{"@type": "ListItem", "position": {i+1}, '
            f'"name": {json.dumps(m["title"] + " – eBook")}, '
            f'"url": "https://translucentv1.github.io/new-business/{bid}/"}}'
            for i, (bid, m, g, c, url) in enumerate(entries)
        )
        + '\n  ]\n}\n</script>'
    )
    return f"""<!DOCTYPE html>
<html lang="{LANG}">
<head>
  <meta charset="utf-8">
  <title>Public-Domain eBooks kaufen – Leseproben & Download (Frankenstein, Dracula, Moby-Dick u.a.)</title>
  <meta name="description" content="Aufbereitete Public-Domain-Klassiker als eBook kaufen – mit Leseprobe. Frankenstein, Dracula, Moby-Dick, Pride and Prejudice, Alice im Wunderland u.a.">
  <meta name="robots" content="index,follow">
  {json_ld}
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
    # SEO: sitemap + robots (Download-Gate-Pfad excluded).
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(_sitemap(entries))
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(_robots())
    # ADR-0013 TB-8: generate the self-contained download deliverables.
    sys.path.insert(0, HERE)
    import deliverable_gen
    dl_paths, dl_skipped = deliverable_gen.build_all()
    wired = [b for b, *_ in entries if _[-1]]
    print(f"Generated {len(entries)} product preview pages + index at {SITE}")
    print(f"Generated {len(dl_paths)} download deliverables under {os.path.join(SITE, 'dl')}")
    if dl_skipped:
        print(f"SKIPPED (corrupt bundle, not published): {dl_skipped}")
    print(f"Stripe-Links wired for: {wired} | placeholders for rest: {[b for b in [e[0] for e in entries] if b not in wired]}")
    return len(entries)


if __name__ == "__main__":
    n = build()
    print(f"Done ({n}).")
