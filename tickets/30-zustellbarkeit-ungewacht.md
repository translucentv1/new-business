# Ticket 30 — Zustellbarkeit der Cron-Berichte ist ungewacht

Typ: `wayfinder:task` (AFK) · Status: **OFFEN** · unblockiert · Priorität: hoch
Hervorgegangen aus: [Ticket 23](23-cron-zustellung-tot.md) (GESCHLOSSEN)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

Ticket 23 hat 4 unzustellbare Cron-Jobs repariert — darunter den Geldpfad-Träger
mit der `*** ERSTER SALE ***`-Meldung. Repariert ist ein **Zustand**, nicht die
**Eigenschaft**. Was hindert den nächsten neu angelegten Job daran, wieder mit
`deliver='origin'` und `origin=None` zu entstehen und still an `whatsapp:self`
zu senden?

Antwort heute: **nichts**. Genau dieselbe Klasse wie Ticket 24 („ein Tor, das
niemand öffnet, ist kein Tor"), nur auf den Meldeweg statt auf die Lieferung.

## Warum das teuer ist

Der Defekt ist **unsichtbar für alle bestehenden Tore**. Er macht keinen Job
`failed`: die Arbeit läuft durch, das Ergebnis landet in
`$HERMES_HOME/cron/output/`, nur der Nutzer erfährt nichts. `cron_health_audit`
prüft, ob der Geldpfad **läuft** — nicht, ob sein Ergebnis **ankommt**.
Zwischen „Kunde hat bezahlt" und „Betreiber weiß davon" liegt damit weiter eine
ungewachte Etappe.

Faktenlage bei Ticket-23-Abschluss (MEASURED, `_probe_t23_inventory.py`):
4 von 15 Jobs waren betroffen, davon 2 enabled + auf dem Geldpfad relevant.

## Vorgehen

1. `_probe_t23_inventory.py` (Ad-hoc-Sonde) zu einem **stehenden Tor** ausbauen:
   `cron_delivery_audit.py`, Zielmenge **aus `jobs.json` abgeleitet** (nicht
   hartkodiert), Ergebniswörter `DELIVERY_OK` / `DELIVERY_DEFEKT` (rc=1) /
   `DELIVERY_UNGEPRUEFT` (rc=2, z. B. `jobs.json` unlesbar). **Leere Zielmenge
   ist nicht grün** (Leere-Schleife-Falle, Ticket 16).
2. `--selftest` mit Fault Injection durch die **echte** `main()`; Rot-Fälle
   gegen die **exakte** Diagnosezeile assertieren (Ticket 17), gegen
   `Traceback` filtern (Exit-Code-Falle).
3. Mutationsprobe gegen den Produktivcode, sha256-genaue Wiederherstellung,
   rc-Wechsel 0→1→0 belegen.
4. Als Etappe in `cron_auto_fulfill.py` einhängen — **ohne** das SALE-Banner
   hinter eine Verzweigung zu schieben (Beinahe-Regression aus Ticket 24) und
   mit eigenem Signalwert, weil ein Melde-Defekt kein Liefer-Defekt ist
   (Ticket 27: Trennung nach Betroffenem, `rc=4`-Klasse prüfen).

## Nicht vergessen (ASSUMED, vor dem Beantworten nachmessen)

- **Positivkontrolle:** ein Melde-Tor, das nur „0 kaputt" ausgeben kann, ist nie
  beim Zählen beobachtet worden (Ticket 15). Der Selftest muss einen Job mit
  `origin=None` **erkennen**, nicht nur die gesunde Lage durchwinken.
- Ob `deliver='origin' + origin=None` die **einzige** unzustellbare Form ist,
  ist unbelegt. Denkbar: `origin` vorhanden, aber mit toter `chat_id`; oder ein
  anderer `platform`-Wert. Gegen die realen Feldwerte in `jobs.json` messen,
  nicht gegen die Vorstellung davon.
- Die drei in Ticket 23 mitreparierten Nicht-Geldpfad-Jobs sind **nicht
  einzeln** als zustellend gemessen. Ein echter Lauf je Job wäre der Beleg.
- Der Fixer `fix_cron_delivery_origin.py` hat **keinen** `--selftest`. Einordnen:
  einmaliger Reparaturlauf (Ad-hoc, braucht keinen) oder stehendes Werkzeug
  (braucht einen)? Ticket 15 verlangt die Einordnung, nicht das Bauchgefühl.
