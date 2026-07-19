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
    btn = (f'<a class="buy" href="{link}">Jetzt kaufen – {price:.2f} €</a>'
           if link else '<p class="soon">Demnächst verfügbar</p>')
    html = f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<title>{title} – digitales Template</title>
<meta name="description" content="{title}. {audience}. Sofort downloadbar.">
</head><body>
<h1>{title}</h1>
<p class="lead">{audience}</p>
<h2>Was ist enthalten</h2>
<ul>{sections}</ul>
<p class="price">Preis: {price:.2f} € · sofort downloadbar nach Kauf</p>
{btn}
<p class="back"><a href="/new-business/">Alle Produkte</a></p>
</body></html>"""
    p = os.path.join(out_dir, "index.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    return p


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
        out.append(build_one(tid, spec, link))
    return out


if __name__ == "__main__":
    paths = build_all()
    for p in paths:
        print("built", p)
