"""Ticket F2 (Voll-Freifahrt): SEO at scale — Runde 2.
Mehr Städte + weitere Template-Varianten. Ziel: URL-Zahl weiter hoch.
"""
import os, json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_ROOT = os.path.join(REPO, "products", "templates")
SITE = os.path.join(REPO, "docs")
LINKS = json.load(open(os.path.join(REPO, "stripe_links.json"), encoding="utf-8"))

CITIES2 = ["Bochum", "Wuppertal", "Bielefeld", "Bonn", "Mannheim", "Gelsenkirchen",
           "Aachen", "Braunschweig", "Chemnitz", "Krefeld", "Halle", "Magdeburg2",
           "Kiel2", "Freiburg2", "Luebeck", "Erfurt2", "Rostock2", "Kassel",
           "Hagen", "Hamm", "Mulheim", "Solingen", "Herne", "Neuss"]
# dedupe
CITIES2 = [c for c in CITIES2 if not c.endswith("2")]

CITY_TPLS = {
    "finanz-tracker-dach": "Haushaltsbuch Vorlage {c}",
    "kleingewerbe-steuer": "Kleingewerbe Steuer {c}",
    "rechnungsvorlage-kleinunternehmer": "Rechnung schreiben {c}",
    "umzug-budget-planer": "Umzug Budget {c}",
    "nebenkostenabrechnung": "Nebenkostenabrechnung {c}",
    "steuerfreibetrag-optimierer": "Steuerfreibetrag {c}",
}

GUIDES2 = {
    "umzug-budget-planer": [
        ("umzug-kosten-sparen", "Umzug Kosten sparen", "5 Hebel, um beim Umzug Geld zu sparen."),
        ("umzug-zeitplan", "Umzug Zeitplan Vorlage", "8-Wochen-Plan fuer stressfreien Umzug."),
    ],
    "nebenkostenabrechnung": [
        ("nk-umlage-schluessel", "Umlageschluessel NK", "Wie Umlageschluessel korrekt berechnet wird."),
        ("nk-muster", "Nebenkosten Muster", "Muster einer rechtssicheren NK-Abrechnung."),
    ],
    "steuerfreibetrag-optimierer": [
        ("freibetrag-tagesgeld", "Freibetrag Tagesgeld", "Freibetrag auf Tagesgeld optimal setzen."),
        ("verlusttopf-nutzen", "Verlusttopf nutzen", "Verluste steuerlich mitnehmen."),
    ],
    "adhs-wochenplaner": [
        ("adhs-morgenroutine", "ADHS Morgenroutine", "Struktur fuer den Start in den Tag."),
        ("adhs-abendroutine", "ADHS Abendroutine", "Abschalten und morgen vorbereiten."),
    ],
    "agent-skills-bundle": [
        ("cursor-skills", "Cursor Skills nutzen", "SKILL.md in Cursor importieren."),
        ("claude-code-skills", "Claude Code Skills", "Skills in Claude Code einsetzen."),
    ],
    "finanz-tracker-dach": [
        ("budget-app-alternative", "Budget App Alternative", "Warum Sheets statt App."),
        ("ausgaben-kategorien", "Ausgaben Kategorien", "Die 10 wichtigsten Kategorien."),
    ],
    "kleingewerbe-steuer": [
        ("kleingewerbe-gruenden", "Kleingewerbe gruenden", "Schritt-fuer-Schritt Steuer-Check."),
        ("ust-frei-grenze", "USt-frei Grenze", "Wann §19 UStG greift."),
    ],
    "rechnungsvorlage-kleinunternehmer": [
        ("rechnung-muster-kleinunternehmer", "Rechnung Muster Kleinunternehmer", "Muster einer §19-Rechnung."),
        ("rechnung-richtig-stellen", "Rechnung richtig stellen", "Die 7 Pflichtangaben."),
    ],
}


def page(tid, slug, title, desc, spec):
    link = LINKS.get(f"tpl:{tid}", "")
    btn = (f'<a class="buy" href="{link}" style="display:inline-block;background:#2962ff;'
           f'color:#fff;padding:.6em 1.2em;border-radius:6px;text-decoration:none;'
           f'font-weight:bold">Jetzt {spec["price_eur"]:.2f} EUR kaufen</a>' if link else '<p>bald</p>')
    kw = ", ".join(spec.get("keywords", [])[:6])
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} – {spec['title']}</title>
<meta name="description" content="{desc} {spec['audience']}">
<meta name="keywords" content="{kw}"><meta name="robots" content="index,follow">
<link rel="canonical" href="https://translucentv1.github.io/new-business/t/{tid}/{slug}/">
</head><body style="font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6">
<h1>{title}</h1><p>{desc}</p>
<p><strong>{spec['title']}</strong> – {spec['audience']}</p>
{btn}<p><a href="/new-business/t/{tid}/">← Hauptseite</a> · <a href="/new-business/t/">Alle</a></p>
</body></html>"""


def build():
    n = 0
    for tid, tpl in CITY_TPLS.items():
        spec = json.load(open(os.path.join(TPL_ROOT, tid, "spec.json"), encoding="utf-8"))
        for c in CITIES2:
            slug = f"{tpl.split()[0].lower()}-{c.lower()}"
            d = os.path.join(SITE, "t", tid, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
                page(tid, slug, tpl.format(c=c), f"{tpl.format(c=c)} – Vorlage.", spec))
            n += 1
    for tid, guides in GUIDES2.items():
        spec = json.load(open(os.path.join(TPL_ROOT, tid, "spec.json"), encoding="utf-8"))
        for slug, title, desc in guides:
            d = os.path.join(SITE, "t", tid, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page(tid, slug, title, desc, spec))
            n += 1
    return n


if __name__ == "__main__":
    built = build()
    base = "https://translucentv1.github.io/new-business"
    urls = []
    for root, dirs, files in os.walk(SITE):
        if "index.html" in files:
            rel = os.path.relpath(root, SITE).replace(os.sep, "/")
            urls.append(f"{base}/" if rel == "." else f"{base}/{rel}/")
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f"  <url><loc>{u}</loc></url>")
    xml.append("</urlset>")
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml) + "\n")
    print(f"SCALE2 built: {built} | Sitemap total: {len(urls)}")
