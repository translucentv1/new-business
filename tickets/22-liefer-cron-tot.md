# Ticket 22 — Läuft der Liefer-Cron wirklich?

Typ: `wayfinder:task` (AFK)
Status: **CLOSED** (2026-08-06)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

`agb.html` § 3 verspricht Lieferung binnen 24 h. Diese Zusage stützt sich laut
Ticket 6 auf „den 2-h-Cron". Dass dieser Cron die Fulfillment-Pipeline
tatsächlich startet, war **nie gemessen** — es war eine Annahme über die
Infrastruktur, während alle bisherigen Tickets den Code im Repo prüften.

## Antwort (MEASURED 2026-08-06)

**Der Liefer-Cron hat in seiner gesamten Lebenszeit kein einziges Mal
gelaufen.** Nicht „selten", nicht „mit Aussetzern" — nie.

Beleg aus `$HERMES_HOME/cron/executions.db` (Job `bfb63346d942`,
„RTD Auto-Fulfill (Stripe → Deliverable → Push)"):

```
status   |Anzahl| von                        bis
failed   | 143  | 2026-07-30T00:39:23+02:00  2026-08-06T04:34:47+02:00
unknown  |   1  | 2026-07-31T15:01:05+02:00
completed|   0  | —
```

Zwei Fehlerklassen, beide unabhängig von diesem Repo:

| Anzahl | ab | Fehler |
|---|---|---|
| 7 | 2026-07-30T00:39 | `RuntimeError: HTTP 404` (Modell weg) |
| 135 | 2026-07-30T15:14 | `Skipped to prevent unintended spend: global inference config drifted … this job is unpinned. No inference call was made.` |
| 1 | 2026-07-31T19:02 | `getaddrinfo failed` (Netz) |

Der Job war ein **agentengetriebener** Job (`script: null`, `no_agent: false`):
er brauchte einen LLM-Call, um anschließend `auto_fulfill.py` per Shell zu
starten. Nach dem globalen Modellwechsel (`nous/hermes-3-llama-3-8b` →
`tencent/hy3:free`) griff die Spend-Protection und übersprang ihn — 135-mal
in Folge, ohne dass irgendetwas im Repo davon rot wurde.

**Wirkung:** Die einzige automatische Auslieferung bezahlter Ware existierte
nicht. Ein Kunde hätte sein Deliverable nur bekommen, wenn zufällig ein
RTD-Builder-Tick (`87a15fe059fc`) lief — und der ist selbst unzuverlässig
(MEASURED: 27 completed / 20 failed, aktuell HTTP 429 Rate-Limit). Die
24-h-Zusage in § 3 AGB war damit **vertraglich ungedeckt**.

Warum es nie auffiel: Alle bisherigen Prüfer messen das **Repo** (Code,
Sitemap, Live-Auslieferung). Der Scheduler ist **außerhalb** des Repos —
kein einziger Prüfer hat je in `executions.db` geschaut. Dieselbe Klasse wie
die Branch-Falle (Ticket 4) und die Origin-`robots.txt` (Ticket 20): der
geprüfte Ort war nicht der wirksame Ort.

## Fix

Die Auslieferung bezahlter Ware darf nicht von Modellverfügbarkeit,
Config-Drift oder Rate-Limits abhängen. Der Job braucht **keinen** LLM:
`auto_fulfill.py` erzeugt lokal per Ollama ($0) und pusht per git.

1. **`scripts/request_delivery/cron_auto_fulfill.py` (NEU, im Repo):** startet
   die echte Pipeline, reicht deren Ausgabe durch, prüft danach den Kaufpfad
   live. Drei-Wege-Konvention wie Ticket 16/17/19 plus ein viertes Wort für
   den Sale-Fall:
   `RTD_FULFILL_OK` (0) · `RTD_FULFILL_SALE` (0) · `RTD_FULFILL_DEFEKT` (1) ·
   `RTD_FULFILL_UNGEPRUEFT` (2). Echter Defekt schlägt Unmessbarkeit.
2. **`$HERMES_HOME/scripts/rtd_auto_fulfill.py`** ist nur noch ein Loader auf die
   Repo-Datei — zwei Kopien würden auseinanderdriften.
3. Job umgestellt: `--script rtd_auto_fulfill.py --no-agent
   --workdir C:/Users/phili/new-business`. Damit ist **kein Inferenz-Call mehr
   beteiligt**, die Spend-Protection kann nicht mehr greifen und ein 429 kann
   die Lieferung nicht mehr blockieren.

## Belege (MEASURED)

- `cron_auto_fulfill.py --selftest` → **SELFTEST OK: 14/14** (Fault Injection
  durch die **echte** `main()`; nur `FULFILL`/`http_code`/`TIMEOUT` werden
  ersetzt). Abgedeckt: Sale über `neu=N`, Sale über `FULFILLED cs_live`,
  `neu=0` ist **kein** Sale, Pipeline-rc≠0, 404/500 auf dem Kaufpfad,
  Netzfehler → UNGEPRUEFT, Defekt schlägt Unmessbarkeit, fehlendes Skript,
  Timeout, Durchreichen der Pipeline-Ausgabe. Ergebniswort wird als
  **exaktes erstes Token** verglichen (Ticket-19-Merkregel).
- Erster echter Job-Lauf nach der Umstellung: `hermes cron run bfb63346d942`
  → „Ran now: succeeded", `executions.db` → **`completed`** (der **erste**
  in 145 Läufen), Ausgabedatei `2026-08-06_05-05-16.md` mit
  `**Mode:** no_agent (script)` und der echten Pipeline-Ausgabe
  `sessions=2 (roh, inkl. Eigentests) paid=0 neu=0`, `rtd.html HTTP 200`,
  `thanks.html HTTP 200`, `ERGEBNIS: RTD_FULFILL_OK`.
- **Rot-Fähigkeit auf Job-Ebene belegt** (sonst wäre „completed" ein
  ungeprüftes Signal — Ungeprüft-Prüfer-Falle): Job kurzzeitig auf eine Sonde
  mit `sys.exit(1)` gezeigt → `Ran now: failed`, DB-Zeile `failed` mit
  `Script exited with code 1 / stdout: RC_PROBE_MARKER…`; danach zurückgestellt
  → wieder `completed`. **rc-Wechsel 0 → 1 → 0.** Sonde gelöscht,
  `jobs.json` zeigt `script=rtd_auto_fulfill.py, no_agent=True,
  last_status=ok, last_error=None`.

## Ehrliche Grenzen

- Gemessen ist, dass der Job **startet und grün endet**, und dass die Pipeline
  bei 0 bezahlten Sessions korrekt nichts tut. Eine echte Auslieferung an einen
  echten Kunden ist weiterhin nie passiert (0 Sales) — die Publish-Etappe
  selbst ist separat durch Ticket 11/20 (`verify_publish_leg.py`, Canary durch
  die Produktivfunktionen) belegt.
- Der Job liefert seinen Bericht weiterhin **nicht** an den Nutzer aus:
  `last_delivery_error` = WhatsApp-Bridge 500 (`jidDecode`). Auch ein lautes
  „ERSTER SALE" käme derzeit nicht an → **Ticket 23**.
- Der Zeitraum 30.07.–06.08. ist damit als Lieferausfall belegt. Folgenlos nur,
  weil es in diesem Zeitraum **0 bezahlte Sessions** gab (funnel_check:
  BESUCHER=0, EIGENTEST=2).

## Nachverifikation 2026-08-06 07:20 (MEASURED, unabhängiger Tick)

Ticket 22 belegte nur einen **manuell** ausgelösten Lauf (`hermes cron run`).
Dass der Job **von selbst, nach Plan** feuert, war damit noch offen — genau der
Punkt, an dem die 24-h-Zusage hängt. Jetzt gemessen, `executions.db`:

```
05:04:48  failed     <- letzter LLM-getriebener Lauf (Spend-Protection)
05:05:15  completed  <- manueller Lauf aus Ticket 22
05:12:51  failed     <- Rot-Sonde (absichtlich)
05:13:31  completed  <- zurueckgestellt
05:46:50  completed  \
06:16:55  completed   |  4 aufeinanderfolgende PLANMAESSIGE Laeufe,
06:47:52  completed   |  unbeaufsichtigt, ohne Inferenz-Call
07:17:57  completed  /
```

Gesamtbilanz des Jobs: **6 completed / 144 failed / 1 unknown** — alle 6
completed liegen nach dem Fix, davor 0 in 145 Läufen.

Inhalt statt Statuscode geprüft (Merkregel Ticket 20), Ausgabedatei
`2026-08-06_07-17-59.md`: `Mode: no_agent (script)`,
`sessions=2 (roh, inkl. Eigentests) paid=0 neu=0`, `rtd.html HTTP 200`,
`thanks.html HTTP 200`, `ERGEBNIS: RTD_FULFILL_OK`. Der Lauf hat also die
echte Pipeline gefahren, nicht nur rc=0 zurückgegeben.
`cron_auto_fulfill.py --selftest` neu ausgeführt: **14/14**.

## Pfad-Falle (in diesem Ticket selbst gefunden)

Dieses Ticket schrieb den Hermes-Pfad als `~/.hermes/…`. **Das ist nicht der
wirksame Ort.** MEASURED: `HERMES_HOME=C:\Users\phili\AppData\Local\hermes`;
der Loader liegt unter `$HERMES_HOME/scripts/rtd_auto_fulfill.py` (766 B).
`~/.hermes/` **existiert zwar**, enthält aber nur `whatsapp/` — ein `ls` auf
den falschen Pfad liefert deshalb ein plausibles „No such file" statt eines
Fehlers. Der Nachverifikations-Tick ist genau darauf hereingefallen und hätte
beinahe „Loader fehlt" als Defekt gemeldet.

Merke: **Hermes-Pfade immer über `$HERMES_HOME` ansprechen, nie über `~/.hermes`.**
Dieselbe Klasse wie die Branch-Falle (Ticket 4) und der Origin-`robots.txt`
(Ticket 20) — nur diesmal beim *Messen* statt beim *Ausliefern*.

## Merkregel

**Ein Prüfer, der nur das Repo kennt, sieht die Infrastruktur nicht.** Der
Scheduler, der die Zusage aus § 3 AGB trägt, lebt außerhalb des geprüften
Baums — und war 143 Läufe lang tot, während jeder Prüfer im Repo grün meldete.
Bei jeder Zusage fragen: **welches System muss dafür laufen, und wo steht sein
Protokoll?**
