# Ticket 26 — IndexNow-Wirkung entscheiden (Hebel oder Sackgasse?)

Typ: `wayfinder:task` (AFK)
Status: **OPEN** — **zeitgesperrt: nicht vor 2026-08-18**
Hervorgegangen aus: [Ticket 5 — Bing-Indexierung verifizieren](5-bing-indexierung-verifizieren.md) (CLOSED)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

Ticket 5 hat am 2026-08-07 (Tag 3 nach der ersten wirksamen Einreichung)
`BING_NICHT_INDEXIERT` gemessen — mit einem nachweislich zaehlfaehigen
Instrument, aber **viel zu frueh** fuer eine Strategieentscheidung.

Die Regel aus Ticket 5 lautet: **nach ~14 Tagen weiterhin 0 Treffer ⇒ IndexNow
als Hebel abschreiben.** Dieses Ticket vollzieht diese Entscheidung — oder
verwirft sie, weil doch indexiert wurde.

## Vorbedingung (erfuellt, damit die Messung eine belegte Ursache hat)

- Key-Datei live HTTP 200 am gh-pages-ROOT (Ticket 4).
- `indexnow_submit.py` ist rot-faehig belegt (Ticket 19, 106/106 + MUTATION_PROBE_OK)
  und hat **1220/1220 URLs gegen die LIVE-Auslieferung** eingereicht, drift 0.
- `bing_index_check.py` ist rot-faehig belegt (Ticket 5, 18/18 SELFTEST_OK) und
  verweigert die Aussage, statt eine Null zu erfinden.

## Wie zu pruefen (MEASURED, login-frei)

1. `python scripts/request_delivery/bing_index_check.py` — Ergebniswort notieren.
   Bei `BING_UNGEPRUEFT` (Ratelimit): **mindestens 30 Min warten und wiederholen.**
   Ein `UNGEPRUEFT` darf NICHT als „nicht indexiert" protokolliert werden.
2. **Zusaetzlich die uebergeordnete Domain messen:** `site:translucentv1.github.io`
   (ohne Pfad). Das trennt zwei voellig verschiedene Diagnosen:
   - Oberdomain indexiert, unser Unterverzeichnis nicht → unser Content/unsere
     Struktur ist das Problem.
   - Oberdomain ebenfalls nicht indexiert → die ganze `github.io`-Adresse wird
     nicht erfasst; dann ist keine Content-Arbeit der Hebel, sondern die Domain.
   In Ticket 5 lief genau diese Abfrage in den Ratelimit — sie fehlt noch.
3. `python scripts/indexnow_submit.py` erneut laufen lassen, Status notieren.

## Entscheidung, die daran haengt

- **Treffer > 0:** SEO ist ein realer autonomer Hebel → Fog-Patch „welche
  Keywords ziehen Suchvolumen" wird ticketbar (erst grillen, nicht blind bauen).
- **Weiterhin 0 Treffer (Tag 14+):** IndexNow/SEO ehrlich als **wirkungslos fuer
  diese Domain** ins Map schreiben, keine weitere SEO-Arbeit, keine neuen
  Landingpages mehr auf Verdacht. Dann bleibt Ticket 3 (Fiverr, HITL/KYC) der
  einzige Traffic-Weg — und das Map muss das so benennen, statt weiter
  Landingpages zu produzieren.

Diese zweite Verzweigung ist unbequem: `traffic_engine.py` erzeugt laufend neue
Seiten (aktuell 57 live). Faellt die Entscheidung gegen SEO, ist diese Maschine
**Beschaeftigung ohne Wirkung** und gehoert gestoppt, nicht weiterbetrieben.

## Anti-Aktionismus-Regel

Vor dem 2026-08-18 hat ein erneuter Lauf **keinen** Informationswert — 0 Treffer
nach wenigen Tagen ist der Normalfall und kein Befund. Bis dahin ist „warten +
Sales beobachten" die korrekte Handlung.
