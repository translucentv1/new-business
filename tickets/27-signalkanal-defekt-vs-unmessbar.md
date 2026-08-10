# Ticket 27 — Im einzigen Signalkanal ist „defekt" von „nicht messbar" nicht unterscheidbar

Typ: `wayfinder:grilling` (AFK entscheidbar, aber Zielkonflikt)
Status: **GESCHLOSSEN 2026-08-10**
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

---

## Aufloesung (2026-08-10, MEASURED)

### Hauptfrage: `exit != 0` bei UNGEPRUEFT BLEIBT

Die Frage war falsch gestellt. Teuer war nicht der Exitcode, sondern dass
`failed` **nicht dekodierbar** war. Mit dem Decoder aus Commit `ce8b2d9` steht
die Bedeutung jetzt in jeder Zeile — LIVE-Lauf 2026-08-10 gegen die echte
`executions.db`, Traeger `bfb63346d942`, 214 Laeufe:

    dekodiert (Ticket 27, INFO): 136x RUNNER-ABBRUCH Spend-Guard (Skript lief
    NIE), 7x DEFEKT (exit 1), 2x RUNNER-ABBRUCH Modell fehlt (Skript lief NIE),
    2x Scheduler-Neustart (kein Skript-Urteil), 1x RUNNER-ABBRUCH DNS/Netz
    (Skript lief NIE), 1x unmessbar (exit 2), 1x laeuft/haengt

Von 150 nicht-`completed`-Laeufen sind **7 echte Defekte**; 139 sind
Runner-Abbrueche, bei denen das Skript nie startete. Damit ist die Praemisse
des Tickets („nur durch Lesen jedes error-Textes") erledigt: das Lesen
uebernimmt das Audit. `exit 0` fuer UNGEPRUEFT wuerde die Information
vernichten, die gerade sichtbar gemacht wurde. **Gruen heisst weiterhin
ausschliesslich „gemessen und gut".**

### Nebenfrage B: JA, eigener Signalwert — `exit 4`

Ein Defekt des **zweiten Rings** ist kein Defekt des Geldpfads (real geschehen
2026-08-08 05:41). Getrennt wird nach BETROFFENEM, nicht nach Schweregrad:
`defects` = Geldpfad, `ring_defects` = Ueberwachung. Neues Ergebniswort
`CRON_HEALTH_NEBENRING_DEFEKT` / `RTD_FULFILL_NEBENRING_DEFEKT`, rc=4, in
`SIGNAL_KONVENTION` hinterlegt. Rangfolge gemessen: Geldpfad-Defekt (1) >
Nebenring (4) > unmessbar (3) > OK (0); der SALE-Banner steht vor der
Verzweigung und wird von keinem davon verschluckt.

### Was dabei GEGENBEWIESEN wurde (der eigentliche Befund des Ticks)

Der Vortick hatte als Antwort auf den Zielkonflikt eine **WACH-UHR**
(`wach_minuten()`) unkommittiert liegen lassen: nicht Wanduhr-Alter, sondern
nur Minuten mit belegbar laufendem Scheduler sollten gegen die Toleranz
gehalten werden. NEU AUSGEFUEHRT statt uebernommen (Merkregel) —
**`cron_health_audit --selftest` war damit ROT: 50/57.** Vier der sieben roten
Faelle waren **FALSCH-GRUEN auf dem Geldpfad**:

| Lage | erwartet | Wach-Uhr |
|---|---|---|
| Heartbeat 1031 min alt, Job feuert alle 30 min | rc=1 | **rc=0** |
| nur der Geldpfad schweigt 900 min, anderer Job laeuft | rc=1 | **rc=0** |
| wirklich stummer zweiter Traeger | rc=1 (benannt) | **maskiert** |
| Geisterzeilen fremder job_ids als Wach-Alibi | rc=2 | **rc=0** |

Zwei unabhaengige Ursachen: (1) Entwurf — die Wach-Summe entsteht aus FREMDEN
Laeufen, ist bei duenner Beleglage klein, und „wenig Wachzeit" fiel in den
GRUEN-Zweig statt in „unmessbar". (2) Verdrahtung — `main()` reichte
`bekannte_ids` **nie** an `check_traeger()` durch, die Geisterzeilen-Sperre lief
also produktiv gar nicht mit (Funktion da, Aufrufer setzt sie nicht — dieselbe
Klasse wie der Signal-Decoder, der zuvor nie aufgerufen wurde).

ENTSCHEIDUNG: Wach-Uhr **verworfen**, Urteil wieder ueber `stillstand_deckt`
(Ticket 25). Der Verzicht kostet Falsch-Rot nach Rechnerabschaltung — das ist
die **billigere** Fehlerrichtung und wandert als eigene Frage in
[Ticket 28](28-falschrot-nach-abschaltung.md).

### Belege

    cron_health_audit --selftest      57/57 SELFTEST_OK   (vorher 50/57)
    cron_auto_fulfill --selftest      38/38 SELFTEST_OK
    _mutation_probe_t27c.py           MUTATION_PROBE_OK 36/36
                                      (rote Mutanten in 2 Produktivdateien,
                                       exakte Diagnosezeile, kein Absturz,
                                       beide sha256-genau restauriert
                                       97f8922fa7f1 / 5e24130fcfd4, rc 0->1->0)
    LIVE cron_auto_fulfill            RTD_FULFILL_OK, [3] CRON_HEALTH_OK
    LIVE Geldpfad                     rtd/thanks HTTP 200, KETTE_OK
