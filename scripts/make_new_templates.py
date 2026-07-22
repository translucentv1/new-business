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
        "audience": "DE-Sparer, die Freibetraege (1000/2000 EUR) optimal nutzen",
        "sections": ["Freibetrag (Tagesgeld/Aktien)", "Sparerpauschbetrag-Check",
                     "Guenstigerpruefung", "Verlusttopf-Nutzung", "Jahresbilanz"],
        "categories": ["Freibetrag", "Tagesgeld", "Aktien", "Verlusttopf", "Guenstigerpruefung"],
        "keywords": ["sparerpauschbetrag ausnutzen", "steuerfreibetrag 1000 euro",
                     "freibetrag aktien", "steuern sparen vorlage"],
        "benefits": "Hole dir deine 1000/2000 EUR zurueck - automatischer Freibetrags-Check (Stand 2023, Sparer-Pauschbetrag lt. \u00a720 EStG).",
    },
}

for tid, spec in NEW.items():
    d = os.path.join(TPL, tid)
    os.makedirs(os.path.join(d, "deliverable"), exist_ok=True)
    json.dump(spec, open(os.path.join(d, "spec.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    cats = spec["categories"]
    # Reichhaltige CSV: 12 Monatsspalten + Jahressumme-Formel + Beispielwert-Hinweis
    header = ["Kategorie", "Jan", "Feb", "Mar", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez", "Summe"]
    lines = [",".join(header)]
    for i, c in enumerate(cats):
        row = [c] + ["0"] * 12
        r = i + 2  # 1-basierte Zeile inkl. Header
        row.append(f"=SUM(B{r}:M{r})")
        lines.append(",".join(row))
    # Summenzeile ueber alle Kategorien
    last = len(cats) + 1
    sumrow = ["GESAMT"] + [f"=SUM({col}2:{col}{last})" for col in
              ["B","C","D","E","F","G","H","I","J","K","L","M"]] + [f"=SUM(N2:N{last})"]
    lines.append(",".join(sumrow))
    open(os.path.join(d, "deliverable", "budget.csv"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    # Reichhaltige Anleitung mit Schritten, Sektionen, Tipps
    secs = spec.get("sections", [])
    md = []
    md.append(f"# {spec['title']}\n")
    md.append(f"> {spec['benefits']}\n")
    md.append(f"**Fuer wen:** {spec['audience']}\n")
    md.append("## Was du bekommst\n")
    md.append("- `budget.csv` – fertige Tabelle mit 12 Monatsspalten + automatischer Jahres- und Gesamtsumme (Google Sheets / Excel / LibreOffice).")
    md.append("- Diese Anleitung mit Schritt-fuer-Schritt-Nutzung und Praxis-Tipps.\n")
    md.append("## In 3 Minuten startklar\n")
    md.append("1. **Oeffnen:** `budget.csv` in Google Sheets (Datei > Importieren > Hochladen) oder direkt in Excel/LibreOffice.")
    md.append("2. **Eintragen:** Trage deine Betraege in die Monatsspalten (B–M) ein. Die Spalte **Summe** (N) rechnet je Kategorie automatisch, die Zeile **GESAMT** summiert alle Kategorien.")
    md.append("3. **Auswerten:** Du siehst sofort Monats- und Jahreswerte. Nichts manuell rechnen.\n")
    md.append("## Kategorien im Ueberblick\n")
    for c in cats:
        md.append(f"- **{c}**")
    md.append("")
    if secs:
        md.append("## Enthaltene Bereiche\n")
        for s in secs:
            md.append(f"- {s}")
        md.append("")
    md.append("## Praxis-Tipps\n")
    md.append("- Trage Werte **monatlich am selben Tag** ein (z. B. am 1.) – so wird es zur Routine.")
    md.append("- Nutze in Google Sheets *Ansicht > Fixieren > 1 Zeile*, damit die Kopfzeile beim Scrollen sichtbar bleibt.")
    md.append("- Kopiere das Blatt pro Jahr (Tab-Duplikat), um einen sauberen Jahresvergleich zu behalten.\n")
    md.append("---")
    md.append("*Digitales Produkt, keine Steuer-/Rechtsberatung. Angaben ohne Gewaehr.*")
    open(os.path.join(d, "deliverable", "ANLEITUNG.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("created", tid)

print("done:", len(NEW), "new templates")
