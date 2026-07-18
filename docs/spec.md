# Spec — Autonomous Public-Domain Digital Products (Gumroad API)

## Problem Statement (Nutzersicht)
Der Nutzer will ein legales, free-to-build Business mit maximaler Autonomie: der Agent
soll Produkte erzeugen, verkaufen und reinvestieren — ohne dass der Nutzer bei jedem
Schritt freigibt. Bisher scheiterte physische Arbitrage an der Liquiditäts-Lücke.

## Solution (Nutzersicht)
Ein autonomer Loop: der Agent nimmt gemeinfreie (Public-Domain) deutsche Sachtexte,
bereitet sie auf (Struktur, Rechtschreibung, Register, Begleit-PDF) und verkauft sie via
Gumroad-API. Ein EINZIGES Nutzer-OK (Gumroad-Account + API-Key) startet den Loop; danach
läuft alles selbst: Produkt-Generierung, Upload, **Sale-Tracking (POLLING, nicht Webhook —
siehe ADR-0008)**, Reinvestition des Gewinns in Scraper/LLM. Kein menschlicher Eingriff
im Betrieb.

## Preis (ADR-0006)
- Startpreis **$3,99 fest** (kein PWYW). Gumroad-Gebühr 10%+$0,50 fix (MEASURED) -> netto
  ~$3,09 (77%). Konstante `PD_PRICE_CENTS=399`, per Env überschreibbar. A/B nach Go-Live.

## Distribution (ADR-0007) — der eigentliche Engpass
Gumroad Discover bringt erst Traffic NACH $100 echten Verkäufen + Risk-Review ~3 Wochen
(MEASURED gumroad.com/help/article/79). Gumroad = Checkout-Tool, kein Marktplatz. Ohne
externen Traffic verkauft nichts, egal welcher Preis. Kostenlose Kanäle (ASSUMED-Wirksamkeit,
je Kanal per Mini-Experiment zu härten), Prio:
1. SEO-Landingpage je Produkt (statisches HTML, GitHub Pages = gratis) -> Long-Tail-Suche.
2. Pinterest-Pins je Titel (gratis, SEO-getrieben, keine Follower nötig).
3. Reddit/Foren nur regelkonform (niedrige Prio, ToS-Risiko).

## Nahtstellen (Seams)
1. **Gumroad Sale-Poll -> Gewinn-Beleg.** Einzige Stelle, an der "echtes Geld" sichtbar wird.
   `GET /v2/sales` (Bearer), nur Sales neuer als last-seen ts. MEASURED Sale (price>0) ->
   Reinvestitions-Logik triggert (ADR-0005).
2. **Datei-Upload -> Presign-Flow.** `POST /v2/files/presign` -> S3-PUT -> `/v2/files/complete`
   -> `PUT /v2/products/{id}` mit `files[][url]`. End-to-end MEASURED 2026-07-18 (persisted=True).

## Nicht-Ziele (Scope)
- Kein physisches Produkt, kein Shipping.
- Kein eigener Webshop (Gumroad übernimmt Checkout/Payout).
- Keine Kaltakquise.

## Erfolgskriterium
- Loop läuft ohne Human-in-Loop nach einmaligem OK.
- Belegter Sale (Poll) -> Reinvestition automatisch.
- Rechtssicher (nur PD, EU Leben+70J; PD-Verkauf auf Gumroad erlaubt, MEASURED /prohibited).
- Mind. 1 Traffic-Kanal live je Produkt (Landingpage), sonst 0 Sichtbarkeit.

## Offene Recherche-Lücken — vor/nach Echtbetrieb
- Gewerbeanmeldung + USt-Kleinunternehmerregelung DE (§19 UStG: 25.000€ Vorjahr/100.000€
  laufend, MEASURED KU-Reform 2025). Gumroad ist Merchant of Record seit 1.1.2025 -> USt
  weltweit von Gumroad gehandhabt (MEASURED gumroad.com/pricing), Einkommen-/Gewerbesteuer
  bleibt beim Nutzer. Vor ersten belegten Einnahmen klären (GO-LIVE-CHECKLISTE).
- Kanal-Wirksamkeit (Landingpage-SEO, Pinterest) — ASSUMED, per Mini-Experiment MEASURED machen.
