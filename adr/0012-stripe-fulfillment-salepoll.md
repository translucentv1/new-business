# ADR-0012: Stripe Fulfillment-Redirect + Stripe-Sale-Poll (ersetzt Gumroad-Poller)

**Status:** Angenommen · **Datum:** 2026-07-18 · **Autor:** Hermes (autonom)

## Kontext
ADR-0010 hat Stripe Payment Links als DE-Zahlungs-Rail festgelegt. ADR-0011
(Payhip-Override) ist gegenstandslos, da Stripe ohne 100$-Hürde auskommt.
Der bisherige `stripe_uploader.py` erzeugte nur Payment-Links **ohne**
Auslieferung: ein Link kassiert, liefert aber die eBook-Datei nicht aus ->
Refund/Chargeback-Risiko. Zudem pollte `sale_poller.py` Gumroad (tot).

## Entscheidung
1. **Fulfillment via `after_completion[type]=redirect`.** Jeder Payment Link
   leitet nach erfolgreicher Zahlung auf die GitHub-Pages-Landingpage des
   Buchs (`https://translucentv1.github.io/new-business/<id>/`) weiter. Diese
   Seite enthält den **vollen, gemeinfreien Buchtext** als sofort lesbares
   Deliverable (MVP-Fulfillment, kein separates Gating nötig).
   - MEASURED 2026-07-18, docs.stripe.com/api/payment-link/create +
     /payment-links/url-parameters: Feld `after_completion[redirect][url]`
     ist der dokumentierte Redirect nach Kauf; `{CHECKOUT_SESSION_ID}` ist
     optional anhängbar (hier nicht nötig, da kein personalisiertes Gating).
2. **Stripe-Sale-Poll** in `stripe_uploader.py::poll_sales()` ersetzt
   `sale_poller.py` (Gumroad). Pollt `GET /v1/charges` (paid, nicht refunded,
   amount>0), schreibt neue Sales nach `sales.log`. Lokale Instanz ohne
   öffentliche URL -> Polling statt Webhook (wie in ADR-0005 begründet).
3. **Landingpages umgebaut** (`landingpage_gen.py`): Statt Gumroad-Link jetzt
   Stripe-Kaufbutton aus `stripe_links.json`; fehlt der Link, Platzhalter
   "Bald erhältlich" (kein toter Gumroad-Link mehr).
4. **Publish-Pipeline** (`publish_site.py`): regeneriert Landingpages und
   pusht sie root-level auf `gh-pages`. Push nur, wenn ≥1 Stripe-Link existiert
   (nie Platzhalter über die Live-Site legen). `.nojekyll` hinzugefügt.

## Konsequenzen
- Positiv: Kasse + Auslieferung geschlossen; kein Gumroad-/Paypal-Catch-22.
- Risiko: MVP-Fulfillment ist eine öffentliche, lesbare Seite (kein
  Download-Gate). Da Gemeinfreiheit vorliegt, kein Lizenz-/Urheber-Problem;
  Conversion kann etwas niedriger sein als bei hartem Gate. Sauberes Gating
  (signierte URLs) ist ein späteres TB, kein Sale-Blocker.
- `sale_poller.py` (Gumroad) ist tot und wird nicht mehr genutzt.

## Belege
- docs.stripe.com/api/payment-link/create — "redirect: Redirects the customer
  to the specified url after the purchase is complete."
- docs.stripe.com/payment-links/url-parameters — "After a customer completes a
  purchase, you can redirect them to a URL ... by setting after_completion on
  the payment link."
- MEASURED: `py -3.12 scripts/test_pd_processor.py` -> 4/4 PASS (Produkt-QA).
- MEASURED: GitHub Pages bereits aktiv (`gh api repos/.../pages` ->
  html_url https://translucentv1.github.io/new-business/, build_type legacy,
  branch gh-pages). Vorher live unter docs/-Pfad mit Gumroad-Links.
