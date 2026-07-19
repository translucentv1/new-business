"""SEO v3: pro-Kapitel Long-Tail-Seiten (autonome Nachtschicht).

Jede Kapitel-Seite targetiert den spezifischen Intent
"<Titel> Kapitel N Zusammenfassung" — echte, spezifische Suchende.
Seite buendelt: Kapitelzusammenfassung + Gesamt-Summary + Figuren +
Link zur Kaufseite. Substanz statt Thin-Content.

Nimmt gefuellte summary_placeholder aus study_guide.json (fill_chapter_summaries.py).
Ueberspringt Kapitel, die noch Platzhalter sind (kein Regressions-Bug).

Kein Hard Stop: reiner lokaler Content, kein Account/Geld/Netz.
"""
import os, re, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "corpus")
SITE = os.path.join(HERE, "..", "docs")
SEO_ROOT = os.path.join(SITE, "seo")
PAGE_BASE = "https://translucentv1.github.io/new-business"
LANG = "de"


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _slugify(t: str, fb: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return s or fb


def build():
    total = 0
    for d in sorted(glob.glob(os.path.join(CORPUS, "*"))):
        bid = os.path.basename(d)
        mj = os.path.join(d, "product", "meta.json")
        gj = os.path.join(d, "product", "study_guide.json")
        if not (os.path.exists(mj) and os.path.exists(gj)):
            continue
        meta = json.load(open(mj, encoding="utf-8"))
        guide = json.load(open(gj, encoding="utf-8"))
        title = meta["title"]
        author = meta.get("author", "Unbekannt")
        slug = _slugify(title, bid)
        overall = guide.get("summary", "")
        chars = guide.get("characters", [])
        product_url = f"{PAGE_BASE}/{bid}/"
        char_html = "".join(f"<li>{_esc(c)}</li>" for c in chars[:10]) or "<li>siehe Lese-Begleiter</li>"
        for i, ch in enumerate(guide.get("chapters", []), 1):
            summ = ch.get("summary_placeholder", "")
            if not summ or "ZUSAMMENFASSUNG Kapitel" in summ or "XXX" in summ:
                continue  # skip unfilled
            ch_title = ch.get("title", f"Kapitel {i}")
            out_dir = os.path.join(SEO_ROOT, slug, "kapitel", str(i))
            os.makedirs(out_dir, exist_ok=True)
            body = (
                f"<h2>{_esc(ch_title)} – Zusammenfassung</h2>\n"
                f"<p>{_esc(summ)}</p>\n"
                f"<h2>Kontext: {_esc(title)} insgesamt</h2>\n"
                f"<p>{_esc(overall)}</p>\n"
                f"<h2>Figuren</h2><ul class='toc'>{char_html}</ul>"
            )
            html = _PAGE.format(
                lang=LANG, title=_esc(title), author=_esc(author),
                topic=_esc(f"{title} {ch_title} Zusammenfassung"),
                desc=_esc(f"{title} {ch_title}: Zusammenfassung und Einordnung."),
                lead=_esc(f"Kapitelzusammenfassung zu {title} ({author})."),
                body=body, cta="Zum Lese-Begleiter", product_url=product_url,
                canonical=f"{PAGE_BASE}/seo/{slug}/kapitel/{i}/", base=PAGE_BASE,
            )
            with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
            total += 1
    print(f"Generated {total} chapter-level SEO pages")
    return total


_PAGE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} – {topic}</title>
  <meta name="description" content="{desc}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="website">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{canonical}">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Book",
    "name": "{title}",
    "author": {{ "@type": "Person", "name": "{author}" }},
    "description": "{desc}",
    "offers": {{ "@type": "Offer", "price": "3.99", "priceCurrency": "EUR", "availability": "https://schema.org/InStock" }}
  }}
  </script>
  <style>
    body{{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6;color:#1a1a1a}}
    h1{{font-size:1.9em}} .byline{{color:#666;font-style:italic;margin-top:-.4em}}
    .box{{margin:1.4em 0;padding:1em;background:#f4f7ff;border-left:4px solid #2962ff;border-radius:6px}}
    .btn{{display:inline-block;background:#2962ff;color:#fff;padding:.7em 1.3em;border-radius:6px;text-decoration:none;font-weight:bold}}
    .btn:hover{{background:#1c44b2}}
    .back{{margin-top:2em;font-size:.9em}}
    a{{color:#2962ff}}
    ul.toc{{line-height:1.9}}
  </style>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <p class="byline">von {author}</p>
    <div class="box">
      <p>{lead}</p>
      <p><a class="btn" href="{product_url}">{cta}</a></p>
    </div>
    {body}
    <p class="back"><a href="{product_url}">Zur Produktseite: {title}</a> · <a href="{base}/">Alle Public-Domain-eBooks</a></p>
  </article>
</body>
</html>
"""


if __name__ == "__main__":
    build()
