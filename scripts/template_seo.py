"""Ticket B (autonomous-business-design loop): Template SEO-Masse.
Pro Template mehrere Long-Tail-SEO-Seiten (verschiedene Suchintentionen),
jede mit DIREKTEM Stripe-CTA (nicht nur Root-Link). Rekursive Sitemap.
Einzig autonomer Traffic-Hebel laut Charta (kein Social-Posting).
"""
import os, json, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_ROOT = os.path.join(REPO, "products", "templates")
SITE = os.path.join(REPO, "docs")
LINKS = json.load(open(os.path.join(REPO, "stripe_links.json"), encoding="utf-8"))

# Long-Tail-Intentionen pro Template (realistische DE-Suchen)
INTENTS = {
    "finanz-tracker-dach": [
        ("haushaltsbuch-vorlage", "Haushaltsbuch Vorlage (Excel/Sheets)",
         "Einnahmen und Ausgaben monatlich erfassen – kostenlose Vorlage-Struktur für DE-Sparer."),
        ("budget-planer", "Budget-Planer Monatsbudget",
         "Planbares Monatsbudget statt Schätzung – fixe & variable Kosten, Sparziele, Bilanz."),
    ],
    "kleingewerbe-steuer": [
        ("einnahmenueberschussrechnung", "Einnahmenüberschussrechnung Vorlage",
         "EÜR-Hilfe für Kleingewerbe – Betriebsausgaben sauber erfassen, §19 UStG konform."),
        ("steuer-selbst-machen", "Kleingewerbe Steuer selbst machen",
         "Ohne teuren Steuerberater: Vorlage für die steuerliche Erfassung deines Kleingewerbes."),
    ],
    "adhs-wochenplaner": [
        ("wochenplan-adhs", "Wochenplan für ADHS",
         "Struktur für die Woche ohne Überforderung – Fokus, Brain-Dump, Dopamin-Tasks."),
        ("adhs-selbstorganisation", "ADHS Selbstorganisation Vorlage",
         "Flexibler Planer, nicht starr – für Menschen mit exekutiver Dysfunktion."),
    ],
    "rechnungsvorlage-kleinunternehmer": [
        ("rechnung-schreiben", "Rechnung schreiben Vorlage",
         "Rechnung in 2 Min statt Word-Suche – rechtssicher nach §19 UStG."),
        ("kleinunternehmer-rechnung", "Kleinunternehmer Rechnung ohne USt",
         "Rechnungsvorlage für Kleinunternehmer – korrekte §19-UStG-Rechnung, keine USt ausgewiesen."),
    ],
    "agent-skills-bundle": [
        ("claude-skill-kaufen", "Claude Skill kaufen",
         "7 fertige Dev-Skills (Code-Review, Debug, Tests, Git) – sofort einsatzbereit."),
        ("dev-skills-bundle", "KI Agent Skills Bundle",
         "Vorgefertigte Agent-Skills für Claude/ChatGPT – kein Prompt-Engineering nötig."),
    ],
}


def build_seo_pages():
    out = []
    for tid, intents in INTENTS.items():
        link = LINKS.get(f"tpl:{tid}", "")
        spec = json.load(open(os.path.join(TPL_ROOT, tid, "spec.json"), encoding="utf-8"))
        for slug, title, desc in intents:
            d = os.path.join(SITE, "t", tid, slug)
            os.makedirs(d, exist_ok=True)
            btn = (f'<a class="buy" href="{link}">Jetzt {spec["price_eur"]:.2f} € kaufen</a>'
                   if link else '<p class="soon">bald</p>')
            kw = ", ".join(spec.get("keywords", [])[:6])
            html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – {spec['title']}</title>
<meta name="description" content="{desc} {spec['audience']}">
<meta name="keywords" content="{kw}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://translucentv1.github.io/new-business/t/{tid}/{slug}/">
</head>
<body style="font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.6">
<h1>{title}</h1>
<p>{desc}</p>
<p><strong>{spec['title']}</strong> – {spec['audience']}</p>
<p>Enthalten: {'; '.join(spec.get('sections', [])[:3])} …</p>
{btn}
<p><a href="/new-business/t/{tid}/">← Zur Hauptseite</a> · <a href="/new-business/t/">Alle Templates</a></p>
</body>
</html>"""
            p = os.path.join(d, "index.html")
            open(p, "w", encoding="utf-8").write(html)
            out.append((tid, slug, link))
    return out


def rebuild_sitemap_recursive():
    """DELEGAT an landingpage_gen.rebuild_sitemap() (Single Source of Truth).
    Bisher os.walk(SITE) -> schrieb AUCH docs/dl/ in die Sitemap (/dl/-Leak,
    widerspricht ADR-0013 Download-Gate). Jetzt vollstaendig + sauber."""
    import landingpage_gen
    dest = landingpage_gen.rebuild_sitemap()
    return open(dest, encoding="utf-8").read().count("<loc>")


if __name__ == "__main__":
    pages = build_seo_pages()
    n = rebuild_sitemap_recursive()
    print(f"SEO subpages built: {len(pages)}")
    print(f"Sitemap URLs (recursive): {n}")
    for tid, slug, link in pages:
        print(f"  t/{tid}/{slug} -> {('CTA' if link else 'NO-LINK')}")
