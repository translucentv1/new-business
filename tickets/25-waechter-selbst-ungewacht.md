# Ticket 25 — Wer meldet den Tod des Waechters selbst?

Typ: `wayfinder:task` (AFK)
Status: **GESCHLOSSEN 2026-08-08** — Entscheidung: **zweiter Ring JA**, als
echter `interval`-Job `5e99ad47470f` (30 min, `no_agent`, `deliver=local`).
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Hervorgegangen aus: [Ticket 24](24-cron-gesundheit-ungewacht.md)

## Question

Ticket 24 laesst `cron_health_audit.py` unbeaufsichtigt **innerhalb** von
`bfb63346d942` mitlaufen (alle 30 min, ohne Inferenz-Call). Damit ueberwacht
der Geldpfad-Job sich selbst und alle anderen Jobs — aber **seinen eigenen Tod
kann er nicht melden**: faellt er aus, laeuft auch das Audit nicht, und nichts
wird rot.

Konkret offen: **Soll ein zweiter, unabhaengiger `--no-agent`-Job das Audit
fahren — oder reicht die Erkennung durch den naechsten Agenten-Tick?**

## Ausgangslage (MEASURED 2026-08-06)

- Der Selbstbezug ist real, aber nicht blind: die Stagnations-Erkennung
  (`letzter Erfolg vor N min > Toleranz`, Toleranz = 180 min bei 30-min-Takt)
  ist rot-faehig (Mutant **M5** in `_mutation_probe_t24.py`). Wer das Audit aus
  *irgendeinem* Kontext startet, sieht den Ausfall.
- Der aeussere Ring ist heute der Agenten-Tick `87a15fe059fc` —
  **27 completed / 22 failed**, also genau die Zuverlaessigkeit, die Ticket 22
  als ungenuegend entlarvt hat.
- Ein zweiter Job kostet nichts (kein Inferenz-Call, kein Geld), verschiebt das
  Problem aber nur eine Ebene: auch der zweite Job kann sterben. Die ehrliche
  Frage ist nicht „luecken los\" sondern **„welche Ausfallmodi sind
  unabhaengig?"** (Spend-Protection und 429 treffen nur Agenten-Jobs; ein
  gestopptes Gateway oder ein ausgeschalteter Rechner trifft beide).

## Wie zu pruefen

1. Ausfallmodi auflisten und je Modus belegen, ob ein zweiter `--no-agent`-Job
   ihn wirklich unabhaengig ueberlebt (**messen**, nicht argumentieren —
   z. B. Job gezielt auf ein `sys.exit(1)` zeigen lassen wie in Ticket 22).
2. Nur wenn mindestens ein realer Modus unabhaengig abgedeckt wird, den
   zweiten Job anlegen; sonst dokumentieren, dass der Agenten-Tick der
   aeussere Ring bleibt, und das Ticket **out of scope** stellen.
3. Kein Job, der bei einem Ausfall nur eine Datei schreibt, die niemand liest —
   solange Ticket 23 (Zustellung) offen ist, ist „rot in `executions.db`" das
   einzige Signal.

## Entscheidung, die daran haengt

Ob der Waechter selbst ueberwacht ist — oder ob bewusst akzeptiert wird, dass
sein Tod erst beim naechsten Agenten-Tick auffaellt.

---

## Aufloesung (2026-08-08, alles MEASURED in DIESEM Tick neu ausgefuehrt)

Der Vortick hinterliess die Arbeit **uncommittet** — nach Merkregel wurde jeder
Claim neu ausgefuehrt, nicht uebernommen.

### 1. Der eigentliche Befund war nicht der Selbstbezug, sondern ein LATCH

Das Audit aus Ticket 24 beurteilte den Geldpfad-Traeger am **Job-Exit
`completed`** — also an genau der Groesse, die es durch sein eigenes rc
**selbst bestimmt**. Ein einziges rotes rc macht den naechsten Lauf
`failed`, damit steigt das Alter des letzten Erfolgs weiter, damit bleibt das
Audit rot: eine Schlinge, die sich nur zuzieht.
AM ALT-STAND AUSGEFUEHRT (`_mutation_probe_t25.py`, Teil 1, echte
`jobs.json` + `executions.db`):

    ALT-STAND am realen Latch  -> rc=1 "letzter Erfolg vor 1031 min"
                                  gegen eine KERNGESUNDE Pipeline
    NEUE Fassung, gleiche Daten -> rc=0 (Latch geloest)
    NEUE Fassung, Pipeline wirklich stumm -> rc=1 (weiterhin rot-faehig)

Fix: das Urteil haengt jetzt an zwei Groessen, die der Job **nicht selbst
setzt** — `[A]` letzter Lauf-VERSUCH (aus `executions.db`) und `[B]`
Pipeline-Heartbeat, geschrieben in Etappe `[2b]` von `cron_auto_fulfill.py`
**vor** dem Urteil und **nur** bei sauberer Pipeline + erreichbarem Kaufpfad.
Der Job-Exit `completed` wird noch gedruckt, aber ausdruecklich als
`[INFO - kein Kriterium, Selbstbezug]`.

### 2. Ausfallmodi gemessen, nicht argumentiert (`executions.db`)

| Modus | Messung heute | zweiter Ring hilft? |
|---|---|---|
| **A job-lokaler Ausfall des Traegers** | 151 Fehl-Laeufe des Traegers, im selben Fenster **470 `completed`-Laeufe anderer Jobs** | **JA** — propagiert nachweislich nicht |
| **B stille Abwesenheit** | Traeger schwieg 409 min; seine letzte DB-Zeile war `completed` — Tod hinterlaesst eine **gruene** Zeile | **JA** — nur ein Dritter sieht das |
| **C Scheduler/Rechner tot** | im Fenster 06:42:32–13:31:10 (409 min) **0 Laeufe IRGENDEINES Jobs** | **NEIN** — gemeinsamer Prozess, ehrlich unabgedeckt |

Ticket-Kriterium war: „nur wenn mindestens ein realer Modus unabhaengig
abgedeckt wird". A und B sind real (151 bzw. 409 min heute) → **Ring anlegen**.
Modus C braucht einen Waechter **ausserhalb dieses Rechners** — das ist NICHT
Gegenstand dieses Tickets und wird nicht heimlich mitgebaut.

### 3. Der Vortick-Ring war falsch konfiguriert und hat den Geldpfad ROT gemacht

MEASURED aus `executions.db` (Fremdbefund dieses Ticks, nicht vom Vortick
gemeldet): der probeweise angelegte Waechter `34410d148c1f` hatte
`schedule = {"kind": "once", ...}`, **feuerte 0 mal** und riss den Traeger
zweimal mit:

    05:41  CRON_HEALTH_DEFEKT "0 Laeufe protokolliert" -> RTD_FULFILL_DEFEKT  (rc=1, failed)
    06:11  "Intervall nicht ableitbar (kind=once)"     -> RTD_FULFILL_UNGEPRUEFT (rc=2, failed)

Der Job ist inzwischen aus `jobs.json` verschwunden. Lehre: ein Waechter, der
noch nie gelaufen ist, ist fuer das Audit ununterscheidbar von einem toten —
deshalb wurde der neue Ring **sofort nach dem Anlegen einmal gefeuert**.

### 4. Der neue Ring — MEASURED

- Angelegt direkt in `cron/jobs.json` (CLI verstuemmelt deutsche Prompts und
  erzeugt `kind: once`): `5e99ad47470f`, `{"kind":"interval","minutes":30}`,
  `script = rtd_health_watchdog.py`, `no_agent=true`, `deliver=local`,
  `workdir = C:\Users\phili\new-business`. Backup vorher:
  `cron/jobs.json.bak_t25_20260808_133913`.
- Loader `$HERMES_HOME/scripts/rtd_health_watchdog.py` ruft das **Repo-Skript**
  auf (keine zweite Kopie) und nennt bewusst NIE den Namen der Lieferpipeline,
  sonst kippt die Rollenerkennung des Audits vom Waechter zum Traeger.
- Echter Job-Lauf `hermes cron run 5e99ad47470f` → **„Ran now: succeeded"**,
  DB-Zeile `completed`, Ausgabedatei `cron/output/5e99ad47470f/
  2026-08-08_13-39-38.md` mit `Mode: no_agent (script)` und
  `Waechter (2. Ring, Ticket 25): 1` — die beiden Ringe **sehen einander**.
- Der Lauf traf eine unmessbare Lage (Scheduler-Stillstand 446 min) und
  meldete korrekt `WAECHTER_UNGEPRUEFT (Audit rc=2, kein Defekt-Claim)` mit
  **exit 0** → kein Falsch-Rot. Genau das, was `34410d148c1f` falsch machte.
- Danach echter Traeger-Lauf: `cron_auto_fulfill.py` → `[2b]` Heartbeat frisch,
  `[3] CRON_HEALTH_OK`, `RTD_FULFILL_OK`; und als **echter Job**
  `hermes cron run bfb63346d942` → `completed` (13:41:58), Ausgabedatei mit
  `RTD_FULFILL_OK`. Vor dem Fix waere derselbe Zustand („letzter Erfolg vor
  417 min") ein Defekt-Claim gewesen.
- Testlage: `cron_health_audit --selftest` **37/37**, `cron_auto_fulfill
  --selftest` **27/27** (inkl. „PRODUKTIV-Heartbeat unangetastet"),
  `_mutation_probe_t25.py` **MUTATION_PROBE_OK 21/21** (11 rote Mutanten in
  2 Produktivdateien, exakte Diagnosezeile, kein `Traceback`, beide Dateien
  sha256-genau restauriert, rc-Wechsel 0→1→0).

### 5. Ehrliche Grenzen

- **Modus C bleibt offen** (ein Prozess, ein Rechner) — bewusst, nicht vergessen.
- **`[A]` allein wuerde luegen:** heute standen zwei Jobs (`bfb63346d942`,
  `8c7afca842ac`) ueber 10 min in `claimed` mit `started_at = None` — der
  Scheduler hatte sie beansprucht, aber nie gestartet (der Pool war vom
  Agenten-Job belegt). `[A]` haette das als frischen „Lauf-VERSUCH" gelesen.
  Nur `[B]` (Heartbeat) wird in diesem Zustand alt und rot. Die zwei Kriterien
  sind deshalb **nicht redundant** — eines deckt genau die Luecke des anderen.
- Der Ring meldet ueber `executions.db` rot; **gelesen** wird das dort erst,
  wenn Ticket 23 (Zustellung) geloest ist. Solange bleibt es das einzige
  verfuegbare Signal, wie im Ticket vorausgesetzt.
- Neu aufgeworfen und NICHT hier geloest: `DEFEKT` (rc=1) und `UNGEPRUEFT`
  (rc=2) landen im Signalkanal beide als `failed` → [Ticket 27](27-signalkanal-defekt-vs-unmessbar.md).
