# Ticket 7 — Widerrufs-Zustimmung im Checkout einholen (§ 356 Abs. 5 BGB)

Typ: `wayfinder:task` (AFK — verändert LIVE-Stripe-Objekte)
Status: **OPEN** — auf der Frontier, sofort bearbeitbar
Blockiert durch: nichts
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Entstanden aus: [Ticket 6 — Rechtsseiten auf dem Kaufpfad](6-rechtsseiten-kaufpfad.md)

## Question

Kann die Zustimmung nach § 356 Abs. 5 BGB — „mit der Ausführung vor Ablauf der
Widerrufsfrist beginnen, Widerrufsrecht erlischt dadurch“ — im bestehenden
Stripe-Payment-Link **beweisbar** eingeholt werden, ohne die als KETTE_OK
verifizierte Kaufkette zu beschädigen?

## Ausgangslage (MEASURED 2026-08-04, Ticket 6)

Die AGB sagt seit Commit `4b6f598` die Wahrheit: die Zustimmung wird **nicht**
eingeholt, das 14-tägige Widerrufsrecht bleibt nach Lieferung bestehen.
Das ist rechtlich sauber, aber wirtschaftlich ein offenes Risiko: ein Kunde kann
das gelieferte Deliverable behalten und binnen 14 Tagen den Kaufpreis
zurückfordern. Bei 3,99–14,99 € pro Sale ist der Einzelschaden klein, das
Prinzip aber unbefriedigend, sobald Volumen entsteht.

Bestand: 3 LIVE Payment Links, je ein Custom Field `anfrage`, Redirect auf
`thanks.html?sid={CHECKOUT_SESSION_ID}`.

## Zu klären

1. **Welcher Stripe-Mechanismus trägt das?** Kandidaten:
   - `consent_collection[terms_of_service] = required` — erzeugt eine echte
     Zustimmungs-Checkbox und schreibt das Ergebnis in die Session. Setzt
     voraus, dass in den Stripe-Einstellungen eine ToS-URL hinterlegt ist
     (Kandidat: die jetzt live indexierbare `agb.html`).
   - `custom_fields` vom Typ `dropdown` als Behelf („Ja, ich stimme zu“).
   Welcher davon ist an einem **Payment Link** (nicht nur an einer
   API-erzeugten Checkout Session) tatsächlich verfügbar? Das ist der
   eigentliche Rechercheteil — nicht aus Analogie zu Checkout Sessions
   schließen, sondern gegen die Payment-Links-API prüfen.
2. **Ist die Zustimmung danach im Fulfillment auslesbar?** Nur was
   `auto_fulfill.py` aus der Session lesen und protokollieren kann, ist im
   Streitfall ein Beweis. Sonst ist die Checkbox Dekoration.
3. **Änderung oder Neuanlage?** Existierende Payment Links sind teilweise
   unveränderlich. Falls neue Links nötig sind: `rtd.html` trägt die URLs
   hart im Markup — dann muss die Seite mitgezogen werden, und
   `verify_rtd_chain.py` muss danach wieder KETTE_OK liefern.

## Definition of Done

- Checkout verlangt eine ausdrückliche Zustimmung, oder es ist belegt
  (API-Antwort, nicht Vermutung), dass das an einem Payment Link nicht geht.
- Die Zustimmung ist serverseitig auslesbar und wird bei Fulfillment geloggt.
- `verify_rtd_chain.py` → KETTE_OK, alle Links weiter `livemode/active`.
- AGB § 5 wird **erst dann** auf „Widerrufsrecht erlischt“ umgestellt, wenn
  Punkt 1 und 2 stehen. Vorher bleibt der ehrliche Text.

## Risiko

Dieses Ticket fasst die einzige funktionierende Einnahmequelle an. Vor jeder
Änderung den Ist-Zustand der Links sichern; nach jeder Änderung
`verify_rtd_chain.py`. Ein kaputter Kauf-Link kostet mehr als jedes
Widerrufsrisiko, das er verhindert.
