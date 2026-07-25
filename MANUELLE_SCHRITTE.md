# MANUELLE SCHRITTE — was der Nutzer (Philipp) selbst machen muss

Autonom erstellt: 2026-07-25. Hermes kann diese nicht (Rechte/Accounts/Externe Systeme).

## 🔴 KRITISCH (Sicherheit — sofort)
1. **GCP-API-Key rotieren**
   - War in `.env` (Zeilen 4 + 8) committet, von GitHub Push Protection geblockt.
   - Hermes hat ihn aus der Git-History entfernt (filter-repo, 2026-07-25).
   - ABER: der Key ist in **Googles Live-System noch gültig** (nur History gelöscht, nicht bei Google gesperrt).
   - Du: Google Cloud Console → IAM & Admin → Service Accounts → Schlüssel löschen / neu generieren.
   - Falls unklar welcher: `grep -n "GCP\|AIza" .env` (historisch) — Key begann mit `AIza...`.

## 🟠 HOCH (für ersten echten Sale nötig)
2. **Live-Stripe-Key eintragen**
   - `.stripe_secrets` hat nur `STRIPE_SECRET_KEY='***'` (Platzhalter).
   - RTD läuft im DEMO-Modus — erzeugt keine echten Payment-Links.
   - Du: echten `sk_live_...` Key aus Stripe Dashboard → `.stripe_secrets` schreiben.
   - Format: `STRIPE_SECRET_KEY=sk_live_xxx` (ohne Anführungszeichen).
   - Optional: `STRIPE_WEBHOOK_SECRET=whsec_xxx` für Webhook-Verifkation.

3. **Gewerbeanmeldung / Impressum / AGB**
   - Service-Verkauf (RTD) braucht bei Regelmäßigkeit Gewerbeschein (DE).
   - Templates liegen bereit (autonom erstellt 2026-07-26): `impressum.html` + `agb.html` (Repo-Root, gh-pages).
   - Du: Platzhalter `[DEIN NAME]`, `[EMAIL]` etc. ausfüllen, gelben TODO-Kasten + `noindex`-Meta entfernen.
   - Wichtig aus AGB §5: Widerrufs-Erlöschen-Checkbox (§ 356 Abs. 5 BGB) muss vor Launch in den Bestellprozess.
   - Erst NACH diesen Schritten öffentlich launchen.

## 🟡 MITTEL (Traffic = Engine)
4. **Traffic aufbauen** (ADR-0022 Engpass)
   - RTD + Stripe-Links + 1300 Landingpages sind da, aber 0 Besucher = 0 Sales.
   - Ideen: Social (Reddit/X/FB-Gruppen zu Study-Guides), Cross-Link auf den 1300 Seiten,
     kostenlose Begleiter + Upsell, Marktplatz (eBay/Etsy — aber du musst Account anlegen).
   - Hermes kann Landingpages bauen, aber Reichweite braucht deine Präsenz/Accounts.

## 🟢 NIEDRIG (optional)
5. **eBay/Etsy-Verkäufer-Account** (ADR-0032) — du musst ihn anlegen, dann baue ich Integration.
6. **Discord-Server** (für Preisfehler-Alert, ADR-0034) — du musst ihn verbinden.
7. **PromptBase-Account** (im Repo nicht vorhanden) — du musst Login/Auth machen.

## Status
- Repo-History: SAUBER (keine Secrets), verifiziert 2026-07-25.
- RTD-Feature: gebaut + gepusht (Commit 1405114), läuft im DEMO-Modus.
- Cron-Job RTD-Builder (87a15fe059fc): alle 2h autonom weiter, liefert an WhatsApp (origin).
