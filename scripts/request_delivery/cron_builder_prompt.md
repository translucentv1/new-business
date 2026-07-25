Baue autonom am Request-to-Delivery-Feature in scripts/request_delivery/.

Naechste Schritte (einen pro Tick, der noch Sinn ergibt):
1. Webhook-Verifkation (HMAC via STRIPE_WEBHOOK_SECRET) + Fulfillment-Trigger ergaenzen: bei Paid -> generator.generate(request) -> deliverable speichern + Status auf fulfilled.
2. Angebots-Landingpage (index.html) ins Repo bauen + Cross-Link von bestehenden 1300 Seiten.
3. Impressum/AGB-Template (rechtlich vor oeffentlichem Launch noetig).

Belegpflicht: MEASURED (HTTP-Test, Dateiinhalt, keine erfundenen Keys).
Stopp wenn Live-Stripe-Key fehlt und nur DEMO moeglich ist.

Kurzer deutscher Statusbericht am Ende: was/Beleg/naechster Schritt.
