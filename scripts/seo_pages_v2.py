"""SEO-Massen-Generator v2 (autonome Nachtschicht, 2026-07-19).

Erzeugt pro Buch MEHRERE thematische Long-Tail-Landingpages mit ECHTEM
Inhalt aus study_guide.json (via companion_llm gefuellt) + echten Kapiteltiteln
aus dem Corpus. Jede Seite verlinkt auf die Kaufseite (/<id>/) -> interne
Verlinkung. Das ist der einzige autonome Traffic-Hebel (Charta: kein Social-Posting).

Seiten pro Buch (Long-Tail-Intent):
  - zusammenfassung   "<Titel> Zusammenfassung & Inhalt"
  - figuren           "<Titel> Figuren & Charaktere"
  - analyse           "<Titel> Analyse & Interpretationsfragen"
  - leseplan          "<Titel> 30-Tage-Leseplan"
  - kapitel           "<Titel> Kapiteluebersicht (alle Kapitel)"
  - kaufen            "<Titel> als eBook kaufen"
  - begleiter         "<Titel> Lese-Begleiter"
  - lesen             "<Titel> kostenlos lesen"

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
        gj = os.path.join(d, "product", "study_guide.json")
        if os.path.exists(mj) and os.path.exists(gj):
            meta = json.load(open(mj, encoding="utf-8"))
            guide = json.load(open(gj, encoding="utf-8"))
            out.append((bid, meta, guide))
    return out


def _chapter_list(guide, limit=61):
    ch = guide.get("chapters", [])
    items = []
    for c in ch[:limit]:
        t = c.get("title", "")
        if t:
            items.append(_esc(t))
    return items


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


def _render(title, author, topic, desc, lead, body, cta, product_url, canonical):
    return _PAGE.format(
        lang=LANG, title=_esc(title), author=_esc(author), topic=_esc(topic),
        desc=_esc(desc), lead=_esc(lead), body=body, cta=_esc(cta),
        product_url=product_url, canonical=canonical, base=PAGE_BASE,
    )


def build():
    bundles = _bundles()
    total = 0
    for bid, meta, guide in bundles:
        title = meta["title"]
        author = meta.get("author", "Unbekannt")
        slug = _slugify(title, bid)
        product_url = f"{PAGE_BASE}/{bid}/"
        summary = guide.get("summary", "")
        characters = guide.get("characters", [])
        questions = guide.get("questions", [])
        plan = guide.get("reading_plan", [])
        chapters = _chapter_list(guide)
        char_html = "".join(f"<li>{_esc(c)}</li>" for c in characters[:12]) or "<li>siehe Lese-Begleiter</li>"
        q_html = "".join(f"<li>{_esc(q)}</li>" for q in questions[:6]) or "<li>siehe Lese-Begleiter</li>"
        plan_html = "".join(f"<li>{_esc(p)}</li>" for p in plan[:10]) or "<li>siehe Lese-Begleiter</li>"
        chap_html = "".join(f"<li>{c}</li>" for c in chapters) or "<li>siehe Lese-Begleiter</li>"

        pages = {
            "zusammenfassung": (
                f"{title} Zusammenfassung & Inhalt",
                f"Kurze Zusammenfassung von {title} ({author}) – Gesamtschau, Figuren und Kernkonflikt auf einen Blick.",
                f"Eine kompakte Zusammenfassung von {title} hilft beim Einstieg und bei der Pruefungsvorbereitung.",
                f"<p>{_esc(summary)}</p><h2>Figuren</h2><ul class='toc'>{char_html}</ul>"
                f"<h2>Kernfragen</h2><ul class='toc'>{q_html}</ul>",
                "Zum vollstaendigen Lese-Begleiter",
            ),
            "figuren": (
                f"{title} Figuren & Charaktere",
                f"Alle wichtigen Figuren aus {title} von {author} – Rolle, Beziehungen, Entwicklung.",
                f"Die Figuren tragen {title}. Hier die zentralen Charaktere im Ueberblick.",
                f"<ul class='toc'>{char_html}</ul><p>Der Lese-Begleiter liefert je Figur Rolle, Motiv und Entwicklungsbogen.</p>",
                "Lese-Begleiter mit Figurenanalyse",
            ),
            "analyse": (
                f"{title} Analyse & Interpretationsfragen",
                f"Diskussionsfragen und Analyseschwerpunkte zu {title} ({author}) – zum Selbststudium oder Unterricht.",
                f"Mit diesen Fragen erschliesst sich {title} ueber die Oberflaechenhandlung hinaus.",
                f"<h2>Diskussionsfragen</h2><ul class='toc'>{q_html}</ul>"
                f"<h2>Zusammenfassung</h2><p>{_esc(summary)}</p>",
                "Lese-Begleiter mit Fragenkatalog",
            ),
            "leseplan": (
                f"{title} 30-Tage-Leseplan",
                f"Ein realistischer 30-Tage-Plan, um {title} von {author} zu lesen – etwa ein Kapitel pro Tag.",
                f"Durchhalten leicht gemacht: {title} in 30 Tagen.",
                f"<h2>Dein Leseplan</h2><ul class='toc'>{plan_html}</ul>"
                f"<p>Der Lese-Begleiter enthaelt den vollen Plan plus Zusammenfassungen je Abschnitt.</p>",
                "Lese-Begleiter mit 30-Tage-Plan",
            ),
            "kapitel": (
                f"{title} Kapiteluebersicht",
                f"Alle Kapitel von {title} ({author}) im Ueberblick – Gliederung zum Nachschlagen.",
                f"Die vollstaendige Kapitelstruktur von {title}.",
                f"<h2>Kapitelverzeichnis</h2><ul class='toc'>{chap_html}</ul>",
                "Zum Lese-Begleiter",
            ),
            "kaufen": (
                f"{title} als eBook kaufen",
                f"{title} von {author} als aufbereitetes eBook (Public Domain) – sicher per Stripe, sofort Download.",
                f"Kaufen Sie {title} als sauber gegliederte, lesefreundliche Ausgabe mit Register.",
                f"<p>{_esc(summary)}</p><p>Im Lieferumfang: Zusammenfassung, Figurenliste, "
                f"Diskussionsfragen, 30-Tage-Leseplan + bereinigter Originaltext.</p>",
                "Jetzt als eBook kaufen (3,99 €)",
            ),
            "begleiter": (
                f"{title} Lese-Begleiter",
                f"Zum {title} von {author}: Lese-Begleiter mit Zusammenfassung, Figuren, Fragen, Leseplan.",
                f"Der {title}-Lese-Begleiter hilft beim Verstehen und Durchhalten.",
                f"<p>{_esc(summary)}</p><ul class='toc'>{char_html}</ul>",
                "Zum Lese-Begleiter",
            ),
            "lesen": (
                f"{title} kostenlos lesen",
                f"{title} von {author} – gemeinfreier Klassiker. Online lesen oder als eBook entdecken.",
                f"Lesen Sie {title} – ein gemeinfreies Werk, neu gegliedert.",
                f"<p>{_esc(summary)}</p><p>Das vollstaendige eBook mit Begleiter erhalten Sie nach dem Kauf.</p>",
                "Leseprobe / Begleiter ansehen",
            ),
        }
        for kind, (topic, desc, lead, body, cta) in pages.items():
            out_dir = os.path.join(SEO_ROOT, slug, kind)
            os.makedirs(out_dir, exist_ok=True)
            canonical = f"{PAGE_BASE}/seo/{slug}/{kind}/"
            html = _render(title, author, topic, desc, lead, body, cta, product_url, canonical)
            with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
            total += 1
    print(f"Generated {total} SEO pages under {SEO_ROOT} for {len(bundles)} books")
    return total


if __name__ == "__main__":
    build()
