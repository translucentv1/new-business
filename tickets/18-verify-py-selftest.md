# Ticket 18 — `scripts/verify.py`: das kanonische Tor ist ungeprüft

**Typ:** `wayfinder:task` (AFK)
**Status:** OFFEN — unblockiert, auf der Frontier
**Eltern:** wayfinder_map.md
**Blockiert durch:** nichts (Ticket 17 geschlossen)
**Priorität:** mittel — größte Prüffläche im Repo, aber nicht der Geldpfad.

## Question

`scripts/verify.py` bezeichnet sich selbst als **„kanonische Verifikation für
new-business"** und ist mit 56 Checks der mit Abstand breiteste Prüfer im Repo
(MEASURED 2026-08-05: `python scripts/verify.py --offline` → `56 ok, 0 fail,
0 skip`, `rc=0`). Er hat **keinen `--selftest`**. Dass er einen Defekt
*bemerkt*, ist unbewiesen — bei 56 Checks ist das die größte unbelegte
Grün-Fläche, die im Repo übrig ist.

Ticket 17 hat die Prämisse „`verify_ticket13_live.py` ist das letzte Skript
ohne Selftest" falsifiziert; dieses Ticket zieht die Konsequenz.

Konkret zu klären, Check für Check:
1. Welche der 56 Checks können **überhaupt** rot werden, und welche sind
   Behauptungs-Etappen (drucken einen Schlusssatz statt zu messen)?
2. Enthält er die **Leere-Schleife-Falle** (`ok = True` + Schleife → grün bei
   leerer Eingabe)? Mehrere Checks melden Listen wie `— []`; eine leere Liste
   sieht dort per Konstruktion gesund aus.
3. Verwechselt er **Baum mit Auslieferung**? `--offline` prüft naturgemäß den
   Baum — wird das im Output klar, oder liest sich ein Baum-Grün wie ein
   Live-Grün?
4. Kennt er ein drittes Ergebniswort für **nicht messbar**? `--live` ist
   „best effort" — ein Netzausfall darf nicht als grün durchgehen.

## Vorgehen

1. Erst inventarisieren: die 56 Checks auflisten und je einordnen in
   *messend* / *behauptend* / *strukturell nicht rot-fähig*.
2. `--selftest` mit Fault Injection durch die **echte** `main()` (Konvention aus
   `auto_fulfill.py`, `sitemap_healthcheck.py`, `funnel_check.py`,
   `verify_rtd_chain.py`, `verify_ticket13_live.py`).
3. Rot-Fälle verlangen die **exakte Diagnosezeile**, nicht nur ein Stichwort,
   und werden gegen `Traceback` gefiltert (Exit-Code-Falle).
4. Mutationsprobe wie `_mutation_probe_t17.py`, inkl. rc-Wechsel 0→1→0 und
   sha256-genauer Wiederherstellung.
5. Wenn ein Check strukturell nicht rot werden kann: **entfernen oder
   reparieren** — ein Check, der immer grün ist, ist schlimmer als keiner, weil
   er die Zählung „56 ok" aufbläht.

## Warum das zählt

Die Zahl „56 ok" wird gelesen wie 56 bestandene Messungen. Nach dem Befund aus
Ticket 16 (ein Prüfschritt druckte jahrelang eine *Begründung* statt eines
Messwerts) und Ticket 17 (ein Prüfer sah nur 7 von 42 Seiten und nur 1 von 3
Pflichtlinks) ist die naheliegende Erwartung: ein Teil dieser 56 misst nichts.

## Ehrliche Abgrenzung

Kein Geldpfad — `verify.py` prüft Funnel-Struktur, Sitemap und `sales.log`.
Zurückstellen, sobald irgendetwas mit Sale-Bezug auf die Frontier kommt.
