"""TB-SEO: Long-Tail-SEO-Seiten pro Buch (Pivot-Research Option A, ADR-0018-Kontext).

Erzeugt pro Buch 3 thematische Landingpages unter docs/seo/<slug>/index.html:
  - "<Titel> kostenlos lesen"        (lesen)
  - "<Titel> als eBook kaufen"       (kaufen)
  - "<Titel> Lese-Begleiter"         (begleiter)
Jede Seite verlinkt intern auf die Haupt-Produktseite (/<id>/) -> interne
Verlinkung fuer SEO. Kein externes Asset, kein <script src>, self-contained.
Seiten sind indexierbar (robots index,follow) und werden in sitemap.xml
aufgenommen. Das Download-Gate (/dl/) bleibt DISALLOWED.

Kein Hard Stop: reiner Content, lokale Verarbeitung, kein Account/Geld/Netz.
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


def _slugify(title: str, fallback: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or fallback


def _bundles():
    out = []
    for d in sorted(glob.glob(os.path.join(CORPUS, "*"))):
        bid = os.path.basename(d)
        mj = os.path.join(d, "product", "meta.json")
        dj = os.path.join(d, "product", "description.md")
        if os.path.exists(mj) and os.path.exists(dj):
            meta = json.load(open(mj, encoding="utf-8"))
            desc = open(dj, encoding="utf-8").read()
            blurb = desc.split("\n")[3].strip() if len(desc.split("\n")) > 3 else ""
            out.append((bid, meta, blurb))
    return out


_PAGE_TPL = """<!DOCTYPE html>
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
    <p>{body}</p>
    <p class="back"><a href="{product_url}">Zur Produktseite: {title}</a> · <a href="{base}/">Alle Public-Domain-eBooks</a></p>
  </article>
</body>
</html>
"""


def _page(title, author, topic, desc, lead, body, cta, product_url, canonical):
    return _PAGE_TPL.format(
        lang=LANG, title=_esc(title), author=_esc(author), topic=_esc(topic),
        desc=_esc(desc), lead=_esc(lead), body=_esc(body), cta=_esc(cta),
        product_url=product_url, canonical=canonical, base=PAGE_BASE,
    )


def build():
    bundles = _bundles()
    total = 0
    for bid, meta, blurb in bundles:
        title = meta["title"]
        author = meta.get("author", "Unbekannt")
        slug = _slugify(title, bid)
        product_url = f"{PAGE_BASE}/{bid}/"
        pages = {
            "lesen": (
                f"{title} kostenlos lesen",
                f"{title} von {author} – gemeinfreier Klassiker. Online lesen oder als "
                f"aufbereitete Ausgabe (Inhaltsverzeichnis + Register) entdecken.",
                f"Lesen Sie {title} von {author} – ein gemeinfreies Werk, neu gegliedert "
                f"und mit Register versehen.",
                f"Möchten Sie {title} lesen? Die öffentliche Leseprobe zeigt Inhaltsverzeichnis "
                f"und das erste Kapitel. Das vollständige eBook erhalten Sie nach dem Kauf.",
                "Leseprobe ansehen",
            ),
            "kaufen": (
                f"{title} als eBook kaufen",
                f"{title} von {author} als aufbereitetes eBook (Public Domain) – sicher per "
                f"Stripe bezahlen, sofort herunterladen.",
                f"Kaufen Sie {title} von {author} als gestyltes, offline lesbares eBook.",
                f"{title} ist gemeinfrei. Wir liefern eine sauber gegliederte, lesefreundliche "
                f"Ausgabe mit Inhaltsverzeichnis und Wortregister – kein Scanner-Export.",
                "Jetzt als eBook kaufen (3,99 €)",
            ),
            "begleiter": (
                f"{title} Lese-Begleiter",
                f"Zum {title} von {author}: ein Lese-Begleiter mit Zusammenfassung, Figuren, "
                f"Diskussionsfragen und 30-Tage-Leseplan.",
                f"Der {title}-Lese-Begleiter hilft beim Verstehen und Durchhalten.",
                f"Zum {title} gibt es einen Lese-Begleiter (KI-gestützte Analyse + gemeinfreier "
                f"Originaltext): Zusammenfassung, Figurenliste, Diskussionsfragen, Leseplan.",
                "Zum Lese-Begleiter",
            ),
        }
        for kind, (topic, desc, lead, body, cta) in pages.items():
            out_dir = os.path.join(SEO_ROOT, slug, kind)
            os.makedirs(out_dir, exist_ok=True)
            canonical = f"{PAGE_BASE}/seo/{slug}/{kind}/"
            html = _page(title, author, topic, desc, lead, body, cta, product_url, canonical)
            with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
            total += 1
    print(f"Generated {total} SEO pages under {SEO_ROOT} for {len(bundles)} books")
    return total


if __name__ == "__main__":
    build()
