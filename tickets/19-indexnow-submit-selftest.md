# Ticket 19 — `indexnow_submit.py`: der einzige autonome Traffic-Hebel ist ungeprüft

**Typ:** `wayfinder:task` (AFK)
**Status:** **GESCHLOSSEN 2026-08-05** — Selftest gebaut, 5 echte Defekte gefunden und behoben
**Eltern:** wayfinder_map.md
**Blockiert durch:** nichts (Ticket 18 geschlossen)

## Question

Bemerkt `scripts/indexnow_submit.py` überhaupt eine fehlgeschlagene Einreichung?

## Antwort: NEIN — an fünf Stellen nicht. Alle AM ALT-STAND AUSGEFÜHRT.

`scripts/_mutation_probe_t19.py` legt `HEAD:scripts/indexnow_submit.py` in eine
Sandbox und fährt dessen **echte `main()`** gegen injizierte Antworten. Gemessen,
nicht argumentiert:

| Fall | Alt-Stand | Befund |
|---|---|---|
| A1 URL lokal, live nicht vorhanden | `SUBMIT_OK` rc=0 | reicht eine **404-URL bei Bing ein** — genau das, was einen IndexNow-Key entwertet |
| A2 lokale Sitemap auf 1 statt 3 URLs geschrumpft | `SUBMIT_OK` rc=0 | **stille Schrumpfung**: weniger Einreichen sah aus wie Bestehen (Ticket-18-Klasse A1) |
| A3 Netz/DNS tot | `KEY_NICHT_LIVE` rc=1 | **falscher Defekt-Vorwurf** gegen die eigene, kerngesunde Key-Datei (Ticket-18-Klasse A2) |
| A4 Codes `[500, 403]` | `SUBMIT_403 … (kein URL-Fehler)` rc=2 | **403 maskiert den echten 500er** — Ausfall liest sich wie „Bing hat den Key nur noch nicht gecrawlt" |
| A5 Netzfehler beim Senden | `SUBMIT_FEHLER` rc=1 | Unmessbarkeit als Defekt-Claim ausgegeben |

**Die Ticket-Hypothese war falsch — und das ist gemessen:** vermutet wurde
`all()` über mehrere Batches als wahrscheinlichster Schwachpunkt. Fall D der
Sonde (`[200, 500]` über 2 Batches) ist am Alt-Stand **korrekt rot** geworden.
Der Batch-Pfad war gesund; die Löcher lagen woanders.

## Fix

- **Drei-Wege-Konvention** (Ticket 16/17/18) nachgezogen: `INDEXNOW_UNGEPRUEFT`
  (rc=2) für Netz/DNS-Ausfall — kein Defekt-Vorwurf gegen eigene URLs.
  Reihenfolge: **echter Defekt > unmessbar > 403 > OK**. `403` wandert auf rc=3
  (kein Aufrufer hing an rc=2 — über alle `.py/.md/.sh/.yml` gegrept).
- **Geltungsbereich** (Ticket-18-Lehre): vor jeder Einreichung wird die
  **LIVE**-Sitemap geholt und gegen den lokalen Baum gerechnet.
  `nur_lokal` (würde 404 einreichen) und `nur_live` (stille Schrumpfung) sind
  beide `INDEXNOW_DRIFT` rc=1 — **ohne** Einreichung. `--allow-drift` reicht
  bewusst nur die Schnittmenge ein (`SUBMIT_OK_TEILMENGE`).
- Leere Code-Liste ist rot (Leere-Schleife-Falle), `--check` dreiwertig,
  `vollzaehlig=ja/nein` wird gedruckt.

## >>> DEFEKT IM EIGENEN FIX — vom ECHTEN LAUF gefunden, nicht vom Selftest <<<

Der erste Live-Lauf nach dem Fix meldete `INDEXNOW_DRIFT lokal=1220 live=3`.
Die Site war kerngesund (`curl … sitemap.xml | grep -c "<loc>"` = **1220 live,
1220 lokal**). Ursache: `http()` schneidet **jeden** Body auf 400 Zeichen ab —
für Statusmeldungen gedacht, tödlich für ein Dokument. Die Live-Sitemap kam als
3 URLs an.

**Warum der Selftest das nicht fing:** die Attrappe lieferte Bodies
*ungekürzt* — sie war **großzügiger als die Realität**. Behoben an beiden Enden:
`http(..., maxlen=None)` für Dokumente, und `FakeNet` kürzt jetzt nach exakt
derselben Regel wie das Original. Neuer Fall: 60-URL-Sitemap (> 4 kB) muss
vollständig gelesen werden. Mutant **M7** stellt genau diesen Defekt wieder her.

## MEASURED (2026-08-05)

```
python scripts/indexnow_submit.py --selftest   -> 106/106 SELFTEST_OK
python scripts/_mutation_probe_t19.py          -> 29/29 MUTATION_PROBE_OK
    A1–A5 Alt-Stand blind + Gegenprobe der neuen Fassung je korrekt rot
    M1–M7 Mutanten alle rot, kein Traceback, sha256-genau wiederhergestellt
    rc-Wechsel 0 -> 1 -> 0
python scripts/indexnow_submit.py              -> SUBMIT_OK rc=0
    key HTTP 200 (Body == Key), lokal 1220 == live 1220, drift 0,
    vollzaehlig=ja, 1220 URLs -> HTTP 200
python scripts/verify.py                       -> VERIFY_OK (66 ok, 0 fail)
```

Der Selftest löst **keine** echte Einreichung aus (Attrappe protokolliert jeden
Aufruf; kein Fall geht gegen den Endpoint).

## Ehrliche Abgrenzung

`SUBMIT_OK` heißt weiterhin **angenommen, NICHT indexiert**. Die Wirkungsfrage
bleibt Ticket 5 (ab 2026-08-07) — die läuft jetzt aber gegen einen Einreicher,
dessen Rot-Fähigkeit bewiesen ist.
