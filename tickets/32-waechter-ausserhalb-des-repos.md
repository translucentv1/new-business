# Ticket 32 — Der 2. Ring liegt außerhalb des Repos, der Fixer ist zum Werkzeug geworden

Typ: `wayfinder:task` (AFK) · Status: **OFFEN** · unblockiert · Priorität: mittel
Hervorgegangen aus: [Ticket 30](30-zustellbarkeit-ungewacht.md) (GESCHLOSSEN)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

Zwei Befunde derselben Klasse („etwas Tragendes steht außerhalb der Prüfung"):

**A) Der 2. Ring ist unversioniert.** `rtd_health_watchdog.py` liegt in
`HERMES_HOME/scripts/`, **nicht** im Repo (MEASURED: `find` über den Repo-Baum
findet keine Kopie). Er ist damit:
- nicht in der Versionsgeschichte — der Ticket-30-Eingriff (`[SILENT]` auf dem
  OK-Pfad) existiert nur als Datei plus `.bak`-Kopie,
- von keinem `--selftest` und keiner Mutationsprobe erfasst,
- bei Verlust/Neuaufsetzen von `HERMES_HOME` ersatzlos weg — zusammen mit dem
  einzigen Ring, der den Tod des Geldpfads melden soll.

Die naheliegende Lösung (Kopie ins Repo) erzeugt **zwei Wahrheiten**, die
auseinanderdriften. Das ist die eigentliche Frage: Spiegel + Drift-Prüfer, oder
Symlink, oder Repo als Quelle und Deployment-Schritt?

**B) `fix_cron_delivery_origin.py` ist zum stehenden Werkzeug geworden.**
Ticket 30 hat es als „einmaliger Reparaturlauf" eingeordnet — diesen Tick lief
es zum **zweiten** Mal, produktiv, an `jobs.json`. Nach Ticket 15 entscheidet
die Nutzung, nicht die Absicht: was wiederholt scharf läuft, ist ein stehendes
Tor und braucht `--selftest` + Mutationsprobe. Es schreibt an der Datei, an der
die gesamte Zustellung hängt.

## Vorgehen

1. A und B getrennt beantworten — es sind zwei Entscheidungen, die nur die
   Klasse teilen.
2. Für B: `--selftest` mit Fault Injection durch die **echte** `main()` gegen
   eine injizierte `jobs.json`-Attrappe; Rot-Fälle mindestens: kein Spender
   vorhanden, Job-Anzahl ändert sich (Rollback muss greifen), Ziel-Job bleibt
   kaputt. Die Attrappe gegen das **reale Schema** gegenmessen (Merkregel
   Ticket 28: Attrappen-Falle).
3. Produktions-`jobs.json` bei keinem Testlauf anfassen.

## Nicht vergessen (ASSUMED, vor dem Beantworten nachmessen)

- Ob es weitere tragende Skripte außerhalb des Repos gibt, ist **unbelegt**.
  Vollzählig über `HERMES_HOME/scripts/` messen und gegen den Repo-Baum
  abgleichen — nicht stichprobenartig (Merkregel Ticket 13/17).
- `.bak`-Dateien sind kein Backup-Konzept: sie liegen im selben Verzeichnis wie
  das Original und gehen mit ihm gemeinsam verloren.
