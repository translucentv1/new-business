# ADR-0032 — Business #2: Reselling/Arbitrage (Recherche & Strategie)

Erstellt: 2026-07-23 (autonome Selbstverbesserungs-Session)
Quelle: Web-Recherche (Primärquellen, MEASURED 2026-07-23)

## Ausgangslage
Nutzer schlug "Kleinanzeigen/Vintage Arbitrage Bot" als 2. Business vor.
Recherche-Ergebnis:

### Kleinanzeigen-Bot (GitHub Second-Hand-Friends/kleinanzeigen-bot)
- Aktiv: 410 Stars, 44 Contributors, AGPL-3.0, letzter Commit 2 Tage alt
- Funktionsweise: Browser-Automatisierung (playwright) zum Publish/Republish
- EIGENER DISCLAIMER: "could violate the terms of service of kleinanzeigen.de"
- **ENTSCHEIDUNG: NICHT BAuen.** Verstößt gegen ADR-0030/0031 Hard-Stop
  "nichts rechtlich belangbares, kein ToS-Bypass". ToS-Verletzung = Risiko.

### Legale Alternativen (recherchiert)
1. **eBay Seller Center / Seller API** (offiziell, ToS-konform)
   - Drittanbieter-Tools erlaubt: Inventory, Promotions, Payments, Feedback
   - Quelle: ebay.com/sellercenter/ebay-for-business/third-party-providers
   - Arbitrage via offizielle API = compliant
2. **Vinted** — verbietet explizit Third-Party-Tools (Facebook-Group-Warnung)
   → Riskant, meiden
3. **eBay Launches Seller Tools** — AI-assisted replies, automated feedback
   → Plattform-eigene Automatisierung, sicher

## Strategie Business #2 (EMPFOHLEN, legal)
- Plattform: **eBay** (offizielle Seller API, kein ToS-Risiko)
- Modell: Vintage/Arbitrage — aber echter, eigener Bestand (kein Scraping
  fremder Inserate zu ToS-widrigen Zwecken)
- Automatisierung NUR über offizielle eBay-APIs (Compliance)
- Voraussetzung: eBay-Seller-Account (Nutzer erstellt, wie Stripe)
- Startkapital: 0 (erst nach erstem echten Sale reinvestieren, ADR-0030)

## Tools die wir brauchen könnten (recherchiert, legal)
- eBay Developer Program API (offiziell, kostenlos für Basis)
- SuperDS / Crosslisting-Tools (hybrid, keine Backend-Verletzung)
- Unsere eigenen 7 Agent-Skills → PromptBase (läuft schon)

## Nächste Schritte (blockiert auf Nutzer)
1. Nutzer erstellt eBay-Seller-Account (wie Stripe-Onboarding)
2. Ich baue eBay-API-Integration (offiziell, compliant)
3. Arbitrage-Logik: eigene Listings automatisiert verwalten

## Hard-Stop-Status
Kleinanzeigen-Bot: BLOCKIERT (ToS-Verletzung).
eBay Seller API: ERLAUBT (offiziell, compliant).
