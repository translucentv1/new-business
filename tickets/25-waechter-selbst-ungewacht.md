# Ticket 25 — Wer meldet den Tod des Waechters selbst?

Typ: `wayfinder:task` (AFK)
Status: **OPEN**
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
