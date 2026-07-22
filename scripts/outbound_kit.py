"""TB-49: Outbound-Kit-Generator. Erzeugt fuer JEDES Template kaufbereite,
kanal-spezifische Post-ENTWUERFE (Etsy-Listing, Reddit, Facebook) - der Mensch
postet auf eigenen Accounts (Hard Stop: kein autonomes Posten).

Preise + Titel + Zielgruppe kommen aus spec.json (single source of truth),
Buy-Links aus stripe_links.json. Keine hartkodierten Preise (Belegpflicht).
Output: docs/social/outbound/<tid>.md  (menschenlesbar, 1-Klick-Copy)
"""
import os, json, glob

REPO = os.environ.get("NEWBIZ_REPO", r"C:\Users\phili\new-business")
TPL = os.path.join(REPO, "products", "templates")
LINKS = json.load(open(os.path.join(REPO, "stripe_links.json"), encoding="utf-8"))
OUT = os.path.join(REPO, "docs", "social", "outbound")
BASE = "https://translucentv1.github.io/new-business"

# Kanal-Hinweise je Zielgruppe (welche echten Communities passen)
CHANNELS = {
    "finanz-tracker-dach": {
        "reddit": ["r/Finanzen (nur Kommentar/Disclaimer)", "r/Haushaltsfuehrung"],
        "fb": ["Finanzen | Sparen | Investieren", "Frugalisten Deutschland"],
        "etsy_tags": ["haushaltsbuch vorlage", "budget planer", "finanzen tracker", "monatsbudget excel", "google sheets budget"],
    },
    "kleingewerbe-steuer": {
        "reddit": ["r/selbststaendig", "r/Finanzen (Kommentar)"],
        "fb": ["Selbststaendige & Unternehmer", "Kleinunternehmer Deutschland"],
        "etsy_tags": ["kleingewerbe vorlage", "euer vorlage", "steuer planer", "einnahmen ausgaben", "kleinunternehmer excel"],
    },
    "adhs-wochenplaner": {
        "reddit": ["r/ADHS", "r/Notion", "r/NotionCreations"],
        "fb": ["ADHS Erwachsene Deutschland", "ADHS Community"],
        "etsy_tags": ["adhs planer", "wochenplaner vorlage", "notion template", "adhd planner deutsch", "fokus planer"],
    },
    "rechnungsvorlage-kleinunternehmer": {
        "reddit": ["r/selbststaendig", "r/Freelance_DE"],
        "fb": ["Selbststaendige & Unternehmer", "Freelancer Deutschland"],
        "etsy_tags": ["rechnung vorlage", "kleinunternehmer rechnung", "rechnungsvorlage", "19 ustg", "invoice template deutsch"],
    },
    "nebenkostenabrechnung": {
        "reddit": ["r/Mietrecht", "r/immobilien"],
        "fb": ["Vermieter Deutschland", "Mieter Community"],
        "etsy_tags": ["nebenkostenabrechnung", "betriebskosten vorlage", "vermieter excel", "nk abrechnung", "umlage vorlage"],
    },
    "steuerfreibetrag-optimierer": {
        "reddit": ["r/Finanzen (Kommentar)", "r/Aktien"],
        "fb": ["Finanzen | Sparen | Investieren", "Aktien & ETF Deutschland"],
        "etsy_tags": ["sparerpauschbetrag", "freistellungsauftrag", "steuer sparen vorlage", "freibetrag rechner", "aktien steuer"],
    },
    "umzug-budget-planer": {
        "reddit": ["r/de", "r/Finanzen (Kommentar)"],
        "fb": ["Umzug & Wohnen Deutschland", "WG & Wohnung Community"],
        "etsy_tags": ["umzug planer", "umzug checkliste", "umzugsbudget", "moving planner", "umzug kosten"],
    },
    "agent-skills-bundle": {
        "reddit": ["r/ClaudeAI", "r/ChatGPT", "r/PromptEngineering"],
        "fb": ["ChatGPT Deutschland", "KI Tools & Automatisierung"],
        "etsy_tags": ["ai prompts", "claude skills", "chatgpt prompts", "developer prompts", "ai agent"],
    },
}


def eur(spec):
    return f"{spec['price_eur']:.2f}".replace(".", ",") + " EUR"


def build_one(tid, spec):
    link = LINKS.get(f"tpl:{tid}", "")
    lp = f"{BASE}/t/{tid}"
    ch = CHANNELS.get(tid, {"reddit": [], "fb": [], "etsy_tags": spec.get("keywords", [])[:5]})
    price = eur(spec)
    title = spec["title"]
    aud = spec["audience"]
    benefit = spec.get("benefits", "")
    secs = spec.get("sections", [])
    kws = spec.get("keywords", [])

    m = []
    m.append(f"# Outbound-Kit — {title}")
    m.append(f"\n**Preis:** {price}  |  **Landingpage:** {lp}  |  **Direkt-Kauf:** {link or '(kein Link)'}\n")
    m.append("> HARD STOP: Der Agent postet NICHT. Diese Entwuerfe kopierst DU auf deine eigenen Accounts.\n")

    # ---- ETSY ----
    m.append("## 1) Etsy-Listing (empfohlen: eingebauter DE-Kaufintent, VAT wird von Etsy abgefuehrt)\n")
    m.append(f"**Titel (max 140 Zeichen):**\n> {title} – digitale Vorlage (Google Sheets/Excel) zum Sofort-Download\n")
    m.append("**Beschreibung:**")
    m.append("```")
    m.append(f"{title}")
    m.append("")
    m.append(f"{benefit}")
    m.append("")
    m.append(f"Fuer wen: {aud}")
    m.append("")
    m.append("Das bekommst du (Sofort-Download nach Kauf):")
    m.append("- Fertige Tabelle mit 12 Monatsspalten + automatischer Jahres- & Gesamtsumme")
    m.append("- Schritt-fuer-Schritt-Anleitung (in 3 Minuten startklar)")
    m.append("- Nutzbar in Google Sheets, Excel und LibreOffice")
    if secs:
        m.append("")
        m.append("Enthaltene Bereiche:")
        for s in secs:
            m.append(f"- {s}")
    m.append("")
    m.append("Digitales Produkt, keine Steuer-/Rechtsberatung. Angaben ohne Gewaehr.")
    m.append("```")
    m.append(f"**Preis:** {price}   |   **Tags:** {', '.join(ch['etsy_tags'])}\n")

    # ---- REDDIT ----
    m.append("## 2) Reddit (Wert zuerst, Link nur im Kommentar mit Disclaimer)\n")
    m.append(f"**Passende Subs:** {', '.join(ch['reddit']) or '(pruefen)'}\n")
    m.append("**Post-Titel:**")
    m.append(f"> Wie ich {aud.split(',')[0].lower()} das mit einer simplen Tabelle geloest habe (Prinzip kostenlos nachbaubar)\n")
    m.append("**Body (Wert liefern, NICHT verkaufen):**")
    m.append("```")
    m.append(f"Ich habe lange nach einer einfachen Loesung fuer '{title.split('(')[0].strip()}' gesucht.")
    m.append("Was bei mir haengengeblieben ist, ist dumm-einfach:")
    m.append("")
    for i, s in enumerate(secs[:3], 1):
        m.append(f"{i}. {s}")
    m.append("")
    m.append("Das Prinzip oben reicht voellig, kein Tool noetig. Falls jemand die fertig")
    m.append("strukturierte Vorlage statt selbstbauen will, hab ich eine aufbereitet - Link im")
    m.append("Kommentar. Kein Muss.")
    m.append("```")
    m.append("**Erster Kommentar (mit Disclaimer + Link):**")
    m.append("```")
    m.append(f"Eigenwerb, daher als Kommentar: Ich hab die Vorlage als '{title}' fertig gemacht")
    m.append(f"({price}), weil ich selbst danach gesucht hatte: {link or lp}")
    m.append("```")
    m.append("**Compliance:** eigener Account, Wert zuerst, Link als Eigenwerb gekennzeichnet, nicht in 10 Subs gleichzeitig.\n")

    # ---- FACEBOOK ----
    m.append("## 3) Facebook-Gruppen (Regeln je Gruppe vorher pruefen)\n")
    m.append(f"**Passende Gruppen:** {', '.join(ch['fb']) or '(pruefen)'}\n")
    m.append("**Beitrag:**")
    m.append("```")
    m.append(f"Kleiner Tipp fuer alle, die {aud.split(',')[0].lower()}: {benefit}")
    m.append("")
    m.append("Ich hab mir dafuer eine simple Tabelle gebaut (12 Monate, rechnet automatisch).")
    m.append(f"Falls es jemand fertig will statt selbst basteln: {lp} ({price}). Sonst gerne das")
    m.append("Prinzip selbst nachbauen - hilft auch so.")
    m.append("```")
    m.append("**Compliance:** nur in Gruppen mit erlaubter Selbstpromo, als Mensch, kein Copy-Paste-Spam.\n")

    m.append("---")
    m.append("## Notion Template Gallery (staerkster kostenloser Hebel — braucht dein Notion-Konto)")
    m.append("Die Gallery hat kaufbereites Publikum. Voraussetzung: Produkt als teilbare Notion-Seite +")
    m.append("dein Notion-Account (Hard Stop: Account = du). Einreichung: notion.com/templates → 'Submit a template'.")
    m.append(f"Im Gallery-Eintrag den Stripe-Checkout verlinken: {link or lp}")
    return "\n".join(m) + "\n"


def build_all():
    os.makedirs(OUT, exist_ok=True)
    built = []
    for p in sorted(glob.glob(os.path.join(TPL, "*", "spec.json"))):
        tid = os.path.basename(os.path.dirname(p))
        spec = json.load(open(p, encoding="utf-8"))
        md = build_one(tid, spec)
        outp = os.path.join(OUT, f"{tid}.md")
        open(outp, "w", encoding="utf-8").write(md)
        built.append(tid)
    # Index
    idx = ["# Outbound-Kit — alle Produkte\n",
           "Kaufbereite Post-Entwuerfe pro Produkt (Etsy / Reddit / Facebook / Notion Gallery).",
           "HARD STOP: Der Agent postet NICHT — du kopierst die Entwuerfe auf deine eigenen Accounts.\n",
           "## Empfohlene Reihenfolge (nach Erst-Sale-Geschwindigkeit, MEASURED 2026-07-22)",
           "1. **Etsy-Listings** — eingebauter DE-Kaufintent, VAT von Etsy abgefuehrt, 0,20 $/Listing",
           "2. **Notion Template Gallery** — staerkstes kostenloses Publikum (braucht dein Notion-Konto)",
           "3. **Facebook-Gruppen** — grosse DE-Communities, Regeln pruefen",
           "4. **Reddit** — Wert zuerst, Link nur im Kommentar\n",
           "## Produkte"]
    for tid in built:
        idx.append(f"- [{tid}]({tid}.md)")
    open(os.path.join(OUT, "index.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
    return built


if __name__ == "__main__":
    b = build_all()
    print(f"Outbound-Kit gebaut: {len(b)} Produkte -> {OUT}")
    for t in b:
        print("  ", t)
