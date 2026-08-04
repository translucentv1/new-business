# Ticket 8 — Widerrufs-Waiver scharfstellen (§ 356 Abs. 6 BGB)

Typ: `wayfinder:task` (HITL — zwei Voraussetzungen kann nur der Nutzer schaffen)
Status: **OPEN — BLOCKIERT**, nicht auf der Frontier
Blockiert durch: zwei USER-Blocker (siehe unten), NICHT durch ein anderes Ticket
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Entstanden aus: [Ticket 7 — Widerrufs-Zustimmung im Checkout](7-widerruf-zustimmung-checkout.md)

## Question

Wann und wie wird der Widerrufs-Waiver tatsächlich scharfgeschaltet — und lohnt
er sich überhaupt bei 3,99–14,99 € pro Sale?

## Warum blockiert (MEASURED in Ticket 7)

§ 356 Abs. 6 Nr. 2 BGB verlangt **kumulativ** a) Beginn der Vertragserfüllung,
b) ausdrückliche Zustimmung, c) Kenntnisbestätigung, d) Vertragsbestätigung nach
§ 312f BGB **auf einem dauerhaften Datenträger**. Die technische Seite von b)/c)
ist gemessen machbar, d) nicht:

| Voraussetzung | Stand | Wer kann es lösen |
|---|---|---|
| b)+c) Zustimmung im Checkout | Stripe unterstützt `consent_collection` am Payment Link, verlangt aber eine ToS-URL in den öffentlichen Geschäftsangaben. Per API **nicht** setzbar („You cannot use this method on your own account"). | **USER**, Dashboard → Settings → Public details → Terms of service URL = `https://translucentv1.github.io/new-business/agb.html` (~2 Min) |
| b)+c) Ersatzweg ohne Dashboard | dropdown-Pflichtfeld am Payment Link — von der API akzeptiert, Wert in `session.custom_fields[].dropdown.value` auslesbar | Agent (AFK), aber sinnlos ohne d) |
| d) Bestätigung auf dauerhaftem Datenträger | kein Mailversand aktiv | **USER**, `EMAIL_*` in `hermes/.env` setzen |
| Auslesen + Protokollieren der Zustimmung | **fertig** (`extract_consent`/`waiver_effective`, Selftest grün, landet in `sales.log`) | erledigt |

## Vorgehen, sobald beide USER-Blocker fallen

1. **ToS-URL gesetzt?** → `probe_consent_collection.py` erneut laufen lassen.
   Erwartung: statt der Fehlermeldung ein Link mit
   `consent_collection={"terms_of_service": "required"}`. Erst dieser Beleg
   zählt, nicht das Dashboard-Screenshot-Gefühl.
2. **Bestehende Links prüfen:** ist `consent_collection` per
   `POST /v1/payment_links/{id}` nachrüstbar, oder müssen die 3 Links neu
   gemintet werden? Wenn neu: `rtd.html` trägt die URLs hart im Markup →
   Seite mitziehen, danach `verify_rtd_chain.py` → KETTE_OK, danach
   Live-Check per curl.
3. **`auto_fulfill.py`**: die Vertragsbestätigung nach § 312f Abs. 3 muss die
   Zustimmung *wiedergeben* — die Delivery-Mail um Vertragsinhalt + die beiden
   Sätze zur Zustimmung ergänzen, nicht nur den Deliverable-Link schicken.
   Achtung § 312f Abs. 2: „spätestens … bevor mit der Ausführung begonnen wird".
4. **Erst dann** AGB § 5 umschreiben — und nur auf den dann tatsächlich
   erfüllten Stand.

## Grill-Frage vor der Umsetzung (nicht überspringen)

Bei 3,99–14,99 € pro Sale und 0 bisherigen Sales: ist ein Widerruf überhaupt ein
reales Risiko, oder ist die zusätzliche Checkout-Reibung teurer als der Schaden,
den sie verhindert? Ein Pflichtfeld mehr im Checkout eines Micro-Produkts kann
die Conversion stärker senken als jeder Widerruf kostet. **Dieses Ticket wird
nicht umgesetzt, weil es technisch geht, sondern erst wenn echte Sale-Daten
existieren, die das Risiko beziffern.** Vorher ist der ehrliche AGB-Text die
billigere Lösung.

## Definition of Done

- Entweder: alle vier Voraussetzungen erfüllt, in `sales.log` pro Sale
  `widerruf_erloschen=true` mit Beleg — und AGB § 5 entsprechend umgestellt.
- Oder: bewusst verworfen, mit Begründung aus echten Sale-Daten. Auch das
  schließt das Ticket.
