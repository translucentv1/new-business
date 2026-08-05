# Ticket 17 — Der letzte ungeprüfte Prüfer: `verify_ticket13_live.py`

**Typ:** `wayfinder:task` (AFK)
**Status:** GESCHLOSSEN 2026-08-05 (Tick 4)
**Eltern:** wayfinder_map.md

## Question

Bemerkt `verify_ticket13_live.py` überhaupt einen Defekt? Es belegt live, dass
Impressum/AGB/Datenschutz-Links auf den ausgelieferten Seiten stehen — aber
niemand hatte gezeigt, dass es rot werden *kann*.

## Antwort: NEIN — und es waren zwei echte Defekte, kein bloß fehlender Test

### Defekt A — die 7er-Stichprobe (Ticket-13-Falle auf sich selbst angewandt)

`STICHPROBE` war eine **hartkodierte Liste von 7 Seiten**, während
`legal_link_audit.py` im Baum **42** prüft. 35 Seiten wurden live **nie**
angefasst. Genau die Teil-Vollständigkeits-Falle, gegen die dieses Skript
gebaut worden war.

Verschärfend: `traffic_engine.py` erzeugt laufend neue Landingpages. Die
Stichprobe war auf dem Stand von Ticket 13 eingefroren — **jede künftige
Traffic-Seite wäre am Live-Check vorbeigelaufen.**

AUSGEFÜHRT, nicht argumentiert (`_mutation_probe_t17.py`, Teil A1): der
Alt-Stand `68946f0` läuft gegen eine Auslieferung, in der
`blog/arbeitszeugnis-schreiben-lassen-ki.html` **404** liefert
→ `rc=0, LIVE_OK -> war BLIND`. Neue Fassung gegen dieselbe Auslieferung:
`rc=1, LIVE_DEFEKT`, Seite namentlich benannt.

### Defekt B — es prüfte nur EINEN von DREI Pflichtlinks

`NEEDLE = "datenschutz.html"`. Impressum und AGB wurden im ausgelieferten Body
**überhaupt nicht** geprüft — obwohl beide § 5 DDG / Art. 13 DSGVO tragen und
das Skript exakt dafür existiert.

AUSGEFÜHRT (Teil A2): Alt-Stand gegen ein `index.html`, das live **ohne
Impressum-Link** ausgeliefert wird → `rc=0, LIVE_OK`. Die Seite lag *innerhalb*
der Stichprobe — die Blindheit war also nicht nur eine Abdeckungs-, sondern eine
Inhaltslücke.

## Fix

- **Zielmenge aus dem Baum abgeleitet** statt hartkodiert (gleiche Exempt-Regel
  wie `legal_link_audit.is_exempt`, damit die zwei Prüfer nicht driften).
  Neue Traffic-Seiten sind ab sofort automatisch abgedeckt.
- **Alle drei Pflichtlinks** werden im ausgelieferten Body geprüft.
- **Soft-404-Erkennung**: HTTP 200 mit `Page not found`/`File not found` im Body
  ist jetzt rot. Größe bleibt als Merkmal draußen — das GitHub-404 ist mit
  9379 B fetter als jede echte Seite (Fette-404-Falle).
- **Leere Zielmenge ist nicht grün** (Leere-Schleife-Falle aus Ticket 16).
- **Drittes Ergebniswort `LIVE_UNGEPRUEFT` (rc=2)** für Netzfehler — ein Timeout
  ist weder Gesundheit noch Defekt. Ein *echter* Defekt schlägt Unmessbarkeit
  (sonst versteckt ein Timeout einen Defekt).
- `urllib.error` explizit importiert (funktionierte vorher nur zufällig über
  einen Seiteneffekt von `import urllib.request`).
- Nebenläufig (8 Threads): 47 Seiten in **1,2 s** statt sequenziell.

## MEASURED

| Messung | Ergebnis |
|---|---|
| `--selftest` | **18/18 SELFTEST_OK** (alle Rot-Fälle durch die *echte* `main()`, gegen `Traceback` gefiltert) |
| `_mutation_probe_t17.py` A1 | Alt-Stand `rc=0 LIVE_OK` bei 404 außerhalb der Stichprobe → **war blind** |
| `_mutation_probe_t17.py` A2 | Alt-Stand `rc=0 LIVE_OK` bei fehlendem Impressum-Link → **war blind** |
| `_mutation_probe_t17.py` B | **MUTATION_PROBE_OK**, 4/4 Mutanten rot, kein Traceback, sha256-genaue Wiederherstellung, rc-Wechsel 0→1→0 |
| echter Live-Lauf | **LIVE_OK**, 47 Seiten vollzählig, 1,2 s |
| unabhängige Gegenmessung | 42/42 Seiten live HTTP 200 **mit allen 3 Rechtslinks**, 0 Defekte |

Die Rot-Fälle verlangen die **exakte Diagnosezeile** (`! blog/a.html:
Rechtslink fehlt: datenschutz.html`), nicht bloß das Vorkommen eines Wortes —
sonst besteht ein Test auch dann, wenn der Prüfer aus dem falschen Grund rot wird.

## Ehrliche Grenze

Geprüft ist die **Anwesenheit** der Links im ausgelieferten Body, nicht ihre
Abmahnsicherheit. Die ladungsfähige Postanschrift bleibt USER-Blocker. Getestet
wird gegen **injizierte** HTTP-Antworten; der echte Server wird nie kaputtgemacht.

## Prämisse des Tickets: FALSIFIZIERT

Das Ticket behauptete, `verify_ticket13_live.py` sei das **letzte**
Verifikationsskript ohne `--selftest`. Vollzählig über alle Skripte gegrept
stimmt das nicht: **`scripts/verify.py`** nennt sich selbst „kanonische
Verifikation für new-business", läuft mit 56 Checks (`rc=0`, MEASURED) und hat
keinen Selftest. → **Ticket 18**.

Damit ist die Teil-Vollständigkeits-Falle bei Claims über die eigene
Werkzeugkiste zum **dritten Mal** aufgetreten (Ticket 14 → 15 → 17). Der Grep
allein reichte nicht — er muss über *alle* Skripte laufen **und** jeder Treffer
muss danach beurteilt werden, ob er ein stehendes Tor oder eine Ad-hoc-Sonde ist
(`check_key.py` = 23-Zeilen-Sonde, zu Recht ohne Selftest;
`scripts/verify.py` = stehendes Tor, zu Unrecht ohne).
