# Ticket 19 — `indexnow_submit.py`: der einzige autonome Traffic-Hebel ist ungeprüft

**Typ:** `wayfinder:task` (AFK)
**Status:** OFFEN — unblockiert, auf der Frontier
**Eltern:** wayfinder_map.md
**Blockiert durch:** nichts (Ticket 18 geschlossen)
**Priorität:** **hoch** — höher als Ticket 18 es war. Das ist zwar kein Geldpfad,
aber der **einzige autonome Traffic-Hebel**, und Traffic ist der einzige
verbliebene Blocker zum ersten Sale (BESUCHER = 0).

## Question

Bemerkt `scripts/indexnow_submit.py` überhaupt eine fehlgeschlagene Einreichung?

Es druckt `ERGEBNIS: SUBMIT_OK` und ist damit — nach dem Grep über alle 43
Skripte (MEASURED 2026-08-05) — **das letzte stehende Tor ohne `--selftest`**.
Die einzigen zwei anderen Skripte ohne Selftest, die ein Ergebniswort drucken,
sind Ad-hoc-Sonden: `measure_tier_diff.py` (Einmalmessung für Ticket 12) und
`probe_consent_collection.py` (Einmalprobe für Ticket 7) — die brauchen keinen.

**Warum das besonders zählt:** Genau dieser Pfad hat schon einmal **11 Tage lang
nichts getan, während alles grün aussah** — die Key-Datei lag auf `master` unter
`docs/`, live 404, IndexNow war seit dem 24.07. nie funktionsfähig (Ticket 4).
Ein `SUBMIT_OK`, das einen Fehlschlag nicht bemerkt, würde denselben Ausfall
erneut verdecken — diesmal an der einzigen Stelle, die ohne Nutzer-Login
überhaupt Besucher bringen kann.

**Zusätzliche Dringlichkeit:** Ticket 5 (Bing-Indexierung verifizieren) wird am
**2026-08-07** zeitentsperrt. Wenn der Einreicher blind ist, misst Ticket 5 eine
Wirkung, deren Ursache nie stattgefunden hat — dann ist auch dessen Ergebnis
wertlos. Ticket 19 sollte **vor** Ticket 5 laufen.

## Ehrlicher Ausgangsbefund (Code-Lektüre, KEIN Test)

Damit der nächste Tick nicht zu viel erwartet: die Struktur liest sich bereits
defensiv, im Gegensatz zu den Alt-Ständen aus Ticket 16–18.

- `http()` fängt `HTTPError` **und** Netzwerkfehler ab und liefert den Status
  zurück, statt zu werfen (Zeile 42–51).
- `check_key_live()` vergleicht den Body **exakt** gegen den Key (Zeile 54–57).
- `main()` hat getrennte Zweige: `KEY_NICHT_LIVE`, `KEINE_URLS`,
  `SUBMIT_403_KEY_NOCH_NICHT_GECRAWLT`, `SUBMIT_FEHLER` (Zeile 97–118).
- Die **Leere-Schleife-Falle** (Ticket 16) scheint durch den `KEINE_URLS`-Zweig
  vorab abgefangen — `all([])` wäre sonst `True` und damit grün bei null URLs.

**Das ist Code-Lektüre, kein Beweis.** Exakt dieselbe Lage wie bei
`sitemap_healthcheck.py` in Ticket 14: inhaltlich korrekt, aber niemand hatte
gezeigt, dass es einen Defekt *bemerkt*. Die Frage bleibt offen, bis sie
ausgeführt ist.

## Vorgehen

1. `--selftest` mit Fault Injection durch die **echte** `main()` (Konvention aus
   Ticket 14–18: nur die HTTP-Antwort wird injiziert, kein Reimplementat).
2. Rot-Fälle, mindestens:
   - Key-Datei live 404 → muss `KEY_NICHT_LIVE` sein, nicht grün
   - Key-Datei live 200, aber **falscher Body** → rot
   - Submit liefert 403 → eigenes Ergebniswort, **kein** `SUBMIT_OK`
   - Submit liefert 500 / 429 → `SUBMIT_FEHLER`
   - **gemischte Batches** (ein Batch 200, einer 500) → rot, nicht grün
     *(die `all()`-Prüfung über mehrere Batches ist der wahrscheinlichste
     Schwachpunkt — bei 1220 URLs und `BATCH` < 1220 laufen mehrere Runden)*
   - **leere Sitemap** → `KEINE_URLS`, nicht `SUBMIT_OK`
   - **Netzfehler/DNS tot** → drittes Ergebniswort, kein Defekt-Claim gegen die
     eigenen URLs (Konvention `*_UNGEPRUEFT` rc=2 aus Ticket 16/17/18)
3. Rot-Fälle gegen die **exakte Diagnosezeile** assertieren und auf `Traceback`
   filtern (Exit-Code-Falle).
4. Mutationsprobe wie `_mutation_probe_t18.py`, inkl. Alt-Stand-Probe per
   `git show`, rc-Wechsel 0→1→0 und sha256-genauer Wiederherstellung.
5. Prüfen, ob die **Sitemap-Herkunft** stimmt: `sitemap_urls()` liest lokal —
   eingereicht werden müssen aber die **ausgelieferten** URLs. Ein Drift zwischen
   Baum und Auslieferung würde 1220 URLs einreichen, die es live nicht gibt
   (Geltungsbereich-Falle aus Ticket 18).

## Ehrliche Abgrenzung

- Kein Geldpfad. `SUBMIT_OK` heißt weiterhin **angenommen, NICHT indexiert** —
  daran ändert auch ein grüner Selftest nichts. Die Wirkungsfrage ist Ticket 5.
- Der Selftest darf **keine echte Einreichung** auslösen (kein Zumüllen des
  IndexNow-Endpunkts mit Testdaten) — nur injizierte Antworten.
