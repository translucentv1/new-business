# Ticket 24 — Wer merkt, wenn der Liefer-Cron wieder stirbt?

Typ: `wayfinder:task` (AFK)
Status: **CLOSED** (2026-08-06)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Hervorgegangen aus: [Ticket 22](22-liefer-cron-tot.md)

## Question

Ticket 22 hat **einen** Cron-Job gemessen und repariert (`bfb63346d942`).
Die Messung war einmalig und von Hand. Es gibt **kein stehendes Tor**, das rot
wird, wenn dieselbe Klasse wieder zuschlägt — und sie hat 143 Läufe lang
unbemerkt zugeschlagen, während jeder Prüfer im Repo grün meldete.

Konkret offen: **Welcher Cron trägt heute die 24-h-Zusage aus § 3 AGB, und was
wird rot, wenn er ausfällt?**

## Warum das nicht Aktionismus ist

Die vier vorherigen Fälle derselben Klasse (Teil-Vollständigkeit) wurden je
durch ein *stehendes* Tor geschlossen, nicht durch eine Einmalmessung:
Ticket 13 → `legal_link_audit.py`, 17 → `verify_ticket13_live.py`,
19 → `indexnow_submit --selftest`, 20 → `dl_noindex_audit.py`.
Ticket 22 ist als einziges bei der Einmalmessung stehen geblieben.

## Ausgangsbefund (MEASURED 2026-08-06 09:26)

`$HERMES_HOME/cron/jobs.json`: 14 Jobs, davon **6 enabled**.
`executions.db`, Bilanz je aktivem Job:

| Job | Name | completed | failed | letzter Lauf |
|---|---|---|---|---|
| `bfb63346d942` | RTD Auto-Fulfill | 10 | 144 | 09:20 completed |
| `87a15fe059fc` | RTD-Builder | 27 | 22 | 09:25 running |
| `3e7e333151b0` | Bericht an Nutzer | 37 | 5 | 09:09 completed |
| `bae39ea51a60` | AI-CEO Money Loop | 12 | 8 | 07:28 completed |
| `8c7afca842ac` | Abend-Report | 6 | 1 | 06:05 completed |
| `a564ec4d11ea` | Selbstverbesserungs-Pass | **0** | 7 | 05.08. failed |

Alle 10 `completed` von `bfb63346d942` liegen **nach** dem Ticket-22-Fix.

## Wie zu prüfen

Ein stehendes Tor `cron_health_audit.py` mit den Konventionen aus
Ticket 16/17/19/20:

- **Zielmenge ABGELEITET, nicht hartkodiert** (Merkregel Ticket 17): Geldpfad-Job
  = ein Job, dessen Skript — direkt oder über den Loader unter
  `$HERMES_HOME/scripts/` — Code aus `<REPO>/scripts/request_delivery/` ausführt.
- **Leere Zielmenge ist NICHT grün** (Merkregel Ticket 16): „kein Job liefert
  aus" ist exakt der Ticket-22-Zustand.
- Drittes Ergebniswort `CRON_HEALTH_UNGEPRUEFT` (rc=2), echter Defekt schlägt
  Unmessbarkeit.
- `--selftest` mit Fault Injection durch die **echte** `main()`, plus
  Mutationssonde am Produktivcode.

## Entscheidung, die daran hängt

Ob die 24-h-Zusage in § 3 AGB überwacht ist oder weiterhin auf Zuruf steht.

---

## Antwort (MEASURED 2026-08-06, abendlicher Tick)

Der Tick startete mit **uncommitteter** Arbeit aus einem Vortick
(`cron_health_audit.py`, 586 Zeilen, untracked). Nach Merkregel wurde nichts
uebernommen, sondern **neu ausgefuehrt** — sie hat gehalten, aber der
entscheidende Teil der Frage war noch offen (siehe „Der eigentliche Befund").

### Das stehende Tor existiert und ist nachweislich rot-faehig

`scripts/request_delivery/cron_health_audit.py` — Zielmenge **abgeleitet**
(Geldpfad-Traeger = Job, dessen Skript direkt oder ueber den Loader Code aus
`<REPO>/scripts/request_delivery/` ausfuehrt), leere Zielmenge ist **nicht**
gruen, drittes Ergebniswort `CRON_HEALTH_UNGEPRUEFT` (rc=2), echter Defekt
schlaegt Unmessbarkeit.

- `--selftest` → **25/25 SELFTEST_OK** (Fault Injection durch die echte `main()`).
- **Echter Lauf** (nicht durch den Selftest ersetzt, Merkregel Ticket 19):
  `CRON_HEALTH_OK` — 14 Jobs / 6 enabled, **1 Geldpfad-Traeger**
  `bfb63346d942`, `no_agent=True`, `enabled=True`, workdir gesetzt, Intervall
  **30 min** (erlaubte Erfolgs-Luecke 180 min), **168 Laeufe / 23 completed**,
  letzter Erfolg **vor 11 min**. `87a15fe059fc` (RTD-Builder) wird korrekt als
  **Nebentraeger** gefuehrt (agentengetrieben — genau die Bauform, die in
  Ticket 22 143x ausfiel) und zaehlt **nicht** als Traeger.
- `_mutation_probe_t24.py` (NEU) mutiert den **Produktivcode**:
  **MUTATION_PROBE_OK 17/17**, **11 Mutanten rot** in 2 Dateien, jeweils mit
  der **exakten** erwarteten Diagnosezeile, ohne `Traceback`, beide Dateien
  sha256-genau wiederhergestellt (`a34ecbbc1ecc2aff`, `e99a326a6ffafa67`),
  rc-Wechsel 0 → 1 → 0. Abgedeckt: leere Zielmenge gruen, agentengetriebener
  Traeger nicht rot, abgeschalteter Job nicht rot, „0 completed" nicht rot,
  stille Stagnation nicht rot, Intervall > 24 h nicht rot, Reihenfolge
  invertiert.

### Der eigentliche Befund: ein Tor, das niemand oeffnet, ist kein Tor

Ein Skript im Repo beantwortet die Ticket-Frage **nicht**. Es haette exakt
denselben Fehler eine Ebene hoeher wiederholt: `cron_health_audit.py` waere nur
gelaufen, wenn ein **Agenten-Tick** daran denkt — und Agenten-Ticks sind genau
die unzuverlaessige Komponente (`87a15fe059fc`: 27 completed / 22 failed,
Spend-Protection- und 429-Klasse). Die Ticket-22-Diagnose lautete „die Zusage
haengt an einem Job, der nie laeuft"; ein nur manuell aufgerufenes Audit ist
dieselbe Bauform.

**Fix:** Das Tor laeuft jetzt **unbeaufsichtigt** in dem einzigen nachweislich
zuverlaessigen Job mit. `cron_auto_fulfill.py` hat eine dritte Etappe:

```
[3] Cron-Gesundheit (Ticket 24)
  ERGEBNIS: CRON_HEALTH_OK (1 Geldpfad-Traeger ueberwacht, ...)
```

`hrc == 1` → `RTD_FULFILL_DEFEKT` (Job wird in `executions.db` **rot**);
`hrc` sonst ≠ 0 → `RTD_FULFILL_UNGEPRUEFT`; fehlendes/abgestuerztes Audit ist
**nie** ein Defekt-Claim gegen den Geldpfad. Damit laeuft das Tor **alle
30 min ohne Inferenz-Call**.

### Beinahe-Regression, im eigenen Umbau gefunden

Der Defekt-Zweig steht **vor** dem Sale-Zweig. Nach dem Einbau haette
ausgerechnet ein Cron-Health-Defekt die `*** ERSTER SALE ***`-Meldung
**verschluckt** — das lauteste Signal des ganzen Systems, unterdrueckt von
einer Nebenmessung. Der Banner wird jetzt **immer** gedruckt, unabhaengig vom
Ergebniswort; Mutant **F3** stellt genau diesen Fehler wieder her und faellt.

- `cron_auto_fulfill.py --selftest`: **14/14 → 21/21** (6 neue Faelle:
  Health-Defekt → rot, Health unmessbar → UNGEPRUEFT, echter Defekt schlaegt
  Health-Unmessbarkeit, Sale-Banner ueberlebt Health-Defekt, gesunde Health
  aendert nichts, Health-Wort wird ueber `rc` statt per Substring gelesen).
- **Echter Lauf der Produktiv-Kette**: `[1] sessions=2 paid=0 neu=0` ·
  `[2] rtd.html HTTP 200 / thanks.html HTTP 200` · `[3] CRON_HEALTH_OK` ·
  `ERGEBNIS: RTD_FULFILL_OK`, rc=0.

### Ehrliche Grenzen

- **Selbstbezug:** Stirbt `bfb63346d942` selbst, laeuft auch das Audit nicht —
  ein Job kann seinen eigenen Tod nicht melden. Diese Luecke schliesst das
  Ticket **nicht**; sie ist als **Ticket 25** aufgemacht. Entlastend: die
  Stagnations-Erkennung (`letzter Erfolg vor N min > Toleranz`) ist
  rot-faehig (Mutant **M5**), d. h. der naechste Lauf des Audits aus
  *irgendeinem* Kontext meldet den Ausfall.
- Der Bericht erreicht den Nutzer weiterhin nicht (WhatsApp-Bridge,
  **Ticket 23**) — ein rotes `executions.db` sieht heute nur, wer nachsieht.
- Gemessen ist die **Konfiguration und Historie** des Schedulers, nicht die
  Zustellung an einen echten Kunden (0 Sales, unveraendert).

### Merkregel

**Ein stehendes Tor ist erst dann stehend, wenn es ohne Agenten laeuft.** Ein
Pruefskript im Repo, das nur ein Tick aufruft, erbt die Ausfallwahrschein-
lichkeit dieses Ticks — und genau daran ist Ticket 22 gestorben. Bei jedem
neuen Tor fragen: **wer ruft es auf, wenn niemand hinsieht?**
