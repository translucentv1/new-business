# Ticket 28 — Falsch-Rot nach Rechnerabschaltung, ohne dabei Falsch-Gruen zu erzeugen

Typ: `wayfinder:prototype` (AFK baubar, aber der erste Entwurf ist bereits gescheitert)
Status: **OPEN**
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Hervorgegangen aus: [Ticket 27](27-signalkanal-defekt-vs-unmessbar.md)

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
