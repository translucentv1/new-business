# Ticket 30 — Zustellbarkeit der Cron-Berichte ist ungewacht

Typ: `wayfinder:task` (AFK) · Status: **GESCHLOSSEN 2026-08-11** · Priorität: hoch
Hervorgegangen aus: [Ticket 23](23-cron-zustellung-tot.md) (GESCHLOSSEN)
Nachfolger: [Ticket 31](31-alarmweg-nur-resolverseitig-belegt.md), [Ticket 32](32-waechter-ausserhalb-des-repos.md)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Antwort (MEASURED 2026-08-11)

**Die Frage war zu eng gestellt.** `deliver='origin'` + `origin=None` ist nicht
die einzige stumme Form — Stummsein ist der **Default**:

| Quelle (`cron/scheduler.py`, diesen Tick gelesen) | Befund |
|---|---|
| `_normalize_deliver_value` Z. 1237 | `deliver` fehlt/leer → **stillschweigend `'local'`** |
| `_resolve_single_delivery_target` Z. 1147 | `'local'` → `return None`, kein Ziel |
| `_deliver_result` Z. 1459 | kein Ziel + `'local'` → `return None  # not a failure` |

Damit wird **jede** Ausgabe eines `local`-Jobs verworfen, auch der Fehler-Alert
eines Laufs mit Exitcode ≠ 0.

**Zwei reale Treffer, beide aktiv, beide von allen bestehenden Toren unsichtbar:**

- `5e99ad47470f` — der **2. Ring aus Ticket 25**. Sein Skript druckt
  `*** ZWEITER RING MELDET: CRON-GESUNDHEIT DEFEKT ***`; per Konstruktion
  konnte dieser Alarm niemanden erreichen. Ein Wächter, den niemand hören kann.
- `bae39ea51a60` — AI-CEO-Loop, dessen `prompt` wörtlich `ERSTER SALE` enthält.
  Das lauteste Signal des Systems wäre in eine Logdatei geschrien worden.

**Gebaut:** `cron_delivery_audit.py` (stehendes Tor, fragt den **produktiven**
Resolver statt die Regel nachzubauen) + Etappe `[4]` in `cron_auto_fulfill.py`
mit eigenem Exitcode 5, **vor** dem SALE-Banner.

**Der geerbte Entwurf enthielt eine Behauptungs-Etappe** (Merkregel Ticket 16):
`INFO … deliver='local' - meldet **bewusst** nur auf Platte`. „Bewusst" ist eine
Absichtsunterstellung, die das Tor nicht messen kann — genau so wären beide
Treffer grün geblieben. Ersetzt durch eine aus der **Quelle des Jobs**
abgeleitete Messung (Skriptdatei bei `no_agent`, sonst `prompt`): trägt der Job
ein Alarmwort, ist fehlende Zustellung ein **Defekt**; sonst eine gezählte,
neutrale Info.

**Fix ohne neuen Lärm** (MEASURED an `run_job` Z. 2782 + `run_one_job` Z. 3833):
`[SILENT]` als erste Zeile unterdrückt die Zustellung auch bei `no_agent`-Skripten,
die Ausgabe bleibt lokal gespeichert. Der Ring meldet gesund still (alle 30 min)
und alarmiert laut — `success=False` umgeht die Unterdrückung.

**Belege:** Tor am echten System `rc 0 → 1 → 0` (beide Jobs namentlich benannt) ·
Selftest 33 → 46 (13 neue Fälle, **0 verlorene**, Labels verglichen statt Summen) ·
`_mutation_probe_t30.py` 25/25, 11 rote Mutanten, sha256-genau restauriert ·
`fix_cron_delivery_origin.py --apply` → `FIX_OK`, 15 Jobs unverändert, Rest-kaputt 0 ·
`RTD_FULFILL_OK` mit `[4] DELIVERY_OK` · `VERIFY_OK` 80 ok / 0 fail · `KETTE_OK`.

**Ehrliche Grenze:** belegt ist die **Auflösbarkeit** des Ziels, nicht die
**Ankunft** der Nachricht (→ Ticket 31). Der Wächter liegt weiterhin
unversioniert außerhalb des Repos, und `fix_cron_delivery_origin.py` ist mit
seinem zweiten Produktivlauf zum stehenden Werkzeug ohne Selftest geworden
(→ Ticket 32).

---

## Question (ursprünglich)

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
