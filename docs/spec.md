# Spec — Autonomous Public-Domain Digital Products (Gumroad API)

## Problem Statement (Nutzersicht)
Der Nutzer will ein legales, free-to-build Business mit maximaler Autonomie: der Agent
soll Produkte erzeugen, verkaufen und reinvestieren — ohne dass der Nutzer bei jedem
Schritt freigibt. Bisher scheiterte physische Arbitrage an der Liquiditäts-Lücke.

## Solution (Nutzersicht)
Ein autonomer Loop: der Agent nimmt gemeinfreie (Public-Domain) deutsche Sachtexte,
bereitet sie auf (Struktur, Rechtschreibung, Register, Begleit-PDF) und verkauft sie via
Gumroad-API. Ein EINZIGES Nutzer-OK (Gumroad-Account + API-Key) startet den Loop; danach
läuft alles selbst: Produkt-Generierung, Upload, Sale-Tracking (Webhook), Reinvestition
des Gewinns in Scraper/LLM. Kein menschlicher Eingriff im Betrieb.

## Nahtstellen (Seams) — eine, so hoch wie möglich
**Gumroad Sale-Webhook -> Gewinn-Beleg.** Das ist die einzige Stelle, an der "echtes Geld"
sichtbar wird. Alles andere (Generierung, Upload, Reinvestition) ist code-intern und
autonom. An dieser Naht wird geprüft: MEASURED Sale? -> Reinvestitions-Logik triggert.

## Nicht-Ziele (Scope)
- Kein physisches Produkt, kein Shipping.
- Kein eigener Webshop (Gumroad übernimmt Checkout/Payout).
- Keine Kaltakquise (KMU-Service-Pfad gestrichen zugunsten Autonomie).

## Erfolgskriterium
- Loop läuft ohne Human-in-Loop nach einmaligem OK.
- Belegter Sale (Webhook) -> Reinvestition automatisch.
- Rechtssicher (nur PD, EU Leben+70J).

## Offene Recherche-Lücken (aus grill-recherche E.) — vor Echtbetrieb schließen
- Gewerbeanmeldung Freibetrag 410€/Jahr + USt-Kleinunternehmerregelung exakt.
- eBay/Kleinanzeigen "wiederholt = gewerblich" (nur relevant, falls PD-Scraper dort quellt).
- Gumroad Discover-Traffic-Anteil (10-20%?) zur Abschätzung der Erreichbarkeit.
