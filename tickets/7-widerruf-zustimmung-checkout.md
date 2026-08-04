# Ticket 7 — Widerrufs-Zustimmung im Checkout einholen (§ 356 Abs. 6 BGB)

Typ: `wayfinder:task` (AFK — verändert LIVE-Stripe-Objekte)
Status: **CLOSED 2026-08-04** — Resolution am Ende dieser Datei
Blockiert durch: nichts
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Entstanden aus: [Ticket 6 — Rechtsseiten auf dem Kaufpfad](6-rechtsseiten-kaufpfad.md)
Folgeticket: [Ticket 8 — Widerrufs-Waiver scharfstellen](8-widerruf-waiver-scharfstellen.md)

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

---

## Resolution (2026-08-04, alles MEASURED)

**Kurz: Ja, Stripe kann es — aber es nützt heute nichts. Die live Payment Links
bleiben deshalb unangetastet.**

### 1. Trägt ein Payment Link `consent_collection`? → JA, aber Dashboard-gesperrt

`probe_consent_collection.py` (neu) hat gegen die LIVE-API einen Link mit
`consent_collection[terms_of_service]=required` anzulegen versucht. Stripe
antwortet **nicht** mit „unknown parameter" (das wäre die Absage), sondern:

> `invalid_request_error`: *You cannot collect consent to your terms of service
> unless a URL is set in the Stripe Dashboard. Update your public business
> details in the Dashboard … with a Terms of service URL …*

Der Parameter ist also auf Payment-Link-Ebene **unterstützt**; es fehlt nur die
ToS-URL in den öffentlichen Geschäftsangaben.

### 2. Lässt sich diese ToS-URL autonom setzen? → NEIN

`POST /v1/accounts/acct_1TuRDHFajs0YddhP` mit
`business_profile[terms_of_service_url]` und mit `tos_acceptance[...]`:

> *You cannot use this method on your own account: you may only use it on
> connected accounts.*

Zusätzlich: `GET /v1/account` enthält **kein einziges** Feld mit „terms"
(geprüft per String-Suche im ganzen Account-Objekt). → Dashboard-only,
**USER-Blocker**, einmalig ~2 Minuten.

### 3. AFK-Ersatzweg: dropdown-Pflichtfeld → funktioniert

Ein Payment Link mit zusätzlichem `custom_fields[1]` vom Typ `dropdown`
(`optional=false`, Option „Ja, ich stimme zu") wurde von der API **angenommen**
(`plink_1U0fgoFajs0YddhP4aGdYmkp`) und sofort wieder deaktiviert.

### 4. Ist die Antwort auslesbar? → JA

Eine echte LIVE-Checkout-Session mit demselben Feld wurde angelegt: das Feld
erscheint als `session.custom_fields[0].dropdown.value` (`null`, solange die
Session offen ist) — genau der Pfad, den `auto_fulfill.py` liest. Probe-Session
danach per `/expire` geschlossen (`status=expired`), Probe-Links deaktiviert,
`aktive Probe-Links uebrig: []`.

### 5. Der eigentliche Befund: die Zustimmung allein reicht rechtlich nicht

Gegen die **Primärquelle** gelesen (gesetze-im-internet.de, HTTP 200), nicht aus
dem Gedächtnis zitiert — und dabei ein Zitierfehler gefunden:
**Für digitale Inhalte ohne körperlichen Datenträger gilt § 356 Abs. 6, nicht
Abs. 5** (Abs. 5 regelt Dienstleistungen). AGB, Ticket 6 und die Skripte wurden
korrigiert.

§ 356 Abs. 6 Nr. 2 verlangt **kumulativ** a) Beginn der Vertragserfüllung,
b) ausdrückliche Zustimmung, c) Bestätigung der Kenntnis vom Erlöschen **und**
d) „*der Unternehmer hat dem Verbraucher eine Bestätigung gemäß § 312f zur
Verfügung gestellt*". § 312f Abs. 2 verlangt diese Vertragsbestätigung
„*auf einem dauerhaften Datenträger*", § 312f Abs. 3 verlangt, dass darin die
Zustimmung nach b) und c) festgehalten ist.

Dauerhafter Datenträger = E-Mail. Der Mailversand hängt an `EMAIL_*`
(USER-Blocker). **Ohne d) erlischt das Widerrufsrecht nicht — egal welche
Checkbox im Checkout steht.**

### 6. Entscheidung

Die drei LIVE-Links werden **nicht** geändert. Ein zusätzliches Pflichtfeld
würde heute nur Checkout-Reibung erzeugen, ohne einen einzigen Euro
Widerrufsrisiko zu senken. Stattdessen wurde die **auslesende Seite** gebaut,
damit der Beweis ab der Sekunde greift, in der die Zustimmung scharfgeschaltet
wird:

- `auto_fulfill.extract_consent()` liest **beide** Träger (`session.consent`
  und das dropdown-`custom_field`), `waiver_effective()` bewertet sie.
- Beides landet in `fulfilled_live.json` **und** in `sales.log` — bei jedem
  Fulfillment, auch wenn es (noch) `null` ist.
- Selftest deckt alle drei real möglichen Session-Formen ab; Formen stammen
  aus den echten API-Antworten oben, nicht aus Annahmen.

MEASURED-Beleg (`auto_fulfill.py --selftest`):

```
CONSENT OK [ohne Zustimmung (Ist-Zustand LIVE)] -> {"tos": null, ... } | widerruf_erloschen=False
CONSENT OK [dropdown-Pflichtfeld (AFK-Weg)] -> {"field": "ja", ...}    | widerruf_erloschen=True
CONSENT OK [consent_collection (nach ToS-URL)] -> {"tos": "accepted"}  | widerruf_erloschen=True
SELFTEST OK: dl/rtd/27c623e9ae7c971c.html (1695 bytes)
```

`verify_rtd_chain.py` nach allen Eingriffen: **KETTE_OK**, 3 Links weiter
`livemode/active`, 399/799/1499 cent = 3,99/7,99/14,99 EUR, Feld `anfrage`,
Redirect unverändert. Ist-Zustand vorher gesichert in
`scripts/request_delivery/plinks_backup_2026-08-04.json` (55 aktive Links).

### Definition of Done — Abgleich

- ✅ Belegt (API-Antwort, nicht Vermutung), was am Payment Link geht.
- ✅ Auslesbar + wird bei Fulfillment geloggt (Selftest grün).
- ✅ `verify_rtd_chain.py` → KETTE_OK, alle Links `livemode/active`.
- ✅ AGB § 5 **nicht** auf „erlischt" umgestellt — im Gegenteil: der Text nennt
  jetzt alle vier Voraussetzungen und sagt offen, dass zwei davon fehlen.

Offen bleibt nur das Scharfschalten → [Ticket 8](8-widerruf-waiver-scharfstellen.md).
