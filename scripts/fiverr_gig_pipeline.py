"""Fiverr Gig Pipeline (autonomous preparation, USER publishes).

Generates ready-to-paste Fiverr gig drafts for DE niches where the user already
has deliverables (Notion/Sheet templates, Dev-Skills). Fiverr requires a human
account + KYC, so this ONLY produces the copy — the user pastes it into
fiverr.com/seller and hits publish. No API exists for gig creation.

Output: fiverr_gigs_draft.json  (one entry per gig, with title/subtitle/
description/packages/price/tags/category) — print-ready.
"""
import json
import os
import datetime

REPO = r"C:\Users\phili\new-business"
OUT = os.path.join(REPO, "fiverr_gigs_draft.json")

# DE niches mapped to the user's existing deliverables (from stripe_links.json / gumroad products)
GIGS = [
    {
        "niche": "Finanz-Tracker / Haushaltsbuch (DE)",
        "title": "Erstelle dir ein persönliches Haushaltsbuch & Finanz-Tracker in Excel/Google Sheets",
        "subtitle": "Mit automatischer Kategorisierung, Monatsauswertung und Spar-Ziel-Tracking",
        "category": "Personal Assistance / Financial Consulting",
        "tags": ["haushaltsbuch", "finanzen", "excel", "budget", "sheets"],
        "packages": {
            "basic": {"name": "Starter", "price_usd": 5, "desc": "1 fertiges Google-Sheet Haushaltsbuch mit 3 Kategorien + Anleitung"},
            "standard": {"name": "Pro", "price_usd": 15, "desc": "Haushaltsbuch + Finanz-Tracker mit Charts + Spar-Ziel + 1 Revision"},
            "premium": {"name": "Premium", "price_usd": 30, "desc": "Alles + Umzug-Budget-Planer + Steuerfreibetrag-Optimierer + 2 Revisionen"},
        },
        "deliverable_source": "products/templates/ (Haushaltsbuch, Finanz-Tracker DACH, Umzug, Steuerfreibetrag)",
    },
    {
        "niche": "Kleinunternehmer Rechnung & Steuer (§19 UStG)",
        "title": "Erstelle deine Rechnungsvorlage & Kleingewerbe Steuer-Planner als Sheets/CSV",
        "subtitle": "GoBD-konforme Rechnung + USt-Voranmeldung-Planer für deutsche Kleinunternehmer",
        "category": "Business / Accounting & Finance",
        "tags": ["rechnung", "kleingewerbe", "steuer", "ustg", "freelancer"],
        "packages": {
            "basic": {"name": "Rechnung", "price_usd": 5, "desc": "1 GoBD-Rechnungsvorlage (.docx/.xlsx) inkl. Impressum-Felder"},
            "standard": {"name": "Steuer-Planner", "price_usd": 15, "desc": "Rechnungsvorlage + §19-UStG Planer + Nebenkostenabrechnung"},
            "premium": {"name": "Full Setup", "price_usd": 30, "desc": "Alles + 1 Stunde Einrichtungs-Support per PDF/Video"},
        },
        "deliverable_source": "products/templates/ (Rechnungsvorlage, Kleingewerbe Steuer-Planner, NK-Abrechnung)",
    },
    {
        "niche": "ADHS Wochenplaner",
        "title": "Erstelle dir einen ADHS-Wochenplaner mit Fokus & Struktur (Notion/Sheets)",
        "subtitle": "Visueller Wochenrhythmus, Prioritäten-Matrix und Energie-Tracking",
        "category": "Lifestyle / Productivity",
        "tags": ["adhs", "wochenplaner", "notion", "produktivität", "fokus"],
        "packages": {
            "basic": {"name": "Template", "price_usd": 5, "desc": "1 ADHS-Wochenplaner-Template (Notion oder Sheets)"},
            "standard": {"name": "Pro", "price_usd": 15, "desc": "Wochenplaner + Monatsrückblick + 1 Anpassung"},
            "premium": {"name": "Coaching-Set", "price_usd": 30, "desc": "Alles + Umzug-Budget-Planer + 2 Anpassungen"},
        },
        "deliverable_source": "products/templates/ (ADHS-Wochenplaner, Umzug-Budget-Planer)",
    },
    {
        "niche": "Dev-Skills / Prompts (Claude/ChatGPT)",
        "title": "Schreibe dir wiederverwendbare Claude/ChatGPT Dev-Skills (Code-Review, Debug, Tests)",
        "subtitle": "7 fertige Skills als Markdown — sofort einsatzbereit, kein Prompt-Engineering nötig",
        "category": "Programming / Other",
        "tags": ["claude", "chatgpt", "dev-skills", "prompts", "coding"],
        "packages": {
            "basic": {"name": "1 Skill", "price_usd": 5, "desc": "1 maßgeschneiderte Dev-Skill (z.B. Code Reviewer)"},
            "standard": {"name": "Bundle", "price_usd": 15, "desc": "3 Dev-Skills deiner Wahl"},
            "premium": {"name": "Full Pack", "price_usd": 30, "desc": "Alle 7 Skills + Anleitung zur Einbindung"},
        },
        "deliverable_source": "products/templates/ (Agent-Skills Bundle – 7 Dev-Skills)",
    },
]


def build_description(g):
    return (
        f"Du brauchst {g['niche']}? Ich liefere dir ein sofort nutzbares Digital-Produkt, "
        f"das ich aus meiner fertigen Vorlagen-Bibliothek für deutsche Nutzer erstelle.\n\n"
        f"Was du bekommst:\n"
        f"- {g['subtitle']}\n"
        f"- Direkt einsatzbereit (Sheets/Notion/CSV/Markdown)\n"
        f"- Deutsche Anleitung inklusive\n\n"
        f"Quelle: kuratierte DE-Nischen-Templates (Finanzen, Steuern, ADHS, Dev-Skills)."
    )


def main():
    out = []
    for g in GIGS:
        entry = {
            "niche": g["niche"],
            "title": g["title"],
            "subtitle": g["subtitle"],
            "category": g["category"],
            "tags": g["tags"],
            "description": build_description(g),
            "packages": g["packages"],
            "deliverable_source": g["deliverable_source"],
            "status": "DRAFT_READY — USER pastes into fiverr.com/seller and publishes",
        }
        out.append(entry)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"generated": datetime.date.today().isoformat(), "gigs": out},
                  f, ensure_ascii=False, indent=2)
    print(f"DRAFTED {len(out)} Fiverr gigs -> {OUT}")
    for e in out:
        print(f"  [{e['niche'][:30]}] {e['packages']['basic']['price_usd']}$/{e['packages']['standard']['price_usd']}$/{e['packages']['premium']['price_usd']}$")


if __name__ == "__main__":
    main()
