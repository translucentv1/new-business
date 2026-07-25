# ADR-0035 — Request-to-Delivery Micro-SaaS (UGC-/Concierge-Pivot)

Erstellt: 2026-07-25 (autonome Session, Nutzer-Grant "6h autonom")
Quelle: Nutzer-Idee "verschiedene Nachfragen erfüllen" + POD-China-Rechnung
(ab 1.7.2026 EU-Zoll +3€/Artikel -> China-Vorteil weg, daher EU-POD/Shirtee
und Service-Modell statt China-Import).

## Entscheidung
Wir bauen einen **Request-to-Delivery**-Kanal: Kunde beschreibt auf einer
Formularseite, was er braucht (Text, Template, Code-Snippet, Study-Guide,
Design-Idee); wir generieren das Lieferobjekt und nehmen die Zahlung via
Stripe Payment Link. Bestehende Infra (24 Stripe-Links, 1300 Landingpages,
gh-pages) wird wiederverwendet.

## Warum dieser Hebel (gegen ADR-Kriterien)
- **0 Investment:** POD/Service auf Bestellung, kein Lager. (Stripe druckt
  bzw. wir liefern digital.) ✅
- **Max Autonomie:** Formular + Generator + Stripe-Link autonom baubar. ⚠️
  Echter Verkauf braucht Live-Stripe-Key (aktuell in `.stripe_secrets` nur
  Platzhalter `***`; ein `sk_test_...` taucht in der Env auf, wird aber
  NICHT genutzt — Test-Keys erzeugen keine echten Sales, Hard-Stop).
- **Schneller erster Sale:** Haengt wie bisher am **Traffic**-Blocker
  (ADR-0022). Request-to-Delivery loest ihn nicht, ist aber ein
  niedrigschwelligeres Angebot als "kaufe mein Buch".
- **Skalierbar:** Jede Anfrage = eigener Link + eigener Fulfillment. ✅
- **Rechtlich:** Service-Verkauf = Gewerbeanmeldung bei Regelmaessigkeit +
  Impressum + AGB vor oeffentlichem Launch. UGC-Uploads (Kunde laedt eigene
  Bilder hoch) wuerden Art.17-Haftung ausloesen -> vorerst NUR Textanfragen,
  keine User-Uploads. ✅ sauber.

## Technischer Stand (MEASURED 2026-07-25)
- `scripts/request_delivery/app.py`: stdlib http.server (kein Flask),
  Routen `/` (Form), `/request` (POST -> Stripe-Link), `/status/<id>`,
  `/webhook` (Stripe). DEMO-Modus greift, wenn kein `sk_live_`-Key da ist.
- `scripts/request_delivery/generator.py`: LLM-Call (Ollama/local) mit
  Template-Fallback, keine hardcoded Keys.
- `scripts/request_delivery/orders.json`: Order-Store.
- **Offen:** Live-Stripe-Key fehlt -> aktuell DEMO. Echter Sale erst nach
  Key-Eintrag + Impressum/AGB/Gewerbeanmeldung.

## Naechste Schritte
1. Nutzer traegt `sk_live_...` in `.stripe_secrets` ein.
2. Ich baue Webhook-Verifkation + Fulfillment-Trigger (Generator bei Paid).
3. Angebotsseite an bestehende 1300 Landingpages anhaengen (Cross-Link).
4. Impressum/AGB-Template (rechtlich vor Launch).

## Status
Skeleton gebaut + lokal getestet (DEMO). Echter Sale blockiert auf
Live-Key (Nutzer) + Gewerbe/Impressum.
