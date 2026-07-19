# SPEC: Notion-Templates + Sheets-Budget-Tracker (Produkt-Pivot)

**Problem:** Public-Domain-Bücher verkaufen sich nicht (0 Sales). Ursache: freier
Substitute (Gutenberg) + kein eingebauter Traffic. Neue Strategie: digitale Produkte
mit echter Nachfrage + Zahlungsbereitschaft, die ich autonom erzeugen + verkaufen kann.

**Lösung:** Notion-Templates (Life/Business) + Google-Sheets-Budget-Tracker, als
DE-Nischen-Produkte (Finanz-Tracker DACH, Kleingewerbe-Planner, ADHS-Wochenplaner).
Verkauf über bestehenden Stripe-Link-Rail (autonom, 0 Account nötig für ersten Sale)
+ optional Etsy später (dein Account = Hard Stop).

## Seams (wo Testing/Verifikation passiert)
1. **Produkt-Generator** (`scripts/template_gen.py`): erzeugt Notion-.md + Sheets-.csv
   aus einer Produkt-Spec. NAHT: Struktur-Validierung (hat alle Sektionen, ist nicht leer).
2. **Stripe-Link** (`scripts/stripe_uploader.py`, existiert): neue Links für Templates.
3. **Landingpage** (`scripts/landingpage_gen.py`, existiert): erweitert um Template-Seiten.
4. **Sale-Poll** (`scripts/stripe_uploader.py poll`, existiert): unverändert.

## Produkt-Spezifikation (MVP, Tracer-Bullet)
- **P1: "Finanz-Tracker DACH"** (Sheets/.csv) — Monatsbudget, Ausgaben-Kategorien (EUR),
  Spar-Ziel, automatische Summen. Zielgruppe: DE-Sparer. Preis 4,99 €.
- **P2: "Kleingewerbe-Steuer-Planner"** (Sheets/.csv) — Einnahmen/Ausgaben, §19 UStG
  Hinweis, Jahresübersicht. Zielgruppe: DE-Kleingewerbler. Preis 9,99 €.
- **P3: "ADHS-Wochenplaner"** (Notion-.md) — Struktur für Fokus/Woche, Brain-Dump,
  Dopamin-Tasks. Preis 6,99 €.

##hart Stop / USER-Schritte (explizit)
- Etsy-Account anlegen + Verifizierung = DU (Phase 2 Traffic).
- Stripe-Payout bereits verbunden (MEASURED: payouts_enabled=True).
- Kein Geld ausgeben, keine Accounts ohne dich.

## Erfolgs-Metrik
- Erster echter Sale (Charge > 0) via Stripe-Poll. Dann Skalierung (mehr Templates,
  Etsy-Phase).
