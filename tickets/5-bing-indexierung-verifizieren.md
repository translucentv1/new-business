# Ticket 5 — Bing-Indexierung verifizieren (Wirkungsnachweis IndexNow)

Typ: `wayfinder:task` (AFK)
Status: **OPEN** — auf Frontier, aber **zeitgesperrt: nicht vor 2026-08-07**
Blockiert durch: [Ticket 4 — IndexNow-Indexierung](4-indexnow-indexierung.md) (CLOSED)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

IndexNow hat die 1205 URLs am 2026-08-04 angenommen (HTTP 202/200 MEASURED).
**Angenommen ≠ indexiert.** Nimmt Bing die Seiten tatsaechlich in den Index —
und kommt daraus messbarer Traffic auf `rtd.html`?

Damit haengt die Kernfrage des Maps zusammen: ist SEO ohne Nutzer-Account ein
echter Traffic-Hebel, oder bleibt Ticket 3 (Fiverr, HITL) der einzige Weg?

## Wie zu pruefen (MEASURED, kein Login noetig)

1. Bing-Suche ohne Account abfragen und Treffer zaehlen, z. B.
   `site:translucentv1.github.io/new-business` — Trefferzahl protokollieren.
   0 Treffer = noch nicht indexiert (normal in den ersten Tagen).
2. `python scripts/indexnow_submit.py` erneut laufen lassen; Status-Code notieren.
   403 = Key-Datei noch nicht gecrawlt (kein URL-Fehler) → weiter warten.
3. Ergebnis in dieses Ticket schreiben.

## Entscheidung, die daran haengt

- **Treffer > 0:** SEO ist ein realer autonomer Hebel → Ticket 2 korrigieren,
  Content/Keywords als naechste Initiative pruefen (grillen, nicht blind bauen).
- **Nach ~14 Tagen weiterhin 0 Treffer:** IndexNow als Hebel abschreiben,
  ehrlich als "wirkungslos fuer diese Domain" ins Map schreiben, keine weitere
  SEO-Arbeit — dann bleibt Ticket 3 (Fiverr, Nutzer) der einzige Weg.

## Anti-Aktionismus-Regel

Vor dem 2026-08-07 hat ein erneuter Lauf **keinen** Informationswert.
Bis dahin ist "warten + Sales beobachten" die korrekte Handlung.
