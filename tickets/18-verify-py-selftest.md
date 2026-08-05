# Ticket 18 — `scripts/verify.py`: das kanonische Tor ist ungeprüft

**Typ:** `wayfinder:task` (AFK)
**Status:** GESCHLOSSEN 2026-08-05 (Tick 5)
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

---

## Auflösung (2026-08-05, Tick 5) — MEASURED

**Antwort auf die Frage: Nein, das kanonische Tor bemerkte einen Defekt nicht
zuverlässig. Drei echte Defekte, nicht nur ein fehlender Test.**

Alle drei wurden **am Alt-Stand ausgeführt**, nicht argumentiert
(`scripts/_mutation_probe_t18.py`, Teil A holt `HEAD:scripts/verify.py` per
`git show` und fährt dessen echte `main()`):

**A1 — Stille Schrumpfung der Prüffläche (der schwerste Befund).**
Der Deckungs-Check der Blogseiten prüfte nur `te.KEYWORDS[0]`, nicht die Liste.
Alt-Stand mit `KEYWORDS` von 37 auf 1 gekürzt → `rc=0`, **„20 ok, 0 fail"** —
grün, obwohl 36 Seiten überhaupt nicht mehr geprüft wurden. Damit war die Zahl
„56 ok" nie eine feste Prüffläche: sie skaliert mit dem Baum, und ein Schrumpfen
sah aus wie ein bestandener Lauf. Genau die Klasse aus Ticket 17 (eingefrorene
Stichprobe), nur umgekehrt — hier schrumpft die Zielmenge statt zu veralten.

**A2 — Netzausfall wurde als Seitendefekt gemeldet.**
`--live` kannte kein drittes Ergebniswort: bei totem Netz druckte der Alt-Stand
`FAIL  live: …` und `rc=1` — ein **Defekt-Claim über eine gesunde Seite**. Die
Konvention aus Ticket 16/17 (`KETTE_UNGEPRUEFT` / `LIVE_UNGEPRUEFT`) fehlte hier.

**A3 — Ergebnislisten wurden nicht zurückgesetzt.**
Zwei `main()`-Läufe im selben Prozess: **58 → 116 ok**. Ehrliche Einordnung:
im Produktivlauf wird `main()` genau einmal aufgerufen, der Defekt ist also
**latent** — er hätte aber jede Test-Harness um dieses Tor still verfälscht
(und tut das bei einem Selftest, der `main()` mehrfach fährt, sofort).

### Fix

- `--selftest` mit Fault Injection durch die **echte** `main()`
  (`scripts/_verify_selftest.py`), Konvention aus Ticket 14–17.
- Deckungs-Check über **alle** `KEYWORDS` statt `KEYWORDS[0]`.
- **Leere-Schleife-Falle** geschlossen: leere `KEYWORDS`-Liste ist rot
  (der Alt-Stand lief hier in einen `IndexError`).
- Drittes Ergebniswort **`VERIFY_UNGEPRUEFT` (rc=2)**; echter Defekt schlägt
  Unmessbarkeit (Vorrang-Regel aus Ticket 17, als eigener Rot-Fall getestet).
- Ergebnislisten werden pro `main()`-Lauf zurückgesetzt.
- **Geltungsbereich wird im Output benannt** („lokaler Baum (kein Netz)" vs
  „lokaler Baum + LIVE-Auslieferung") — Frage 3 des Tickets: ein Baum-Grün las
  sich vorher wie ein Live-Grün.
- Rot-Fälle assertieren gegen die **exakte Diagnosezeile** und filtern auf
  `Traceback` (Exit-Code-Falle).

### Belege (alle heute ausgeführt)

| Messung | Ergebnis |
|---|---|
| `python scripts/verify.py --selftest` | **30/30 SELFTEST_OK**, rc=0 |
| `python scripts/_mutation_probe_t18.py` | **11/11 MUTATION_PROBE_OK**, rc=0 |
| Alt-Stand-Proben A1/A2/A3 | alle drei reproduziert (s. o.) |
| Mutanten der neuen Fassung | **5/5 rot**, je mit erwarteter Diagnosezeile |
| Wiederherstellung nach Mutation | sha256-genau (`a6b7e8cdaf122005`), rc-Wechsel 0→1→0 |
| `python scripts/verify.py --offline` | **65 ok, 0 fail, 0 skip, 0 ungeprueft** → VERIFY_OK |
| `python scripts/verify.py --live` | **72 ok, 0 fail, 0 skip, 0 ungeprueft** → VERIFY_OK |

Frage 1 des Tickets (Inventar messend/behauptend) ist damit **operativ**
beantwortet: der Selftest fährt 20 Rot-Fälle durch die echte `main()`; der
Mutant „`check()` kann nicht mehr rot werden" macht **20 Rot-Meldungen** — d. h.
20 Checks sind nachweislich rot-fähig. Ein Check, der strukturell nicht rot
werden kann, ist damit sichtbar, statt die Zählung aufzublähen.

### Ehrliche Grenzen

- Die Prüffläche ist **tree-abhängig** (65 offline / 72 live heute, nicht „56").
  Der Selftest prüft jetzt, dass sie **vollständig** ist, nicht dass sie eine
  bestimmte Zahl hat.
- Getestet wird gegen **injizierte** Bäume und Antworten; die LIVE-Auslieferung
  wird für keinen Test kaputtgemacht.
- Kein Geldpfad: `verify.py` prüft Funnel-Struktur, Sitemap und `sales.log`.
  Der Geldpfad hängt weiterhin an `verify_rtd_chain.py` (Ticket 16).

**Commit:** `d5e0f79` — im `origin/gh-pages`-Tree verifiziert, 0 unpushed.
