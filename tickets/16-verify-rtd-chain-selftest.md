# Ticket 16 — Kann der Torwaechter des Geldpfads rot werden?

**Typ:** `wayfinder:task` (AFK)
**Status:** OFFEN — unblockiert, auf der Frontier
**Eltern:** wayfinder_map.md
**Blockiert durch:** nichts (Ticket 15 geschlossen)

## Question

`verify_rtd_chain.py` entscheidet mit `KETTE_OK`, ob der Geldpfad intakt ist —
jeder Tick zitiert dieses Wort als Beleg. Das Skript hat aber **keinen
`--selftest`** (MEASURED 2026-08-05, Ticket 15): niemand hat je gezeigt, dass es
einen kaputten Kaufpfad ueberhaupt **bemerkt**. Wuerde es rot, wenn ein Link
deaktiviert waere, der Preis auf 0 stuende, das Pflichtfeld `anfrage` fehlte
oder der Redirect auf eine tote Domain zeigte?

Gleiche Klasse wie Ticket 14 (Sitemap-Pruefer) und Ticket 15 (Besucher-Zaehler):
ein Pruefer, der nie rot werden kann, winkt einen kaputten Geldpfad durch.

## Warum das zaehlt

`KETTE_OK` ist die Aussage, auf die sich seit Wochen jeder Statusbericht
stuetzt. Sie deckt die **einzige Einnahmequelle** ab. Solange der Pruefer
ungeprueft ist, ist „der Kaufpfad ist intakt" streng genommen ASSUMED.

## Vorgehen

1. `--selftest` mit Fault Injection durch die **echte** `main()` bauen
   (Konvention aus `auto_fulfill.py`, `sitemap_healthcheck.py`, `funnel_check.py`):
   nur die Stripe-Antwort injizieren, kein Reimplementat.
2. Rot-Faelle mindestens fuer: Link inaktiv (`active=False`), `livemode=False`,
   `unit_amount=0`/fehlend, Pflichtfeld `anfrage` fehlt, Redirect-URL falsche
   Domain, Hash-Paritaet verletzt, 0 Links gefunden.
3. Jeden Rot-Fall zusaetzlich gegen `Traceback` filtern (Exit-Code-Falle:
   ein Absturz ist keine Erkennung).
4. Mutationsprobe wie `_mutation_probe_t15.py`: Produktivcode mutieren,
   rc-Wechsel 0→1→0 belegen, Datei per sha256 bitgenau wiederherstellen.
5. **Die 3 LIVE-Links dabei NICHT anfassen** — Ticket 7 hat gezeigt, wie schnell
   man an der einzigen Einnahmequelle etwas kaputtmacht. Alles gegen injizierte
   Antworten testen, danach ein echter Lauf zur Kontrolle.

## Danach noch offen

`verify_ticket13_live.py` (Live-Beleg Rechtslinks) hat ebenfalls keinen
Selftest — geringere Tragweite, aber dieselbe Klasse.
