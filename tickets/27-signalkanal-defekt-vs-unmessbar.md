# Ticket 27 — Im einzigen Signalkanal ist „defekt" von „nicht messbar" nicht unterscheidbar

Typ: `wayfinder:grilling` (AFK entscheidbar, aber Zielkonflikt)
Status: **OPEN**
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Hervorgegangen aus: [Ticket 25](25-waechter-selbst-ungewacht.md)

## Question

Seit Ticket 16/17/18/19 gilt im ganzen Geldpfad die Konvention
**„unmessbar ist kein Defekt-Claim"** — drittes Ergebniswort, rc=2. Am
Prozessrand verschwindet sie: der Cron-Runner kennt nur `exit 0 = completed`
und `exit != 0 = failed`. Damit ist `RTD_FULFILL_UNGEPRUEFT` (rc=2) in
`executions.db` **exakt dasselbe Zeichen** wie `RTD_FULFILL_DEFEKT` (rc=1).

Soll `cron_auto_fulfill.py` bei `UNGEPRUEFT` mit **exit 0** enden (wie es der
Waechter-Loader `rtd_health_watchdog.py` bereits tut), oder bleibt Rot-bei-
Unmessbarkeit die gewollte Vorsicht?

## Ausgangslage (MEASURED 2026-08-08)

- Zwei Laeufe desselben Tages, verschiedene Bedeutung, gleiche DB-Zeile:

      05:41  rc=1  RTD_FULFILL_DEFEKT      -> status='failed'
      06:11  rc=2  RTD_FULFILL_UNGEPRUEFT  -> status='failed'

- Bilanz des Traegers `bfb63346d942`: **149 failed / 40 completed / 2 unknown /
  1 claimed**. Wie viele der 149 echte Defekte und wie viele nur „unmessbar"
  waren, ist aus dem Statusfeld **nicht** ableitbar — nur durch Lesen des
  `error`-Textes jeder einzelnen Zeile.
- Der zweite Ring loest es bereits in seine Richtung: `rc=2 -> exit 0` plus
  Klartextzeile `WAECHTER_UNGEPRUEFT`. Zwei Bauteile desselben Geldpfads
  behandeln denselben Fall also **entgegengesetzt** — mindestens eines ist falsch.

## Der Zielkonflikt (nicht vorschnell aufloesen)

- **exit 0 bei UNGEPRUEFT**: ehrlich (kein Defekt-Vorwurf gegen eine gesunde
  Pipeline), aber ein dauerhaft unmessbarer Geldpfad sieht dann **gruen** aus —
  genau die Verwechslung, die Ticket 14 („fettes 404") und Ticket 18
  („Baum-Gruen liest sich wie Live-Gruen") teuer gemacht haben.
- **exit != 0 bei UNGEPRUEFT**: konservativ, aber jede Nachtabschaltung faerbt
  den Geldpfad rot; nach genug Falsch-Rot liest niemand das Signal mehr — die
  Klasse, an der Ticket 22 gestorben ist (143 rote Laeufe, niemand sah hin).

## Wie zu pruefen

1. Zaehlen, wie oft rc=2 real vorkommt (`error`-Texte der 149 `failed`-Zeilen
   klassifizieren) — erst dann ist die Haeufigkeit des Falsch-Rot bekannt.
2. Pruefen, ob der Runner einen dritten Zustand kennt (Exitcode-Mapping in
   `cron/`), bevor eine Konvention erfunden wird, die er gar nicht abbilden kann.
3. Falls kein dritter Zustand existiert: entscheiden, welche der beiden
   Fehlerrichtungen teurer ist — und die Entscheidung im Map begruenden, nicht
   im Code verstecken.

## Nebenfrage B (gleiche Wurzel)

Soll ein Defekt des **Waechters** den **Traeger** rot machen? Heute ja: am
2026-08-08 05:41 riss ein nie gefeuerter Waechter den Lieferjob mit
(`RTD_FULFILL_DEFEKT`, obwohl die Lieferung sauber lief). Das ist die Klasse
„Nebenmessung verschluckt/vergiftet das Hauptsignal" aus Ticket 24 — dort
geloest fuer den Sale-Banner, hier noch offen fuer das Job-rc.
