"""Ticket F (Voll-Freifahrt): SEO at scale.
Erzeugt pro Geld-Template Stadt- + Varianten-Seiten (long-tail, low competition),
jede mit DIREKTEM Stripe-CTA. Ziel: tausende indexierbare URLs, die bis Sonntag
ranken koennen. Autonom, kostenlos, legal. Rekursive Sitemap danach.
"""
import os, json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_ROOT = os.path.join(REPO, "products", "templates")
SITE = os.path.join(REPO, "docs")
LINKS = json.load(open(os.path.join(REPO, "stripe_links.json"), encoding="utf-8"))

CITIES = ["Berlin", "Hamburg", "Muenchen", "Koeln", "Frankfurt", "Stuttgart",
          "Duesseldorf", "Leipzig", "Dresden", "Hannover", "Bremen", "Nuernberg",
          "Dortmund", "Essen", "Karlsruhe", "Freiburg", "Kiel", "Mainz", "Saarbruecken",
          "Erfurt", "Rostock", "Potsdam", "Magdeburg", "Wiesbaden", "Augsburg"]

# welche Templates bekommen Stadt-Seiten (hohe lokale Suchintention)
CITY_TPLS = {
    "finanz-tracker-dach": "Haushaltsbuch Vorlage {c}",
    "kleingewerbe-steuer": "Kleingewerbe Steuer {c}",
    "rechnungsvorlage-kleinunternehmer": "Rechnung schreiben {c}",
}

# generische Varianten/Guides pro Template
GUIDES = {
    "finanz-tracker-dach": [
        ("budget-im-blick", "Monatsbudget behalten", "Wie du Ausgaben ohne Excel-Stress im Blick behaeltst."),
        ("erste-schritte-sparen", "Erste Schritte Sparen", "Vom 0 auf Sparplan: fixe Kosten, Sparziele, Bilanz."),
    ],
    "kleingewerbe-steuer": [
        ("steuerliche-erfassung", "Steuerliche Erfassung Kleingewerbe", "Was das Finanzamt bei der steuerlichen Erfassung will – vorbereitet."),
        ("euer-richtig", "EÜR richtig machen", "Einnahmenüberschussrechnung korrekt fuer §19 UStG."),
    ],
    "adhs-wochenplaner": [
        ("struktur-fuer-den-tag", "Struktur fuer den Tag ADHS", "Tagesplan statt Überforderung – flexibel, nicht starr."),
        ("fokus-aufgaben", "Fokus-Aufgaben planen", "Die 3 wichtigsten Tasks des Tages – mit Dopamin-Belohnung."),
    ],
    "rechnungsvorlage-kleinunternehmer": [
        ("rechnung-mit-19-ust", "Wann 19% USt?", "Kleinunternehmer-Grenze erklaert – wann du USt ausweisen musst."),
        ("rechnung-vorlage-word", "Rechnung Vorlage (Word-frei)", "Ohne Word: rechtssichere Rechnung als Markdown/CSV."),
    ],
    "agent-skills-bundle": [
        ("claude-skills-fuer-anfaenger", "Claude Skills fuer Anfaenger", "Wie du SKILL.md in Cursor/Claude Code nutzt."),
        ("dev-skills-spart-zeit", "Dev-Skills spart Zeit", "Code-Review, Debug, Tests als vorgefertigte Skills."),
    ],
}


def page(tid, slug, title, desc, spec):
    link = LINKS.get(f"tpl:{tid}", "")
    btn = (f'<a class="buy" href="{link}" style="display:inline-block;background:#2962ff;'
           f'color:#fff;padding:.6em 1.2em;border-radius:6px;text-decoration:none;'
           f'font-weight:bold">Jetzt {spec["price_eur"]:.2f} € kaufen</a>'
           if link else '<p class="soon">bald</p>')
    kw = ", ".join(spec.get("keywords", [])[:6])
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – {spec['title']}</title>
<meta name="description" content="{desc} {spec['audience']}">
<meta name="keywords" content="{kw}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://translucentv1.github.io/new-business/t/{tid}/{slug}/">
</head><body style="font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6">
<h1>{title}</h1>
<p>{desc}</p>
<p><strong>{spec['title']}</strong> – {spec['audience']}</p>
<p>Enthalten: {'; '.join(spec.get('sections', [])[:3])} …</p>
{btn}
<p><a href="/new-business/t/{tid}/">← Zur Hauptseite</a> · <a href="/new-business/t/">Alle Templates</a></p>
</body></html>"""


def build():
    n = 0
    for tid, tpl in CITY_TPLS.items():
        spec = json.load(open(os.path.join(TPL_ROOT, tid, "spec.json"), encoding="utf-8"))
        for c in CITIES:
            slug = f"{tpl.split()[0].lower()}-{c.lower()}"
            title = tpl.format(c=c)
            desc = f"{title} – sofort nutzbare Vorlage fuer {spec['audience']}."
            d = os.path.join(SITE, "t", tid, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(tid, slug, title, desc, spec))
            n += 1
    for tid, guides in GUIDES.items():
        spec = json.load(open(os.path.join(TPL_ROOT, tid, "spec.json"), encoding="utf-8"))
        for slug, title, desc in guides:
            d = os.path.join(SITE, "t", tid, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(tid, slug, title, desc, spec))
            n += 1
    return n


if __name__ == "__main__":
    built = build()
    # recursive sitemap — DELEGAT an landingpage_gen.rebuild_sitemap()
    # (Single Source of Truth): vollstaendig (root+PD+/seo/+/t/) OHNE /dl/-Leak.
    import landingpage_gen
    dest = landingpage_gen.rebuild_sitemap()
    n = open(dest, encoding="utf-8").read().count("<loc>")
    print(f"SCALE pages built: {built}")
    print(f"Sitemap URLs total: {n}")
