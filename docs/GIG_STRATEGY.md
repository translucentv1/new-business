# GIG-STRATEGIE — "Tasks für Geld" (Bens Video-Lehre, legal + $0)

Stand: 2026-07-28. Pivot weg von Buch-Verkauf (tot laut User) hin zu dem, was in den
3 Videos funktioniert hat: **Aufgaben erledigen → Geld**. Bens "Task Market" war
der einzige echte Money-Maker (Soul, Teil 2). Wir spiegeln das legal als Fiverr-Gig
+ Gumroad-Templates.

## Was verkaufen wir? (MEASURED-Nachfrage aus research/markt-non-etsy.md)
1. **Fiverr: "KI-Text & Code in 24h"** — Festpreis-Gig. Nutzt LLM_API_KEY (openai, schon gesetzt)
   + RTD-Engine. Käufer beschreibt, wir liefern Deliverable. Echte Nachfrage
   (fiverr.com/categories/programming-tech MEASURED live).
2. **Gumroad: Notion-Templates** — 11.330 Listings unter Tag = Nachfrage bewiesen.
   Status 2026-08-01 MEASURED: Watcher **läuft NICHT** — `scripts/gumroad_sale_poll.py`
   gibt `NO TOKEN` aus, es existiert nur `.gumroad_secrets.template`, kein echtes
   Token. Blocker sind also ZWEI: Payout-Freischaltung *und* API-Token (beide USER).
3. **Lead-Magnet** (lead_magnet.html) = Top-of-Funnel, bleibt.

## Warum das funktioniert (Bens eigene Lektion)
- "Distribution is the hard part" → wir nutzen Fiverr/Gumroad als fertigen
  Traffic-Kanal statt SEO-Buch-Seiten.
- "Make a product people ask for" → Dienstleistung = Auftrag existiert VOR Erstellung.

## Autonomer Loop (cronjob bae39ea51a60)
- Fiverr-Gig-Text generieren + in docs/ ablegen (Account-Erstellung = USER, KYC).
- Bei eingehendem Auftrag: RTD-Engine erstellt Deliverable, Stripe/Link zahlt.
- Gumroad-Payout-Watcher weiter aktiv.

## KOSTEN-REGEL (User-Freigabe 2026-07-28)
Jede ausgehende Ausgabe (Fiverr-Pro-Gebühr, Ads, Paid-Tools, Krypto-Deposit) braucht
vorher persönliche User-Bestätigung. Organisch ($0) autonom.
