"""TB-22: Template-Produktgenerator (Notion .md + Google-Sheets .csv).

Erzeugt aus products/templates/<id>/spec.json echte, verkaufbare Dateien:
  - .csv mit Excel-Summenspalten (fuer Google Sheets / Excel)
  - .md (Notion-importfaehig: qua Header + Bullet-Sektionen)
Keine Platzhalter. Autonom, 0 Budget, kein Account.

NAHT (Seam): generate() gibt ein Dict zurueck; test_template_gen.py
assertet Struktur (hat alle Sektionen, keine leeren Werte, Formel-Zelle da).
"""
import os, json, csv

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
TPL_ROOT = os.path.join(REPO, "products", "templates")


def _ensure_specs():
    """Lege die 3 MVP-Produkt-Specs an, falls nicht vorhanden."""
    os.makedirs(TPL_ROOT, exist_ok=True)
    specs = {
        "finanz-tracker-dach": {
            "id": "finanz-tracker-dach",
            "title": "Finanz-Tracker DACH (Monatsbudget)",
            "type": "sheets",
            "price_eur": 4.99,
            "lang": "de",
            "audience": "DE-Sparer, die Ausgaben pro Monat im Blick behalten wollen",
            "sections": [
                "Einnahmen (Gehalt, Nebenjobs, sonstiges)",
                "Fixkosten (Miete, Versicherungen, Abos)",
                "Variable Kosten (Lebensmittel, Freizeit, Transport)",
                "Sparziele (Notgroschen, Urlaub, Anschaffungen)",
                "Automatische Monatsbilanz (Einnahmen - Ausgaben)",
            ],
            "categories": ["Gehalt", "Nebenjob", "Miete", "Versicherung", "Lebensmittel",
                           "Freizeit", "Transport", "Abo", "Sparziel"],
        },
        "kleingewerbe-steuer": {
            "id": "kleingewerbe-steuer",
            "title": "Kleingewerbe Steuer-Planner (§19 UStG)",
            "type": "sheets",
            "price_eur": 9.99,
            "lang": "de",
            "audience": "DE-Kleingewerbler mit Kleinunternehmerregelung",
            "sections": [
                "Einnahmen (Rechnungen, Bar, Online)",
                "Betriebsausgaben (Büro, Software, Werbung, Fahrten)",
                "Privatentnahmen",
                "Umsatzsteuer-Hinweis (§19 UStG: keine USt berechnen/anmelden)",
                "Gewinn = Einnahmen - Ausgaben (fuer EÜR / Steuer)",
            ],
            "categories": ["Rechnung", "Bar", "Online", "Büro", "Software", "Werbung",
                           "Fahrten", "Privatentnahme"],
        },
        "adhs-wochenplaner": {
            "id": "adhs-wochenplaner",
            "title": "ADHS-Wochenplaner (Fokus & Struktur)",
            "type": "notion",
            "price_eur": 6.99,
            "lang": "de",
            "audience": "Menschen mit ADHS / exec. Dysfunction, die Struktur wollen",
            "sections": [
                "Wochen-Fokus (1 Kernziel)",
                "Brain-Dump (alles, was im Kopf schwirrt)",
                "Dopamin-Tasks (kleine Siege)",
                "Mo-So Tagesplan (max 3 Prios/Tag)",
                "Rejection-Sensitivity-Notiz",
                "Wochendebrief (was lief, was nicht)",
            ],
            "categories": [],
        },
        "rechnungsvorlage-kleinunternehmer": {
            "id": "rechnungsvorlage-kleinunternehmer",
            "title": "Rechnungsvorlage für Kleinunternehmer (§19 UStG)",
            "type": "sheets",
            "price_eur": 5.99,
            "lang": "de",
            "audience": "DE-Kleingewerbler & Freelancer mit Kleinunternehmerregelung, die rechtskonforme Rechnungen schreiben wollen",
            "sections": [
                "Absender & Empfänger (Briefkopf)",
                "Rechnungsnummer & Datum",
                "Leistungsbeschreibung (Positionen)",
                "Brutto-Beträge je Position",
                "Hinweis §19 UStG: 'Stellt frei von Umsatzsteuer gem. §19 UStG'",
                "Zahlungsziel & Bankdaten",
            ],
            "categories": ["Leistung", "Betrag", "Rechnungsnummer", "Datum", "Zahlungsziel"],
        },
    }
    for sid, spec in specs.items():
        p = os.path.join(TPL_ROOT, sid)
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, "spec.json"), "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
    return specs


def generate_sheets(spec, out_dir):
    """Erzeugt budget.csv mit 12 Monatsspalten + Summen-Formeln + reiche Anleitung."""
    os.makedirs(out_dir, exist_ok=True)
    cats = spec["categories"]
    header = ["Kategorie", "Jan", "Feb", "Mar", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez", "Summe"]
    rows = [header]
    for i, c in enumerate(cats):
        r = i + 2
        rows.append([c] + [0] * 12 + [f"=SUM(B{r}:M{r})"])
    last = len(cats) + 1
    rows.append(["GESAMT"] + [f"=SUM({col}2:{col}{last})" for col in
                 ["B","C","D","E","F","G","H","I","J","K","L","M"]] + [f"=SUM(N2:N{last})"])
    path = os.path.join(out_dir, "budget.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)
    # Reiche Begleit-Anleitung
    with open(os.path.join(out_dir, "ANLEITUNG.md"), "w", encoding="utf-8") as f:
        f.write(f"# {spec['title']}\n\n")
        f.write(f"**Fuer wen:** {spec['audience']}\n\n")
        f.write("## Was du bekommst\n\n")
        f.write("- `budget.csv` – Tabelle mit 12 Monatsspalten, automatischer Zeilen- (Summe) "
                "und Gesamtsumme (GESAMT) fuer Google Sheets / Excel / LibreOffice.\n")
        f.write("- Diese Anleitung mit Schritt-fuer-Schritt-Nutzung.\n\n")
        f.write("## In 3 Minuten startklar\n\n")
        f.write("1. **Oeffnen:** `budget.csv` in Google Sheets (Datei > Importieren > Hochladen) "
                "oder direkt in Excel/LibreOffice.\n")
        f.write("2. **Eintragen:** Betraege in die Monatsspalten (B–M). Die Spalte **Summe** (N) "
                "rechnet je Kategorie automatisch, die Zeile **GESAMT** summiert alle Kategorien.\n")
        f.write("3. **Auswerten:** Monats- und Jahreswerte sofort sichtbar – nichts manuell rechnen.\n\n")
        f.write("## Enthaltene Bereiche\n\n")
        for sec in spec["sections"]:
            f.write(f"- {sec}\n")
        f.write("\n## Praxis-Tipps\n\n")
        f.write("- Werte **monatlich am selben Tag** eintragen – so wird es Routine.\n")
        f.write("- In Google Sheets *Ansicht > Fixieren > 1 Zeile* fuer eine feste Kopfzeile.\n")
        f.write("- Pro Jahr das Blatt duplizieren (Tab-Kopie) fuer einen sauberen Jahresvergleich.\n\n")
        f.write("---\n*Digitales Produkt, keine Steuer-/Rechtsberatung. Angaben ohne Gewaehr.*\n")
    return path


def generate_notion(spec, out_dir):
    """Erzeugt planner.md (Notion-importfaehig) mit Anleitung + strukturierten Sektionen."""
    os.makedirs(out_dir, exist_ok=True)
    lines = [f"# {spec['title']}\n"]
    lines.append(f"> Zielgruppe: {spec['audience']}\n")
    lines.append("\n## So nutzt du diese Vorlage\n")
    lines.append("1. In Notion: *Import > Markdown* und diese Datei hochladen (oder Inhalt in eine neue Seite kopieren).\n")
    lines.append("2. Jede Sektion unten ist eine Checkliste – hake ab oder ergaenze eigene Zeilen.\n")
    lines.append("3. Dupliziere die Seite woechentlich fuer eine fortlaufende Historie.\n")
    for sec in spec["sections"]:
        lines.append(f"\n## {sec}\n")
        lines.append("- [ ] \n")
        lines.append("- [ ] \n")
        lines.append("- [ ] \n")
    lines.append("\n---\n*Digitales Produkt. Persoenliche Nutzung.*\n")
    path = os.path.join(out_dir, "planner.md")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


def generate(spec_id=None):
    specs = _ensure_specs()
    out = {}
    for sid, spec in specs.items():
        if spec_id and sid != spec_id:
            continue
        d = os.path.join(TPL_ROOT, sid, "deliverable")
        if spec["type"] == "sheets":
            out[sid] = generate_sheets(spec, d)
        else:
            out[sid] = generate_notion(spec, d)
    return out


if __name__ == "__main__":
    res = generate()
    for k, v in res.items():
        print(f"generated {k}: {v}")
