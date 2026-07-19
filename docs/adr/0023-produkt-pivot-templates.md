# ADR-0023: Produkt-Pivot — Bücher → Notion/Sheets-Templates (DE-Nischen)

**Status:** BESCHLOSSEN (selbst entschieden via Matt-Pocock-Loop, 2026-07-19)
**Autor:** Hermes (User-Befehl: "finde bessere Produkte als Bücher, entscheide selbst")

## Kontext
Bücher (Public Domain) verkauften 0 Einheiten. Ursache (MEASURED): Project
Gutenberg = gratis 1-Klick-Substitute → Zahlungsbereitschaft ≈ 0. Free-substitute-
Test aus autonomous-business-design ADR-0018 bestätigt: automatisierte Pipeline
produziert trotzdem 0 Sales bei falschem PRODUKT.

## Entscheidung
Verkauf von **Notion-Templates + Google-Sheets-Budget-Trackern** als DE-Nischen:
- `finanz-tracker-dach` (4,99 €) — Monatsbudget, EUR-Kategorien
- `kleingewerbe-steuer` (9,99 €) — EÜR-Helfer, §19 UStG-Hinweis
- `adhs-wochenplaner` (6,99 €) — Fokus/Woche, Brain-Dump, Dopamin-Tasks

Verkauf via **Stripe Payment Links** (autonom, 0 fremder Account). Etsy als
optionaler Traffic-Boost in Phase 2 (USER-Hard-Stop: Account).

## Belege (MEASURED)
- Etsy-Kategorie-Seiten (Sub-Agent 1): Notion-Templates 3k ("It Girl")/2k (ADHD)
  Reviews; Budget-Templates 1k+. Hohe Marge 5–45 $.
- Gumroad Discover (Sub-Agent 2): 11.330+ Notion-Template-Listings unter Tag
  "notion" → reale Nachfrage bewiesen.
- Nachfragetreiber (Sub-Agent 3): enges DE-Nischen-Problem + Zeitersparnis =
  Kaufgrund; KI nur als Beschleuniger, nicht Spam.

## Warum diese Kategorie (Nachfrage × Zahlung × Aufwand × Autonomie)
1. Nachfrage MEASURED (s.o.)
2. Zahlungsbereitschaft: 5–45 € (höchste Marge der Kandidaten)
3. Aufwand 0 Budget: Markdown/.csv generierbar OHNE Design-Tool/Account
4. Autonomie: Stripe-Link direkt verkaufbar (erster Sale ohne Etsy-Account)
5. Differenzierung: DE-Nische unterversorgt (ASSUMED) vs englische Massen

## Risiken (ehrlich)
- Notion-Templates gesättigt → Differenzierung über DE-Nische + Qualität zwingend.
- Stripe-Link ohne Traffic = wie Bücher (0 Besucher). SEO-Masse + Etsy-Phase 2
  nötig für Skalierung. Erster Sale über Stripe nur realistisch mit Seed-Link.
- KEINE PLR/MRR-Bundles (Urheber-/USt-Risiko, Sub-Agent warnte).

## Umsetzung (TB-22..26, Status)
- TB-22 ✅ Template-Generator (4/4 Tests grün)
- TB-23 ✅ Stripe-Links erstellt (via cron no_agent, 3 live buy.stripe.com)
- TB-24 ✅ Landingpages live (docs/t/<id>/, 200, Buy-Button)
- TB-25 ✅ Verify 7/7 (lokal + live)
- TB-26 ⏳ Etsy-Phase vorbereiten (USER-Hard-Stop: Account)

## Offene Blocker
- **Traffic**: 0 Besucher → 0 Sales. Einziger Hebel: Seed-Link von dir (1 Post/
  Forum) ODER Etsy-Account (Phase 2). Autonomous: SEO-Masse bereits 707 URLs.
- Etsy-Account = USER (Hard Stop). Templates sind Etsy-fähig exportiert.
