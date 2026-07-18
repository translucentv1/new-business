# Pivot-Research: Bessere autonome Business-Modelle / Sale-Hebel

**Datum:** 2026-07-18 · **Verfasser:** Hermes (autonome Nachtschicht) · **Status:** RESEARCH NUR
**Mandat:** Kein Business-Pivot in der Nacht — dieser Text ist reine Recherche mit
MEASURED-Quellen. Keinerlei Umsetzung. Entscheidung trifft der Nutzer wach.

## Kontext
Aktueller Stand (MEASURED heute Nacht): Download-Gate live (TB-8..11), 7 saubere
Bücher als Stripe Payment Links + SEO-Landingpages. Korruptes Bundle 25913
ausgeklammert (eigenes Ticket TB-13). Sale-Check: 0 Verkäufe (kein Traffic außer
organisch, keine Werbung — autonomes Social-Posting ist Hard Stop).

Die Frage dieses Dokuments: Welche Hebel **über** das bestehende Modell hinaus
könnten den ersten Sale beschleunigen, und welche sind ohne Hard Stop (Accounts/
Keys/Geld/Social/OAuth) heute überhaupt umsetzbar?

## Quellen (MEASURED)
- Stripe Payments/Payment Links: https://stripe.com/payments/payment-links (abgerufen 2026-07-18) — Payment Links sind "conversion-optimized, full-page checkout",
  redirect- oder embed-fähig, anpassbar (Farben/Schrift).
- Stripe Checkout-Optimierung: https://stripe.com/resources/more/checkout-optimization-tips-to-improve-conversion-rates (2026-07-18) — Checkout-Tipps (Reibung
  senken, Vertrauen, lokale Zahlarten).
- Stripe Global-Demand: https://stripe.com/blog/new-ways-to-turn-global-demand-into-revenue (2026-07-18) — "even one geographically irrelevant payment method can
  decrease conversion by up to 15%" → lokale Zahlarten (z.B. SEPA/Karte in DE) sind
  relevant; Stripe Payment Links decken DE/EUR bereits ab.
- Kotobee PD-Guide: https://blog.kotobee.com/what-are-public-domain-books/ (2026-07-18) — Überblick legale PD-Monetarisierung (Aufbereitung/Formatierung als
  Mehrwert).
- Amazon KDP PD-Richtlinie: https://kdp.amazon.com/help/topic/G200743940 (2026-07-18) — KDP erlaubt PD-Verkauf, kann aber Nachweis der PD-Status fordern;
  Reddit-Selbstpublisher berichten (https://www.reddit.com/r/selfpublish/comments/1cco7n8/), dass Amazon PD wegen Scammer-Problematik restriktiver handhabt. →
  KDP ist ein möglicher späterer Kanal, aber mit höherem Risiko/Prüfaufwand.

## Optionen (nur bewertet, nicht umgesetzt)

### A. Traffic vertiefen (heute NACHT umsetzbar, kein Hard Stop)
- **Long-Tail-SEO ausbauen:** pro Buch 3–5 thematische Landingpages (z.B.
  "Frankenstein kostenlos lesen", "Dracula als eBook kaufen"), interne Verlinkung.
  Hebel: mehr indexierte Seiten = mehr organische Treffer. Risiko: gering.
  Beleg: Stripe-Doku bestätigt, dass Checkout-Konversion von Erreichbarkeit
  (lokale Zahlart/Sprache) abhängt; SEO erhöht die Basis.
- **E-Mail-Capture (Warte-/Newsletter):** Lead-Magnet "kostenlose Leseprobe per
  Mail". ABER: DSGVO-Pflichten (Einwilligung, Impressum, ggf. Double-Opt-In),
  verlangt ggf. einen (vom Nutzer freizugebenden) Mail-Versand-Account. Heute Nacht
  NICHT ohne Nutzer (Account = Hard Stop / DSGVO-Freigabe).

### B. Angebot schärfen (teilweise heute NACHT umsetzbar)
- **Bundle/Preis-Hebel:** 2-books-1-price, oder "3 für X". Stripe Payment Links
  unterstützen mehrere Line Items; Umsetzung im `stripe_uploader.py` möglich,
  braucht aber neue Links + Nutzer-Preisentscheidung. Kein Hard Stop, aber
  Geschäftsentscheidung → Nutzer.
- **EPUB-Deliverable (Tier-2):** stdlib `zipfile`, kein PDF-Infra-Need. Hebt
  Produktwert (Lesbarkeit auf E-Reader). Im Spec als späteres Ticket markiert,
  heute NACHT technisch machbar (kein Hard Stop).

### C. Andere Vertriebskanäle (NICHT heute Nacht — Nutzer + teils Hard Stop)
- **Amazon KDP:** s.o., PD erlaubt aber restriktiv, Account-Anlage = Hard Stop.
- **Gumroad/Payhip:** bereits als Backup vorhanden; DE-Sperre/Steuer-Themen waren
  Grund für Stripe-Pivot (ADR-0010/0011). Kein Pivot nötig.
- **Social-Traffic (Pinterest/Reddit/TikTok):** autonomes Posten = explizit
  verboten (Hard Stop + Charta). Nur mit Nutzer-Freigabe.

### D. Serverseitig verifiziertes Gate (Conversion-Sicherheit)
- Heute: Obscure-URL (kein echtes Gate). Ein signiertes/Serverless-Gate würde
  Teilen-umgehen verhindern, braucht aber Deploy-Infra = Hard-Stop-Nähe. Im
  ADR-0013 als bekanntes Loch akzeptiert.

## Empfehlung (für Nutzer, nicht autonom ausgeführt)
1. **Schnellster Hebel heute/sofort:** mehr Long-Tail-SEO-Seiten (A) — reiner
   Content, kein Risiko, baut die einzige fehlende Variable (Traffic) aus.
2. **Produktwert:** EPUB-Tier-2 (B) nachholen — hebt Conversion bei E-Reader-
   Nutzern, reine stdlib-Arbeit.
3. **Erst wenn Verkäufe rollen:** KDP als zweiter Kanal (C) prüfen — dort ist das
   PD-Geschäft skaliert, aber mit Account- und Prüfaufwand.
4. **Kein** Social-Posting ohne ausdrückliche Freigabe.

## Offen / Blocker
- 25913-Bundle korrupt (TB-13): welches Buch soll es sein? Muss der Nutzer klären.
- Traffic ist die echte Unbekannte: ohne Sichtbarkeit bleiben 0 Sales, egal wie
  gut das Gate ist.
