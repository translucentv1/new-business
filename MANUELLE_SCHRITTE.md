# MANUELLE SCHRITTE — Klick-fertige Checkliste

Autonom vorbereitet: 2026-07-25. Alles ist ready, du musst nur noch Klicks machen.
Geschätzte Zeit: ~20 Min für die kritischen Punkte (1-3), dann läuft der erste Sale.

---

## 🔴 1. GCP-API-Key rotieren (SICHERHEIT — 2 Min)
Der Key in der alten `.env` war echt. Hermes hat ihn aus der Git-History gelöscht,
aber er ist bei Google noch LIVE.

- Gehe zu: https://console.cloud.google.com/apis/credentials
- Linker Balken: **APIs & Services → Credentials**
- Finde den Key, der mit `AIza...` beginnt (war in `.env` Zeile 4 oder 8)
- Klicke auf ihn → **Löschen** (oder neu generieren + alten löschen)
- Fertig. Danach ist der alte Key wertlos.

✅ Checkbox: [ ] GCP-Key bei Google gelöscht/neu generiert

---

## 🟠 2. Live-Stripe-Key eintragen (2 Min)
RTD läuft im DEMO-Modus, bis hier ein `sk_live_`-Key steht.

- Datei bereits vorbereitet: `C:\Users\phili\new-business\.stripe_secrets`
- Öffne sie, ersetze `sk_liv...ga3P` (Platzhalter) mit deinem vollständigen `sk_live_`-Key (ca. 32–40 Zeichen, nicht gekürzt)
- Key holen: https://dashboard.stripe.com/apikeys → **Secret key** (zeigen + kopieren)
- Speichern. Fertig — RTD erzeugt jetzt echte Payment-Links.

✅ Checkbox: [ ] `.stripe_secrets` hat echten `sk_live_`-Key
✅ Checkbox: [ ] (Optional) `STRIPE_WEBHOOK_SECRET` eingetragen

---

## 🟠 3. Impressum / AGB / Gewerbe (10 Min, vor öffentlichem Launch)
Service-Verkauf braucht das rechtlich sauber.

- **Gewerbe anmelden:** https://www.gewerbeanmeldung.de/ (oder lokales Ordnungsamt)
  → "Kleingewerbe" reicht für den Start (bei geringem Einkommen)
- **Impressum + AGB:** Platzhalter sind schon in `rtd.html` + `scripts/request_delivery/index.html`
  → Ersetze `[DEIN NAME]`, `[STRASSE]`, `[PLZ ORT]`, `[EMAIL]` mit echten Daten
  → AGB-Template: z.B. https://www.e-recht24.de/ (kostenlose Vorlage für Kleinunternehmer)
- **Umsatzsteuer:** Als Kleinunternehmer (§19 UStG) keine USt ausweisen nötig → einfacher Start

✅ Checkbox: [ ] Gewerbe angemeldet (oder Kleinunternehmer-Regelung geprüft)
✅ Checkbox: [ ] Impressum in `rtd.html` ausgefüllt
✅ Checkbox: [ ] AGB verlinkt

---

## 🟡 4. Traffic aufbauen (laufend — deine Accounts)
RTD + 1300 Seiten + Stripe-Links sind da, aber 0 Besucher = 0 Sales.

**Schnellste Hebel (du musst Account haben):**
- **Reddit:** r/studyguides, r/languagelearning, r/writing — hilfreiche Antworten + Link zu `rtd.html`
- **X/Twitter:** Threads zu "KI Lese-Begleiter" + Link
- **Pinterest:** Covers der 1300 Bücher pinnen → Link zur Buy-Box
- **TikTok/Faceless YouTube:** AI-narrated Book-Summaries (0 Invest, aber dein Upload)

**Was Hermes autonom vorbereitet hat:**
- `rtd.html` ist live auf gh-pages (https://translucentv1.github.io/new-business/rtd.html)
- Cross-Link-Plan in `GELD_STACKING.md` (Affiliate in 1300 Seiten)

✅ Checkbox: [ ] Mind. 1 Traffic-Kanal gestartet

---

## 🟢 5. Weitere Accounts (optional, für mehr Stacking)
- **eBay/Etsy:** Verkäufer-Account für ADR-0032 (Business #2) — du musst anlegen, dann baue ich Integration
- **Discord:** Server für Preisfehler-Alert (ADR-0034) — du verbindest, dann baue ich Bot
- **PromptBase:** Login/Auth (im Repo nicht vorhanden) — du machst, dann publish ich Listings

---

## Status
- Repo: SAUBER (0 Secrets, verifiziert 2026-07-25)
- RTD-Feature: gebaut + gepusht, Fulfillment-Flow MEASURED (Order → Webhook → fulfilled)
- Cron RTD-Builder (87a15fe059fc): alle 2h autonom, liefert an WhatsApp
- `.stripe_secrets`: vorbereitet, wartet auf Live-Key
- `rtd.html`: live, wartet auf Traffic
