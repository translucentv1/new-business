# Ticket 23 — Kein Cron-Bericht erreicht den Nutzer (WhatsApp-Bridge tot)

Typ: `wayfinder:task` (HITL — der Fix greift in die WhatsApp-Sitzung des Nutzers ein)
Status: **OPEN**
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
