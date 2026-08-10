# Ticket 28 — Falsch-Rot nach Rechnerabschaltung, ohne dabei Falsch-Gruen zu erzeugen

Typ: `wayfinder:prototype` (AFK baubar, aber der erste Entwurf ist bereits gescheitert)
Status: **GESCHLOSSEN 2026-08-10** — Antwort unten unter „Resolution".
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Hervorgegangen aus: [Ticket 27](27-signalkanal-defekt-vs-unmessbar.md)

## Resolution (MEASURED 2026-08-10)

**Antwort: nicht die Zeit zaehlen, sondern die *verpassten Gelegenheiten* — und
das Ergebnis ist nicht GRUEN, sondern UNMESSBAR.** Genau daran ist die Wach-Uhr
gescheitert: sie wollte das Schweigen entlasten und landete im Gruen-Zweig.

Kriterium `[B]` urteilt jetzt so:

- `>= 1` eigener Lauf, der seit dem Heartbeat **wirklich gestartet** ist
  (`started_at` gesetzt), ohne zu melden -> **DEFEKT**. Das ist die Messlatte
  aus Ticket 27 (Falsch-Gruen-Fall 1: Job feuert alle 30 min, Pipeline meldet
  seit 1031 min nicht).
- **0** gestartete Laeufe seit dem Heartbeat -> **kein Defekt-Claim**, aber auch
  kein Gruen: `CRON_HEALTH_UNGEPRUEFT` (rc=2) mit benannter Begruendung. Ob der
  Job ueberhaupt feuert, sagt bereits Kriterium `[A]`.
- **Kein Dauerfreibrief:** > 1440 min stumm ist DEFEKT, auch ohne Gelegenheit.
- **Uhr-Jitter:** 60 s Karenz, sonst wird der meldende Lauf selbst zur
  „verpassten Gelegenheit".

Der im Ticket benannte Fallstrick war real: die letzte DB-Zeile war `claimed`
mit `started_at=NULL` — ein Lauf, der **nie startete** und deshalb per
Konstruktion nichts melden konnte. Wer ihn mitzaehlt, reproduziert das
Falsch-Rot exakt (Mutant M1 stellt genau das wieder her und faellt).

### Belege

| Nachweis | Ergebnis |
|---|---|
| Alt-Stand (HEAD) gegen die konservierte Lage 784/793/9 min | `rc=1 CRON_HEALTH_DEFEKT` — das Falsch-Rot ist **ausgefuehrt**, nicht behauptet |
| Neue Fassung, dieselbe Lage | `rc=2 CRON_HEALTH_UNGEPRUEFT` mit benannter Begruendung (kein stilles Gruen) |
| `cron_health_audit.py --selftest` | **67/67** |
| Deckungs-Check gegen stille Schrumpfung (Ticket 18) | alle **57** HEAD-Faelle namentlich weiterhin vorhanden, **+10** neu — 0 verschwunden |
| `_mutation_probe_t28.py` | `MUTATION_PROBE_OK 22/22`, 6 rote Mutanten, sha256-genau restauriert `13ab250e05eff98f`, rc 0→1→0 |
| Verdrahtung (`x=None`-Falle aus Ticket 27) | Selftest liest eine **echte SQLite-Datei mit realem Schema**; Gegenmessung an der Produktiv-DB: Spalten `job_id/status/claimed_at/started_at/finished_at/error` vorhanden, 1001 Zeilen, 2 ohne `started_at` |
| Echte Laeufe | `CRON_HEALTH_OK`, `cron_auto_fulfill` -> `RTD_FULFILL_OK` mit `[2b]` frischem Heartbeat und `[3] CRON_HEALTH_OK` |
| Regression | `VERIFY_OK` (78 ok, 0 fail), `KETTE_OK`, `cron_auto_fulfill --selftest` 38/38 |

### Ehrliche Grenze

Bei **dauerhaft stummem Scheduler** bleibt es bei `UNGEPRUEFT` — Gruen ist dort
ausdruecklich **nicht** das Ziel. Ausfallmodus C aus Ticket 25 (Rechner/Scheduler
tot) ist damit weiterhin **nicht abgedeckt**; das braeuchte einen Waechter
**ausserhalb dieses Rechners**. Der Exitcode bleibt `!= 0`, der Job erscheint in
`executions.db` also weiterhin als `failed` — lesbar gemacht hat das der Decoder
aus Ticket 27, beseitigt ist es nicht.

### >>> TICKET-PRAEMISSE FALSIFIZIERT <<<

Der Abschnitt „Nicht vergessen" behauptete, der zweite Ring
(`rtd_health_watchdog.py`) loese denselben Fall **entgegengesetzt**
(`rc=2 -> exit 0`). Das stimmt seit Ticket 27 nicht mehr — der Text war aus der
T27-Beschreibung uebernommen statt am Ist-Stand gemessen. **MEASURED** an einer
Kopie (Produktion unangetastet), die auf eine Audit-Attrappe mit `rc=2` zeigt:

    ERGEBNIS: WAECHTER_UNGEPRUEFT (Audit rc=2, kein Defekt-Claim)   exit 3

Beide Ringe teilen also bereits dieselbe Konvention: **unmessbar ist kein
Defekt-Claim, aber auch kein Gruen.** Nichts zu entscheiden, nichts zu erklaeren.
Echter Lauf des Waechters danach: `WAECHTER_OK` (rc=0).

## Question

Nach einer Rechner-/Scheduler-Abschaltung meldet `cron_health_audit.py` den
Geldpfad rot, obwohl die Lieferung kerngesund ist. Wie wird dieses Falsch-Rot
beseitigt, **ohne** die vier Falsch-Gruen-Faelle einzuhandeln, an denen die
WACH-UHR aus Ticket 27 gescheitert ist?

## Der reale Fall (MEASURED 2026-08-10 01:45Z, echte `executions.db`)

    Scheduler-Stillstand (groesste Luecke in 2880 min): 784 min
    Pipeline-Heartbeat: 2026-08-09T12:39:42Z          -> 793 min alt
    [A] letzter Lauf-VERSUCH vor 9 min
    DEFEKTE GELDPFAD (1):
      ! bfb63346d942 ...: Liefer-Pipeline meldete zuletzt vor 793 min,
        erlaubt waeren 180 min - die Lieferung steht
    ERGEBNIS: CRON_HEALTH_DEFEKT

Die Lieferung stand **nicht**. Der Rechner war 784 min aus; der Heartbeat ist
genau 9 min aelter als der Stillstand, weil er 9 min vor dessen Beginn
geschrieben wurde. Die Regel aus Ticket 25 verlangt `stillstand >= hb_age - 1`,
also **Deckung auf die Minute** — 8 min Differenz genuegen fuer den Defekt-Claim.

Gegenprobe im selben Tick: Traeger einmal echt laufen lassen ->
`[2b] Pipeline-Heartbeat geschrieben` -> `[3] CRON_HEALTH_OK` ->
`RTD_FULFILL_OK`. Das Rot war also **transient und selbstheilend**, kein Latch
(wichtig: die Klasse aus Ticket 25 ist NICHT zurueck). Es haelt nur so lange an,
wie der Traeger nicht laufen kann — heute, weil der Agenten-Job den Runner-Pool
belegte (DB-Zeile `status='claimed'`, `started_at=NULL`).

## Warum der naheliegende Entwurf schon gescheitert ist

Wach-Uhr = „nur Minuten mit belegbar laufendem Scheduler zaehlen". Ergebnis:
Selftest 50/57, davon 4 **Falsch-Gruen auf dem Geldpfad** (Tabelle in Ticket 27).
Nicht nochmal in dieser Form versuchen.

## Kandidat, der beide Richtungen halten koennte (NICHT verifiziert)

Nicht die Zeit zaehlen, sondern die **verpassten Gelegenheiten**: hat der Job
seit dem Heartbeat tatsaechlich *gestartete* Laeufe gehabt, ohne zu melden?

- >= 1 gestarteter eigener Lauf seit dem Heartbeat, kein Heartbeat -> **DEFEKT**
  (deckt den Fall „Job feuert, Pipeline meldet nicht" = Falsch-Gruen-Fall 1).
- 0 gestartete Laeufe seit dem Heartbeat -> kein `[B]`-Defekt; ob der Job
  ueberhaupt feuert, sagt bereits Kriterium `[A]`.

Fallstrick, der im echten Fall sofort zuschlaegt: die letzte Zeile war
`status='claimed'` mit `started_at=NULL` — ein Lauf, der **nie startete** und
folglich keinen Heartbeat schreiben konnte. `attempts` enthaelt heute nur
Zeitstempel, der Status geht verloren. Wer diesen Kandidaten baut, muss
gestartete Laeufe von bloss beanspruchten trennen, sonst ist das Falsch-Rot
exakt reproduziert.

## Wie zu pruefen

1. Kandidat gegen **alle 57** bestehenden Selftest-Faelle fahren — jeder
   Rot-Fall muss rot bleiben (die 4 Falsch-Gruen-Lagen aus Ticket 27 sind die
   Messlatte, sie gehoeren als benannte Faelle in den Selftest).
2. Am **Alt-Stand ausfuehren**, nicht argumentieren: die konservierte Lage von
   2026-08-10 (784/793/9 min, `claimed`+`started_at=NULL`) muss mit der neuen
   Fassung gruen sein und mit der alten rot.
3. Mutationssonde: mindestens ein Mutant pro neuem Zweig, exakte Diagnosezeile.
4. Ehrliche Grenze benennen: bei dauerhaft stummem Scheduler bleibt „unmessbar"
   das richtige Wort — Gruen ist dort **nicht** das Ziel.

## Nicht vergessen

Der zweite Ring (`rtd_health_watchdog.py`) loest denselben Fall weiterhin
entgegengesetzt (`rc=2 -> exit 0`). Ticket 27 hat das bewusst stehen lassen,
weil er keinen Geldpfad traegt. Wer hier entscheidet, entscheidet auch das —
oder benennt ausdruecklich, warum die Ringe verschiedene Konventionen haben.
