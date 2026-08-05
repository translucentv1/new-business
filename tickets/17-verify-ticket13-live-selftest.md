# Ticket 17 — Der letzte ungeprüfte Prüfer: `verify_ticket13_live.py`

**Typ:** `wayfinder:task` (AFK)
**Status:** OFFEN — unblockiert, auf der Frontier
**Eltern:** wayfinder_map.md
**Blockiert durch:** nichts (Ticket 16 geschlossen)
**Prioritaet:** niedrig — Rechtslinks, nicht Geldpfad. Nur nehmen, wenn kein
Ticket mit hoeherem Informationswert offen ist.

## Question

Nach Ticket 15 (Grep ueber alle Skripte) und Ticket 16 ist
`verify_ticket13_live.py` das **letzte** Verifikationsskript ohne `--selftest`.
Es belegt live, dass Impressum/AGB/Datenschutz-Links auf den ausgelieferten
Seiten stehen und dass frueher verwaiste Landingpages jetzt HTTP 200 liefern —
aber niemand hat gezeigt, dass es einen Defekt **bemerkt**.

Konkret zu klaeren:
1. Wird es rot, wenn eine gepruefte URL 404 liefert?
2. Wird es rot, wenn der Datenschutz-Link im **live abgerufenen Body** fehlt?
3. Faellt es auf die **Fette-404-Falle** herein (GitHub-Pages-404 ist 9379 B,
   groesser als jede echte Seite — prueft das Skript `%{http_code}` oder Groesse)?
4. Verwechselt es „Link im lokalen Baum" mit „Link im live ausgelieferten Body"?
   Genau diese Verwechslung war der Kern von Ticket 13.

## Warum das (nur mittel) zaehlt

Ein blinder Rechtslink-Pruefer kostet kein Geld, aber er hat schon einmal eine
Luecke verdeckt: Ticket 13 fand den Datenschutz-Link auf **33 von 38** Seiten
fehlend, obwohl jede Stichprobe gruen aussah. Abmahnrisiko ist real, aber
niedriger priorisiert als der Geldpfad.

## Vorgehen

1. `--selftest` mit Fault Injection durch die **echte** `main()` (Konvention aus
   `auto_fulfill.py`, `sitemap_healthcheck.py`, `funnel_check.py`,
   `verify_rtd_chain.py`): nur die HTTP-Antwort injizieren, kein Reimplementat.
2. Rot-Faelle mindestens: 404 auf einer Pflicht-URL, Body ohne
   Datenschutz-Link, Body mit 9379-B-404-Inhalt (Fette-404-Falle),
   Netzfehler (-1), leere URL-Liste (kein stiller Gruen-Fall — der Defekt aus
   Ticket 16!).
3. Jeden Rot-Fall gegen `Traceback` filtern (Exit-Code-Falle).
4. Mutationsprobe wie `_mutation_probe_t16.py`, inkl. rc-Wechsel 0→1→0 und
   sha256-genauer Wiederherstellung.
5. Danach ein echter Lauf zur Kontrolle.

## Erwartetes Ergebnis

Entweder ein belegbar rot-faehiger Pruefer — oder ein weiterer echter Defekt
derselben Klasse. Damit waere die Konvention „jedes Verifikationsskript hat
einen Selftest" erstmals **vollzaehlig** erfuellt und nicht nur geglaubt.
