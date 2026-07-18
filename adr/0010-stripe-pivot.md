# ADR-0010: Sales-Kanal-Pivot — Gumroad DE gesperrt → Stripe Payment Links

**Datum:** 2026-07-18
**Status:** ACCEPTED

## Kontext
Gumroad blockiert in DE das Publish für Neuseller: PayPal-Connect verlangt
"compliant + $100 earned + erste payout" (MEASURED via API + Screenshot). Stripe
ist in DE nicht bei Gumroad verfügbar. Catch-22: kein Publish ohne Payout-Methode,
kein Umsatz ohne Publish.

## Entscheidung
Primärer Sales-Kanal wird **Stripe Payment Links** (`POST /v1/payment_links`):
- DE-verfügbar, sofort kaufbar, KEIN $100-Connect-Hurdle (nur Bankdaten bei Auszahlung).
- API-erstellbar → voll autonom (ByteMe-Loop).
- Gumroad: Drafts bleiben als Parkplatz, DE-Verkauf via Gumroad vorerst tot.
- Payhip: Backup-Kanal (kein Create-API, nur manuell + License/Sales-API).

## Konsequenzen
- `stripe_uploader.py` erstellt pro Buch einen Payment Link, speichert URL in
  `stripe_links.json`. Token aus `.stripe_secrets` (gitignored), kein Hard-Stop-Bruch.
- Landingpages zeigen auf Stripe-Links (nicht Gumroad).
- Sale-Poller erweitert um Stripe-Charge-Polling (später).
- User muss EINMAL: Stripe-Account + API-Key (in `.stripe_secrets`) — sonst wie Gumroad.

## Trade-offs
- Stripe-Fees (EEA 1.5%+0.25€ + 0% Plattform) vs Gumroad 10%. Besser für Marge.
- Manueller Gumroad-Weg entfällt komplett für DE-Erstverkauf.
