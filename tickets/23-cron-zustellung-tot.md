# Ticket 23 — Kein Cron-Bericht erreicht den Nutzer (WhatsApp-Bridge tot)

Typ: `wayfinder:task` (war als HITL geführt — **Prämisse falsifiziert**, siehe
Resolution: der Fix war AFK und hat die WhatsApp-Sitzung nie berührt)
Status: **GESCHLOSSEN 2026-08-11** — Resolution am Ende dieser Datei
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Hervorgegangen aus: [Ticket 22](22-liefer-cron-tot.md)

## Question

Die Auslieferung an den **Nutzer** (Statusberichte, und im Ernstfall die
Sale-Meldung) läuft über die WhatsApp-Bridge. Die ist defekt. Soll der
Zustellweg gewechselt werden — und auf welchen?

## Befund (MEASURED 2026-08-06)

`hermes cron list`: **jeder** Job mit einem Zustellziel meldet

```
⚠ Delivery failed: delivery error: WhatsApp bridge error (500):
  {"error":"Cannot destructure property 'user' of 'jidDecode(...)' as it is undefined."}
```

betroffen u. a. `bfb63346d942` (RTD Auto-Fulfill), `87a15fe059fc` (RTD-Builder),
`8c7afca842ac` (Abend-Report), `a564ec4d11ea` (Selbstverbesserungs-Pass).
`grep -c jidDecode logs/gateway-stdio.log` → **68** Treffer im aktuellen Log.
Systemweit, nicht ein einzelner kaputter Job (bekannte Klasse, siehe Skill
`hermes-cron-jobs` § 3: der JID-Resolver ist nach einem Bridge-Reconnect stale).

**Wirkung:** Die Arbeit läuft, die Ergebnisse landen in
`$HERMES_HOME/cron/output/<job>/*.md` — aber der Nutzer bekommt **nichts**
zugestellt. Auch die laute „ERSTER SALE"-Meldung aus `cron_auto_fulfill.py`
würde heute nicht ankommen.

## Warum kein Cron-Tick das eigenmächtig repariert

Der dokumentierte Fix ist ein Gateway-Neustart (`hermes gateway restart`), damit
die Bridge den JID-Resolver neu aufbaut. Ein Tick läuft **innerhalb** des
Gateway-Prozesses — ein Neustart von hier aus SIGTERMt den eigenen Elternprozess
und bricht den laufenden Tick ab. Muss aus einer **frischen Shell** kommen.

## Optionen für den Nutzer

1. `hermes gateway restart` aus einer separaten Shell — behebt die Ursache,
   trifft aber alle Kanäle gleichzeitig.
2. Zustellziel je Job auf `local` stellen (Bericht nur noch als Datei unter
   `$HERMES_HOME/cron/output/`) — verliert die Push-Benachrichtigung, beendet aber
   die Fehlerflut.
3. Anderer Kanal (Telegram/Mail) — braucht Zugangsdaten, also ohnehin Nutzer.

## Entscheidung, die daran hängt

Ohne funktionierenden Kanal ist die Sale-Meldung nur noch in `sales.log` und in
den Cron-Ausgabedateien sichtbar. Das ist kein Blocker für den Verkauf selbst
(die Auslieferung an den **Kunden** läuft unabhängig davon, siehe Ticket 22),
aber der Nutzer erfährt den ersten Sale dann nicht aktiv.

## Nebenbefund (MEASURED, eigener kleiner Defekt)

Job `a564ec4d11ea` („Selbstverbesserungs-Pass") ist **doppelt tot**: er wird seit
dem Modellwechsel per Spend-Protection übersprungen (7 Läufe, 0 completed), und
sein hinterlegtes Skript `self_improve_pass.py` existiert **weder** in
`$HERMES_HOME/scripts/` **noch** im Repo. Eine reine
Umstellung auf `--no-agent` würde ihn also nicht retten. Nicht Geldpfad,
deshalb hier nur protokolliert.

**Beleg 2026-08-06 nachgezogen (der ursprüngliche war am falschen Pfad gemessen):**
Die erste Fassung dieses Befunds prüfte `~/.hermes/scripts/` — dieses Verzeichnis
existiert gar nicht (`HERMES_HOME=C:\Users\phili\AppData\Local\hermes`, siehe
Pfad-Falle in Ticket 22). Am **echten** Pfad neu gemessen: `self_improve_pass.py`
fehlt dort ebenfalls (`ls` → No such file), und `find . -name self_improve_pass.py`
im Repo ist leer. **Die Schlussfolgerung hält also — die Begründung war es nicht.**
Nebenbefund dabei: unter `$HERMES_HOME/scripts/` liegt ein ähnlich benanntes
`newbiz_self_improve.py`. Der Job zeigt damit vermutlich schlicht auf einen
falschen Dateinamen; das ist eine Ein-Zeilen-Korrektur am Job, aber sie gehört
dem Nutzer (kein Geldpfad, und der Job wäre ohne `--no-agent` weiterhin tot).

---

## Resolution (2026-08-11, MEASURED)

**Die Ticket-Überschrift war falsch: die WhatsApp-Bridge ist NICHT tot.**
Der dokumentierte Fix (Gateway-Neustart aus frischer Shell — der Grund für das
HITL-Etikett) hätte gar nichts repariert: er behandelt eine Ursache, die es
nicht gibt.

### Gegenbeweis zur Prämisse

Im selben `gateway-stdio.log`, das 98 `jidDecode`-Fehler trägt, stehen
**9 erfolgreiche Zustellungen**, die letzten unmittelbar vor diesem Tick:

    Job '3e7e333151b0': delivered to whatsapp:8511...@lid via live adapter

Eine tote Bridge stellt nicht achtmal hintereinander zu. Der Unterschied liegt
nicht am Kanal, sondern **am Job**.

### Echte Ursache (vollzählig klassifiziert, nicht per Stichprobe)

`_probe_t23_inventory.py` klassifiziert **alle 15** Jobs in `jobs.json`:

    KAPUTT (4)      deliver='origin' + origin=None
      a564ec4d11ea  Selbstverbesserungs-Pass
      87a15fe059fc  RTD-Builder            <- die Tick-Berichte selbst
      8c7afca842ac  Abend-Report 22Uhr
      bfb63346d942  RTD Auto-Fulfill       <- GELDPFAD, trägt "ERSTER SALE"
    ZUSTELLBAR (2)  deliver='origin' + origin-Block vorhanden
    LOKAL (9)       deliver='local' (keine Zustellung gewollt)
    SONSTIGES (0)

Bei `deliver='origin'` **ohne** `origin`-Block fällt der Scheduler auf den
„whatsapp home channel" zurück und schickt wörtlich an `whatsapp:self`.
`jidDecode('self')` ist `undefined` → die Bridge antwortet korrekt mit HTTP 500.
Der 500er war also nie ein Bridge-Defekt, sondern eine **unauflösbare
Empfängeradresse**.

### Fix (AFK, ohne Neustart, ohne Eingriff in die WhatsApp-Sitzung)

`scripts/request_delivery/fix_cron_delivery_origin.py`: überträgt den
origin-Block eines **nachweislich zustellenden** Jobs auf die kaputten. Kein
Ziel erfunden, keine Zugangsdaten im Code (die Adresse wird zur Laufzeit aus
`jobs.json` gelesen und im Output gekürzt), Backup vor dem Schreiben,
Gegenlesen danach (Job-Anzahl unverändert, Rest-Kaputt = 0), Rollback bei
Abweichung. Default ist `--dry-run`.

### Beleg: derselbe Job, derselbe Kanal, vorher/nachher

    2026-08-10 21:56:12  ERROR  bfb63346d942: WhatsApp bridge error (500) jidDecode
    2026-08-10 22:27:14  ERROR  bfb63346d942: WhatsApp bridge error (500) jidDecode
    2026-08-10 22:58:15  ERROR  bfb63346d942: WhatsApp bridge error (500) jidDecode
    --- Fix 23:58:28  FIX_OK, Backup jobs.json.bak-t23-20260810-235828 (27394 B) ---
    2026-08-10 23:58:50  INFO   bfb63346d942: delivered to whatsapp:8511...@lid

Drei Fehlschläge in Folge, dann ein Erfolg — nicht argumentiert, sondern durch
einen echten Job-Lauf erzeugt (`hermes cron run bfb63346d942` → „Ran now:
succeeded").

### Was NICHT als Beleg zählt

`last_delivery_error = None` ist **kein** Erfolgsbeweis: der Fix setzt dieses
Feld selbst zurück, und ein Lauf ohne Zustellversuch ließe es ebenfalls leer.
Gezählt hat nur die positive Zeile `delivered to …` in `agent.log`.
Der `gateway-stdio.log` bekam **0** neue Zeilen — `hermes cron run` läuft im
CLI-Prozess, nicht im Gateway. Wer nur dort gesucht hätte, hätte den Erfolg für
„nichts passiert" gehalten.

### Wirkung

Der lauteste Kanal des Systems war stumm: die `*** ERSTER SALE ***`-Meldung des
Geldpfad-Trägers ist **nie** beim Nutzer angekommen, ebensowenig die
Tick-Berichte des RTD-Builders. Der Verkauf selbst war nie betroffen (die
Kunden-Auslieferung läuft unabhängig, Ticket 22) — der erste Sale wäre aber nur
in `sales.log` sichtbar gewesen.

### Ehrliche Grenze

Belegt ist **eine** erfolgreiche Zustellung des Geldpfad-Trägers. Dass die
übrigen drei reparierten Jobs zustellen, ist strukturell gleich begründet, aber
nicht einzeln gemessen. Und nichts hält einen künftig angelegten Job davon ab,
wieder mit `origin=None` zu entstehen — diese Stelle ist ungewacht (→ Ticket 30).
