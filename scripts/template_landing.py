"""TB-24: Template-Landingpages. Baut pro Template eine SEO-Seite unter
docs/t/<id>/index.html mit Stripe-Kaufbutton (aus stripe_links.json, Key
'tpl:<id>'). Unabhaengig von der Buch-Logik (KISS)."""
import os, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
TPL_ROOT = os.path.join(REPO, "products", "templates")
SITE = os.path.join(REPO, "docs")
LINKS = os.path.join(REPO, "stripe_links.json")


def _load_links():
    if os.path.exists(LINKS):
        try:
            return json.load(open(LINKS, encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def build_one(tid, spec, link):
    out_dir = os.path.join(SITE, "t", tid)
    os.makedirs(out_dir, exist_ok=True)
    title = spec["title"]
    price = spec["price_eur"]
    audience = spec["audience"]
    sections = "\n".join(f"<li>{s}</li>" for s in spec["sections"])
    keywords = ", ".join(spec.get("keywords", [])[:8])
    slug = tid
    # JSON-LD Product/Offer (rich results, price in EUR)
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": title,
        "description": f"{title}. {audience}",
        "offers": {
            "@type": "Offer",
            "priceCurrency": "EUR",
            "price": f"{price:.2f}",
            "availability": "https://schema.org/InStock",
            "url": link or ""
        }
    }, ensure_ascii=False)
    btn = (f'<a class="buy" href="{link}">Jetzt kaufen – {price:.2f} €</a>'
           if link else '<p class="soon">Demnächst verfügbar</p>')
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – digitales Template (DE) | sofort Download</title>
<meta name="description" content="{title}. {audience}. Sofort downloadbar als Markdown + CSV nach Kauf.">
<meta name="keywords" content="{keywords}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://translucentv1.github.io/new-business/t/{slug}/">
<script type="application/ld+json">{ld}</script>
<style>
  body{{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6;color:#1a1a1a}}
  h1{{font-size:1.9em}} h2{{font-size:1.3em;margin-top:1.4em}}
  ul{{padding-left:1.2em}} li{{margin:.4em 0}}
  .buy{{display:inline-block;background:#2962ff;color:#fff;padding:.7em 1.3em;border-radius:6px;text-decoration:none;font-weight:bold;margin:.8em 0}}
  .price{{font-size:1.1em;font-weight:bold}}
  .back a{{color:#2962ff}}
</style>
</head>
<body>
<h1>{title}</h1>
<p class="lead">{audience}</p>
<h2>Was ist enthalten</h2>
<ul>{sections}</ul>
<p class="price">Preis: {price:.2f} € · sofort downloadbar nach Kauf</p>
{btn}
<p class="back"><a href="/new-business/t/">← Alle Templates</a> · <a href="/new-business/">Alle Produkte</a></p>
</body>
</html>"""
    p = os.path.join(out_dir, "index.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    return p


def build_portal(entries):
    """ADR-na: Portal-Index docs/t/index.html — der Funnel-Einstieg.
    entries: list of (tid, spec, link). Zeigt alle Templates mit Kaufbutton."""
    rows = []
    for tid, spec, link in entries:
        title = spec.get("title", tid)
        price = spec.get("price_eur", "")
        price_s = f"&euro;{price:.2f}".replace(".", ",") if price else ""
        btn = (f'<a class="buy" href="{link}">Jetzt kaufen ({price_s})</a>'
               if link else '<span class="soon">bald erhaeltlich</span>')
        rows.append(
            f'    <li>\n'
            f'      <h3><a href="{tid}/">{title}</a></h3>\n'
            f'      <p>{btn}</p>\n'
            f'    </li>'
        )
    body = "\n".join(rows)
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Produktivitaets-Templates kaufen – Finanz-Tracker, Steuer, ADHS-Planer (DE)</title>
  <meta name="description" content="Digitale DE-Nischen-Templates kaufen: Finanz-Tracker DACH, Kleingewerbe-Steuer-Planer, ADHS-Wochenplaner, Rechnungsvorlage. Sofort-Download nach Kauf.">
  <meta name="robots" content="index,follow">
  <style>
    body{{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6;color:#1a1a1a}}
    h1{{font-size:1.9em}} h3{{font-size:1.2em;margin-bottom:.2em}}
    ul{{list-style:none;padding:0}} li{{margin:1.2em 0;padding:1em;background:#f4f7ff;border-left:4px solid #2962ff;border-radius:6px}}
    .buy{{display:inline-block;background:#2962ff;color:#fff;padding:.6em 1.1em;border-radius:6px;text-decoration:none;font-weight:bold}}
    .soon{{color:#888;font-style:italic}}
  </style>
</head>
<body>
  <h1>Produktivitaets-Templates (DE)</h1>
  <p>Sofort nutzbare Vorlagen fuer Finanzen, Steuern und Planung – als Markdown + CSV.
     Direkt nach dem Kauf herunterladbar.</p>
  <ul>
{body}
  </ul>
</body>
</html>
"""
    dest = os.path.join(SITE, "t", "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    return dest


def build_sitemap(entries):
    """ADR-na: docs/sitemap.xml — hilft Google, alle Template-LPs + Portal zu
    indexieren (Long-Tail-SEO). Vollautonom, keine Accounts."""
    base = "https://translucentv1.github.io/new-business"
    urls = [f"{base}/t/"]
    for tid, spec, link in entries:
        urls.append(f"{base}/t/{tid}/")
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f"  <url><loc>{u}</loc></url>")
    xml.append("</urlset>")
    dest = os.path.join(SITE, "sitemap.xml")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(xml) + "\n")
    return dest


def build_all():
    links = _load_links()
    out = []
    for d in sorted(glob.glob(os.path.join(TPL_ROOT, "*"))):
        tid = os.path.basename(d)
        spec_p = os.path.join(d, "spec.json")
        if not os.path.exists(spec_p):
            continue
        spec = json.load(open(spec_p, encoding="utf-8"))
        link = links.get(f"tpl:{tid}", "")
        out.append((tid, spec, link, build_one(tid, spec, link)))
    entries = [(tid, spec, link) for tid, spec, link, _ in out]
    portal = build_portal(entries)
    sm = build_sitemap(entries)
    print(f"Portal index -> {portal}")
    print(f"Sitemap     -> {sm}")
    return [e[3] for e in out]


if __name__ == "__main__":
    paths = build_all()
    for p in paths:
        print("built", p)
