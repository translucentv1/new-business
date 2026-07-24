# ADR-0034 — Business #3: Preisfehler-Scanner (Arbitrage)

Erstellt: 2026-07-23 (Nutzer hebt Hard-Stop für Scraping auf)
Quelle: Nutzer-Instruktion "scraping kannst du machen ich löse den hardstop auf.
das risiko dafür rechtlich belangt zu werden ist super gering"

## Entscheidung
- Hard-Stop "kein ToS-Bypass" für **Scraping öffentlicher Marktplatz-Daten**
  wird vom Nutzer EXPLIZIT aufgehoben (Risiko als gering eingeschätzt).
- Weiterhin VERBOTEN (auch nach Lift): fake Accounts, KYC/Steuer-Umgehung,
  IP-Verletzung, alles Straftbare.
- Methode: read-only HTTP-GET öffentlicher Suchen/Listings (kein Browser-Spam,
  keine Account-Erstellung). Offizielle APIs (eBay Browse) bevorzugt, wo verfügbar.

## Ziel
Preisfehler scannen (z.B. 500€-Item versehentlich für 50€ gelistet).
Nutzer wird ge-pinged → kauft + reselled. Agent gibt KEIN Geld aus.

## Plattformen
- eBay: offizielle Browse API (braucht Dev-Account — Nutzer muss License-Haken setzen)
- Kleinanzeigen: öffentliche Suche (ToS jetzt OK laut Nutzer)
- Amazon: schwer anti-bot, niedrige Priorität

## Alerting
- Nutzer wünscht Discord-Ping. Discord ist NICHT verbunden (nur Local + WhatsApp).
- Fallback: WhatsApp (schon verbunden, hier läuft der Chat).
- Discord-Connection nötig für exakten Wunsch.

## Nächste Schritte
1. Scanner-Skeleton bauen (scripts/price_scanner.py)
2. Test auf 1-2 Queries (Kleinanzeigen öffentlich)
3. Cron alle 30min + WhatsApp-Alert bei Treffer
4. eBay Browse API nach Nutzer-Signup integrieren
