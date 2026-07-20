import os, json

REPO = r"C:\Users\phili\new-business"
TPL = os.path.join(REPO, "products", "templates")
LINKS = json.load(open(os.path.join(REPO, "stripe_links.json"), encoding="utf-8"))

# 3 neue DE-Nischen-Templates mit Kauf-Intention
NEW = {
    "umzug-budget-planer": {
        "title": "Umzug-Budget-Planer (DE)",
        "type": "sheets",
        "price_eur": 2.99,
        "lang": "de",
        "audience": "DE-Privathaushalte, die einen Umzug kostenkontrolliert planen wollen",
        "sections": ["Umzugskosten (Mietwagen, Hilfe, Material)", "Kaution & Nebenkosten",
                     "Ein-/Ausgaben-Tracking", "Sparpotenzial (DIY vs Dienstleister)",
                     "Budget-Bilanz"],
        "categories": ["Mietwagen", "Hilfe", "Material", "Kaution", "Nebenkosten", "Sparziel"],
        "keywords": ["umzug budget planer", "umzug kosten rechner", "umzug finanzierung",
                     "umzug kosten sparen", "umzugsbudget vorlage"],
        "benefits": "Plane deinen Umzug ohne Kosten-Uberraschung - alle Posten in einer Vorlage.",
    },
    "nebenkostenabrechnung": {
        "title": "Nebenkostenabrechnung Vorlage (Vermieter/Mieter)",
        "type": "sheets",
        "price_eur": 2.99,
        "lang": "de",
        "audience": "Mieter & Vermieter, die NK sauber erfassen wollen",
        "sections": ["Heizkosten", "Wasserkosten", "Grundsteuer/Versicherung",
                     "Sonstige Betriebskosten", "Umlageschluessel", "Abrechnung pro Partei"],
        "categories": ["Heizung", "Wasser", "Versicherung", "Grundsteuer", "Umlage"],
        "keywords": ["nebenkostenabrechnung vorlage", "nebenkosten abrechnung excel",
                     "betriebskostenabrechnung", "nk abrechnung mieter"],
        "benefits": "Nebenkosten rechtssicher erfassen - Umlageschluessel inklusive.",
    },
    "steuerfreibetrag-optimierer": {
        "title": "Steuerfreibetrag Optimierer (DE)",
        "type": "sheets",
        "price_eur": 2.99,
        "lang": "de",
        "audience": "DE-Sparer, die Freibetraege (801/1608 EUR) optimal nutzen",
        "sections": ["Freibetrag (Tagesgeld/Aktien)", "Sparerpauschbetrag-Check",
                     "Guenstigerpruefung", "Verlusttopf-Nutzung", "Jahresbilanz"],
        "categories": ["Freibetrag", "Tagesgeld", "Aktien", "Verlusttopf", "Guenstigerpruefung"],
        "keywords": ["sparerpauschbetrag ausnutzen", "steuerfreibetrag 801 euro",
                     "freibetrag aktien", "steuern sparen vorlage"],
        "benefits": "Hole dir deine 801/1608 EUR zurueck - automatischer Freibetrags-Check.",
    },
}

for tid, spec in NEW.items():
    d = os.path.join(TPL, tid)
    os.makedirs(os.path.join(d, "deliverable"), exist_ok=True)
    json.dump(spec, open(os.path.join(d, "spec.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    csv = "Kategorie,Betrag,Notiz\n" + "\n".join(f"{c},0," for c in spec["categories"])
    open(os.path.join(d, "deliverable", "budget.csv"), "w", encoding="utf-8").write(csv)
    md = f"# {spec['title']}\n\n{spec['benefits']}\n\nKategorien:\n" + "\n".join(f"- {c}" for c in spec["categories"])
    open(os.path.join(d, "deliverable", "ANLEITUNG.md"), "w", encoding="utf-8").write(md)
    print("created", tid)

print("done:", len(NEW), "new templates")
