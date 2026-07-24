# ADR-0011: Kanal-Override — zurück zu Payhip (User-Entscheid)

**Datum:** 2026-07-18
**Status:** ACCEPTED (User-Override über ADR-0010 Stripe-Pivot)

## Kontext
User entschied explicit: "benutze Payhip". Stripe-Pivot (ADR-0010) wird
zurückgestellt, bleibt aber als Backup erhalten (stripe_uploader.py).

## Entscheidung
Payhip als primärer Sales-Kanal. WICHTIG (MEASURED): Payhip Public API
unterstützt NUR Coupons + License Keys — KEIN Produkt-Upload per API.
-> Produkte manuell im Payhip-Dashboard anlegen (5 Min).
-> payhip_links.py = Registry der manuell erstellten Links + HTTP-Verify
   + Sale-Tracking via Payhip Sales/License API (später, mit API-Key).

## Konsequenzen
- payhip_links.py: trägt Links aus payhip_links.json, verifiziert Erreichbarkeit
  (HTTP 200, kein API-Key), baut Landingpage-Redirects.
- Landingpages zeigen auf Payhip-Links.
- stripe_uploader.py bleibt als Backup (API-automatisierbar, DE-tauglich).
- gumroad_uploader.py: Drafts als Parkplatz, DE-Verkauf tot (PayPal-Catch-22).

## Trade-offs
- Manueller Schritt (Produkt-Anlage) vs volle API-Automatisierung bei Stripe.
- Payhip-Plattformfee (0% bei eigenem Stripe-Connect laut Help) + Stripe-Fees.
- User bevorzugt Payhip -> Override gewinnt über Effizienz-Erwägung.
