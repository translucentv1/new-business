"""SEO Scale 3: ALLE 8 Templates auf volles Stadt-Set (~50) + neue Intent-Guides.
Konsolidiert die vorherigen seo_scale + seo_scale2 Läufe. Single source: CITIES_ALL.
Delegiert Sitemap-Rebuild an landingpage_gen.rebuild_sitemap() (SSOT).
"""
import os, json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_ROOT = os.path.join(REPO, "products", "templates")
SITE = os.path.join(REPO, "docs")
LINKS = json.load(open(os.path.join(REPO, "stripe_links.json"), encoding="utf-8"))

# Alle ~50 deutschen Großstädte (für flächendeckende lokale SEO)
CITIES_ALL = [
    "Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart",
    "Düsseldorf", "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden",
    "Hannover", "Nürnberg", "Duisburg", "Bochum", "Wuppertal", "Bielefeld",
    "Bonn", "Mannheim", "Karlsruhe", "Augsburg", "Wiesbaden", "Mainz",
    "Münster", "Gelsenkirchen", "Aachen", "Braunschweig", "Chemnitz",
    "Krefeld", "Halle", "Kiel", "Freiburg", "Lübeck", "Erfurt", "Rostock",
    "Kassel", "Magdeburg", "Potsdam", "Saarbrücken", "Hagen", "Hamm",
    "Mülheim", "Solingen", "Herne", "Neuss", "Osnabrück", "Heidelberg",
    "Darmstadt", "Regensburg"
]

# Keyword-Template für Stadt-Seiten (je Template ein passender Satz)
CITY_TPLS = {
    "adhs-wochenplaner":       "ADHS Wochenplaner {c}",
    "agent-skills-bundle":      "KI Agent Skills {c}",  # WENIGER sinnvoll aber für URL-Masse
    "finanz-tracker-dach":      "Haushaltsbuch Vorlage {c}",
    "kleingewerbe-steuer":      "Kleingewerbe Steuer {c}",
    "rechnungsvorlage-kleinunternehmer": "Rechnung schreiben {c}",
    "nebenkostenabrechnung":    "Nebenkostenabrechnung {c}",
    "steuerfreibetrag-optimierer": "Steuerfreibetrag {c}",
    "umzug-budget-planer":      "Umzug Budget {c}",
}

# Neue Intent-Guides (mehr als die 2-4 pro Template in seo_scale2)
GUIDES_ALL = {
    "adhs-wochenplaner": [
        ("adhs-morgenroutine", "ADHS Morgenroutine", "Struktur für den Start in den Tag."),
        ("adhs-abendroutine", "ADHS Abendroutine", "Abschalten und morgen vorbereiten."),
        ("adhs-selbstorganisation", "ADHS Selbstorganisation Vorlage", "Flexibler Planer für exekutive Dysfunktion."),
        ("adhs-fokus-aufgaben", "ADHS Fokus Aufgaben", "Max 3 Prioritäten pro Tag setzen."),
        ("adhs-dopamin-tasks", "ADHS Dopamin Tasks", "Kleine Siege für Motivation."),
    ],
    "agent-skills-bundle": [
        ("claude-code-skills", "Claude Code Skills", "Skills in Claude Code einsetzen."),
        ("cursor-skills", "Cursor Skills nutzen", "SKILL.md in Cursor importieren."),
        ("dev-skills-bundle", "KI Agent Skills Bundle", "7 fertige Dev-Skills sofort nutzbar."),
        ("dev-skills-spart-zeit", "Agent Skills sparen Zeit", "Kein Prompt-Engineering nötig."),
        ("claude-skills-fuer-anfaenger", "Claude Skills für Anfänger", "Einfach loslegen mit KI-Agenten."),
    ],
    "finanz-tracker-dach": [
        ("budget-app-alternative", "Budget App Alternative", "Warum Sheets statt App."),
        ("ausgaben-kategorien", "Ausgaben Kategorien", "Die 10 wichtigsten Kategorien."),
        ("haushaltsbuch-vorlage", "Haushaltsbuch Vorlage (Excel/Sheets)", "Einnahmen/Ausgaben monatlich erfassen."),
        ("budget-planer", "Budget-Planer Monatsbudget", "Fixe & variable Kosten, Sparziele."),
        ("erste-schritte-sparen", "Erste Schritte Sparen", "Mit 50€ Sparrate starten."),
        ("budget-im-blick", "Budget im Blick behalten", "Monatsbilanz automatisch."),
    ],
    "kleingewerbe-steuer": [
        ("kleingewerbe-gruenden", "Kleingewerbe gründen", "Schritt-für-Schritt Steuer-Check."),
        ("ust-frei-grenze", "USt-frei Grenze", "Wann §19 UStG greift."),
        ("einnahmenueberschussrechnung", "Einnahmenüberschussrechnung Vorlage", "EÜR-Hilfe für Kleingewerbe."),
        ("steuer-selbst-machen", "Kleingewerbe Steuer selbst machen", "Ohne teuren Steuerberater."),
        ("euer-richtig", "EÜR richtig ausfüllen", "Betriebsausgaben sauber erfassen."),
        ("steuerliche-erfassung", "Steuerliche Erfassung Kleingewerbe", "Alle relevanten Posten."),
    ],
    "rechnungsvorlage-kleinunternehmer": [
        ("rechnung-schreiben", "Rechnung schreiben Vorlage", "Rechnung in 2 Min statt Word-Suche."),
        ("kleinunternehmer-rechnung", "Kleinunternehmer Rechnung ohne USt", "Korrekte §19-UStG-Rechnung."),
        ("rechnung-richtig-stellen", "Rechnung richtig stellen", "Die 7 Pflichtangaben."),
        ("rechnung-muster-kleinunternehmer", "Rechnung Muster Kleinunternehmer", "Muster einer §19-Rechnung."),
        ("rechnung-vorlage-word", "Rechnungsvorlage Word Alternative", "Sheets statt Word."),
        ("rechnung-mit-19-ust", "Rechnung mit 19% USt Vorlage", "Für Regelbesteuerte."),
    ],
    "nebenkostenabrechnung": [
        ("nk-umlage-schluessel", "Umlageschlüssel NK", "Korrekte Berechnung."),
        ("nk-muster", "Nebenkosten Muster", "Muster einer rechtssicheren NK-Abrechnung."),
        ("nk-heizkosten-berechnen", "Heizkosten berechnen NK", "Heizkostenverteiler korrekt anwenden."),
        ("nk-wasserkosten-umlage", "Wasserkosten Umlage", "Kalt-/Warmwasser korrekt umlegen."),
    ],
    "steuerfreibetrag-optimierer": [
        ("freibetrag-tagesgeld", "Freibetrag Tagesgeld", "801€ optimal setzen."),
        ("verlusttopf-nutzen", "Verlusttopf nutzen", "Verluste steuerlich mitnehmen."),
        ("sparerpauschbetrag-ausnutzen", "Sparerpauschbetrag ausnutzen", "Kein Cent verschenken."),
        ("freibetrag-aktien", "Freibetrag Aktien", "Aktiengewinne steuerfrei halten."),
    ],
    "umzug-budget-planer": [
        ("umzug-kosten-sparen", "Umzug Kosten sparen", "5 Hebel, um Geld zu sparen."),
        ("umzug-zeitplan", "Umzug Zeitplan Vorlage", "8-Wochen-Plan für stressfreien Umzug."),
        ("umzug-kaution-rechner", "Umzug Kaution Rechner", "Kaution & Nebenkosten kalkulieren."),
        ("umzug-diy-vs-dienstleister", "Umzug DIY vs Dienstleister", "Was lohnt sich wann."),
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
        spec_path = os.path.join(TPL_ROOT, tid, "spec.json")
        if not os.path.exists(spec_path):
            continue
        spec = json.load(open(spec_path, encoding="utf-8"))
        for c in CITIES_ALL:
            slug = f"{tpl.split()[0].lower()}-{c.lower()}"
            # Umlaute/ß in slug filtern
            slug = slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
            d = os.path.join(SITE, "t", tid, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
                page(tid, slug, tpl.format(c=c), f"{tpl.format(c=c)} – Vorlage.", spec))
            n += 1

    for tid, guides in GUIDES_ALL.items():
        spec_path = os.path.join(TPL_ROOT, tid, "spec.json")
        if not os.path.exists(spec_path):
            continue
        spec = json.load(open(spec_path, encoding="utf-8"))
        for slug, title, desc in guides:
            d = os.path.join(SITE, "t", tid, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
                page(tid, slug, title, desc, spec))
            n += 1
    return n


if __name__ == "__main__":
    built = build()
    # Sitemap SSOT: landingpage_gen.rebuild_sitemap()
    import landingpage_gen
    dest = landingpage_gen.rebuild_sitemap()
    url_count = open(dest, encoding="utf-8").read().count("<loc>")
    print(f"SCALE3 built: {built} | Sitemap total URLs: {url_count}")