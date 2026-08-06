# Ticket 24 — Wer merkt, wenn der Liefer-Cron wieder stirbt?

Typ: `wayfinder:task` (AFK)
Status: **OPEN**
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
