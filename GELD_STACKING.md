# GELD STACKING — Methoden (legal, 0 Invest, autonom bewertet)

Recherchiert: 2026-07-26 (autonom, während Nutzer abwesend). Quellen: aequifin.com,
lowcontentprofits.com, medium.com/passive-income, reddit r/passive_income.

Ziel: Mehrere Einnahmequellen STACKEN, die alle 0 Invest brauchen und (teilweise)
autonom von Hermes gebaut werden können.

## Stack-Ranking (für unser Setup)

### 🥇 1. RTD-Service (BEREITS GEBBAUT — `scripts/request_delivery/`)
- Was: Kunden beschreiben Anfrage → wir liefern → Stripe-Zahlung
- Invest: 0 € (POD/digital auf Bestellung)
- Autonom: 90 % (nur Live-Key + Traffic fehlt)
- Stackt mit: allem anderen (Quer-Verkauf)
- Status: Fulfillment MEASURED (Order→Webhook→fulfilled)

### 🥇 2. POD mit eigenen Designs (EU/Shirtee)
- Was: Wir generieren Designs, Shirtee druckt auf Bestellung, verkauft via gh-pages
- Invest: 0 € (Shirtee druckt erst bei Sale)
- Autonom: 80 % (Design-Generierung + Integration baubar; Account bei Shirtee nötig)
- Rechtlich: sauber (kein China-Import seit 1.7.2026 Zoll +3€)
- Stackt mit: RTD (Design-Wünsche → POD), 1300 Seiten (Cross-Sell)

### 🥈 3. Affiliate-Links in 1300 Seiten einbauen
- Was: Amazon/Thalia-Partnerlinks in die 1224 Buch-Landingpages
- Invest: 0 €
- Autonom: 70 % (Injektion in `*/index.html` machbar; Generator unbekannt → Risiko
  bei Re-Build. Besser: CTA via geteiltes Snippet)
- Stackt mit: RTD + POD (Käufer ohne Kauf → Affiliate-Commission)
- Rechtlich: Impressum muss Affiliate-Verweise enthalten (§6 TMG)

### 🥈 4. Digital Products (KDP/Low-Content)
- Was: Notizbücher, Planer, Study-Templates via KDP (Amazon)
- Invest: 0 € (KDP druckt POD)
- Autonom: 60 % (Cover + Inhalt generierbar; Account bei Amazon KDP nötig)
- Stackt mit: 1300 Seiten (Cross-Promo)

### 🥉 5. Faceless YouTube / TikTok (AI-Narration)
- Was: KI-narrated Book-Summaries, Faceless
- Invest: 0 € (TTS + Bilder KI-generiert)
- Autonom: 40 % (Skript + Voice + Video baubar; UPLOAD braucht deinen Account)
- Stackt mit: 1300 Bücher (Content-Quelle)
- Rechtlich: Public-Domain-Text OK, aber Musik/Bilder lizenzfrei nötig

## Empfohlener Stack (Priorität)
1. **RTD** (läuft, nur Live-Key) → sofort erster Sale möglich
2. **POD/Shirtee** (Designs generieren + Integration) → 2. Quelle
3. **Affiliate in 1300 Seiten** → passiver Bonus auf bestehenden Traffic
4. **KDP** (Digital Products) → 4. Quelle
5. **Faceless Video** (später, braucht Upload-Account)

## Was Hermes autonom vorbereiten kann (während du weg bist)
- [x] RTD-Backend + Offer-Seite (fertig)
- [ ] POD-Design-Generator (Shirtee API Skeleton)
- [ ] Affiliate-Snippet für 1300 Seiten (CTR-fähig, ohne Generator-Konflikt)
- [ ] KDP-Cover-Template-Generator

## Blockers (du)
- Live-Stripe-Key (RTD)
- Shirtee-Account (POD)
- Amazon-KDP-Account (Digital)
- Upload-Accounts (YouTube/TikTok/Affiliate-Netzwerke)
- Impressum/AGB/Gewerbe (rechtlich vor Launch)

## Rechts-Check (ADR-0030 Hard-Stop)
Alle Methoden sind SAUBER: kein Fake-Account, kein ToS-Bypass, keine IP/Steuer-
Verstöße. Einziges: Gewerbe/Impressum/AGB vor öffentlichem Launch (siehe
MANUELLE_SCHRITTE.md Punkt 3).
