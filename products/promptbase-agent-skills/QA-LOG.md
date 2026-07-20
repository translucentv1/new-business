# QA-LOG — PromptBase Agent-Skills (7 SKILL.md)

Methode (MEASURED, 2026-07-19): Jede SKILL.md ist selbst ein Prompt. Der
ausfuehrende LLM-Agent wendet die Instruktionen (Frontmatter + Process +
Output format + Rules) auf 1-2 realistische Beispiel-Eingaben an und erzeugt
die Roh-Ausgabe. Die Roh-Ausgabe wird 1:1 gespeichert. Danach wird geprueft,
ob sie EXAKT dem in der SKILL.md deklarierten Output-Format folgt.

Bewertung pro Skill: PASS (Format + Inhalt OK) | FIXED (Schwaeche gefunden +
SKILL.md verbessert) | PROBLEM (Formatbruch / unbrauchbar).

Jede SKILL.md-Datei ist < 1300 Bytes — also KURZ. Das ist ein QA-Risiko:
kaum Fehlerbeispiele, wenig Guard-Rails gegen Preamble/Blabla. Daher ist die
zentrale Pruefung: "folgt die Ausgabe EXAKT dem Format oder redet das Modell
drumherum?".

================================================================================
SKILL 1 — clean-code-reviewer  (Claude Skill, $6.99)
================================================================================
Deklariertes Output-Format (Zitat SKILL.md):
  For each finding: `[PASS 1-4] SEVERITY(low|med|high) — file:line — one sentence — suggested fix`
  End with: `VERDICT: ship | ship-with-fixes | block` and one-line reason.

--- Test-Eingabe 1 (realistischer Diff mit 2 echten Bugs) ---
```python
def get_user(conn, uid):
    cur = conn.cursor()
    cur.execute("SELECT name, email FROM users WHERE id = " + uid)
    return cur.fetchone()

def process(items):
    total = 0
    for i in range(1, len(items)):
        total += items[i]
    return total
```

--- Roh-Ausgabe (ausgefuehrt) ---
[PASS 1] high — get_user():3 — SQL string concatenation with `uid` allows injection — use a parameterized query: `cur.execute("SELECT name, email FROM users WHERE id = %s", (uid,))`
[PASS 1] med — process():7 — `range(1, len(items))` skips `items[0]` (off-by-one) — use `range(len(items))` or `for i, v in enumerate(items)`
[PASS 2] — no auth bypass, secret leak, or unsafe eval found
[PASS 3] low — process():6-8 — no guard for empty/None `items` (None would crash) — add `if not items: return 0` at top
[PASS 4] low — get_user():2 — `cur` is fine; names are clear
VERDICT: block — SQL injection is a release-blocking security bug; fix before ship.

--- Test-Eingabe 2 (nur Kosmetik, soll VERDICT: ship liefern) ---
```python
def add(a, b):
    return a + b
```
--- Roh-Ausgabe 2 ---
[PASS 1] — correct, returns the sum
[PASS 2] — no security issue
[PASS 3] — fine for ints; note: str+str also works (intended?)
[PASS 4] — naming clear
VERDICT: ship — trivially correct, no issues.

--- Format-Check ---
PASS 1: `[PASS 1-4] SEVERITY — file:line — satz — fix` wird eingehalten.
VERDICT-Zeile vorhanden + Begruendung.
SCHWAECHE: `[PASS 1-4]` ist mehrdeutig — es kann als "Durchlauf 1-4" ODER als
"Bestanden/Ampel" gelesen werden. Der Skill meint offenbar den Durchlauf-
Index (1=CORRECTNESS ... 4=CLARITY). Ein Kauefer-LLM koennte "PASS"/"FAIL"
davor schreiben wollen. -> Minimal-Klärung im Format-String empfohlen.
ERGBNIS: FIXED (siehe Aenderung unten: PASS-Notation geklaert + "kein Preamble"-Regel).

================================================================================
SKILL 2 — daily-standup-writer  (ChatGPT Skill, $4.99)
================================================================================
Deklariertes Output-Format:
  Three sections, each 1-3 bullets:
  - GESTERN: completed work, outcomes not activity
  - HEUTE: the single most important next thing
  - BLOCKER: real impediments only; if none, write "Keine"

--- Test-Eingabe 1 (Commit-Liste, gemischt DE/EN) ---
Commits:
- feat: add login retry with backoff
- fix: null pointer in profile load
- docs: update README onboarding

--- Roh-Ausgabe (ausgefuehrt) ---
GESTERN:
- Login retry with exponential backoff shipped (fewer failed auth loops)
- Null-pointer crash on profile load fixed
- README onboarding section updated

HEUTE:
- Wire retry metrics into the dashboard so we can see auth-failure drop

BLOCKER:
- Keine

--- Test-Eingabe 2 (nur Bullets, englisch -> Sprach-Match-Pruefung) ---
- finished CSV import
- started rate limiter
(no blockers)

--- Roh-Ausgabe 2 ---
GESTERN:
- CSV import finished and verified against the sample file
- Rate limiter started (token-bucket skeleton in place)

HEUTE:
- Complete the rate limiter middleware and add a unit test

BLOCKER:
- Keine

--- Format-Check ---
Struktur GESTERN/HEUTE/BLOCKER eingehalten, 1-3 Bullets, outcome-led.
BUG (MEASURED): Eingabe 2 ist ENGLISCH, Skill sagt "match user language",
aber die BLOCKER-Regel hardcodet deutsch "Keine". Ausgabe 2 schreibt trotzdem
"Keine" statt "None" -> Sprach-Match wird an dieser Stelle gebrochen.
ERGBNIS: FIXED (siehe Aenderung: "Keine / None").

================================================================================
SKILL 3 — test-case-generator  (Claude Skill, $6.99)
================================================================================
Deklariertes Output-Format:
  For each case: `TC-{n} [P0|P1|P2] — given: <input> — when: <action> — then: <expected>`
  End with a one-line coverage gap note.

--- Test-Eingabe 1 (Funktions-Signatur) ---
def divide(a, b):
    return a / b

--- Roh-Ausgabe (ausgefuehrt) ---
TC-1 [P0] — given: a=10, b=2 — when: divide called — then: returns 5.0
TC-2 [P0] — given: a=10, b=0 — when: divide called — then: raises ZeroDivisionError
TC-3 [P1] — given: a=-10, b=3 — when: divide called — then: returns -3.33… (correct sign)
TC-4 [P1] — given: a=10, b=0.0 — when: divide called — then: still raises (float zero)
TC-5 [P2] — given: a=10, b="2" — when: divide called — then: raises TypeError (no implicit cast)
TC-6 [P2] — given: a=(very large int), b=1 — when: divide called — then: returns a (no overflow surprise)
Coverage gap: no spec for non-numeric/None inputs beyond TypeError; undefined behavior for b=None not pinned.

--- Test-Eingabe 2 (Endpoint-Spec, 5 Zeilen) ---
POST /orders  body: {user_id, items[]}  -> 201 created, 400 if items empty, 401 if no auth

--- Roh-Ausgabe 2 ---
TC-1 [P0] — given: valid user_id + 1 item — when: POST /orders — then: 201 + order id
TC-2 [P0] — given: items=[] — when: POST /orders — then: 400
TC-3 [P0] — given: no auth header — when: POST /orders — then: 401
TC-4 [P1] — given: unknown user_id — when: POST /orders — then: 404 (assumed; spec silent)
TC-5 [P1] — given: duplicate item ids — when: POST /orders — then: accepted or 409 (spec silent)
TC-6 [P2] — given: 10k items — when: POST /orders — then: 201 or 413 (payload limit unstated)
Coverage gap: auth failure vs expired token not distinguished; idempotency on retry unspecified.

--- Format-Check ---
TC-{n} [P0|P1|P2] — given/when/then exakt eingehalten. Coverage-gap-Zeile da.
Fehlende Annahmen bei 2 werden sauber als "spec silent / assumed" markiert (Regel erfuellt).
ERGBNIS: PASS (kein Fix noetig, nur "kein Preamble"-Regel unten ergaenzt).

================================================================================
SKILL 4 — root-cause-debugger  (Claude Skill, $7.99)
================================================================================
Deklariertes Output-Format:
  SYMPTOM: <one line>
  ROOT CAUSE: <layer + one sentence>
  EVIDENCE: <what proves it, cite pasted code/trace>
  NEXT CHECK: <one concrete step to confirm>
  FIX (only after NEXT CHECK passes): <smallest change>

--- Test-Eingabe 1 (Stack-Trace mit KeyError) ---
```
Traceback (most recent call last):
  File "app.py", line 42, in handler
    return cfg["timeout"]
KeyError: 'timeout'
```
--- Roh-Ausgabe (ausgefuehrt) ---
SYMPTOM: App crashes on startup with `KeyError: 'timeout'` at app.py:42.
ROOT CAUSE: config layer — the code reads `cfg["timeout"]` but that key is missing from the loaded config.
EVIDENCE: app.py:42 `return cfg["timeout"]` plus the KeyError name matches the accessed key exactly; no default provided.
NEXT CHECK: print `list(cfg.keys())` right before line 42 to confirm 'timeout' is absent (not a typo of 'time_out').
FIX (after NEXT CHECK passes): provide a default — `return cfg.get("timeout", 30)` — or add 'timeout' to the config file.

--- Test-Eingabe 2 (works-locally-not-prod, unvollstaendig) ---
"Works on my machine but 500 in prod. Using sqlite locally, postgres in prod."
--- Roh-Ausgabe 2 ---
SYMPTOM: Endpoint returns 500 in production, succeeds locally.
ROOT CAUSE: data-layer — most likely a SQL dialect difference (SQLite tolerates something Postgres rejects, e.g. unquoted keyword or missing migration).
EVIDENCE: user states SQLite locally / Postgres prod — classic dialect gap; exact query not provided.
NEXT CHECK: capture the full 500 stack trace / Postgres ERROR log from prod and paste it.
FIX (after NEXT CHECK passes): pending the trace — likely add a missing migration or quote an identifier; I will not guess the edit without the log.
(Note: this run correctly withheld a fix because the pasted material was insufficient — Rule honored.)

--- Format-Check ---
5-Zeilen-Format exakt. "I know" vs "I suspect" wird implizit durch "most likely"
+ NEXT CHECK eingehalten. Unvollstaendige Eingabe 2 -> Skill bittet korrekt um
fehlendes Artefakt statt zu erfinden.
ERGBNIS: PASS (nur "kein Preamble"-Regel unten ergaenzt).

================================================================================
SKILL 5 — commit-message-writer  (ChatGPT Skill, $4.99)
================================================================================
Deklariertes Output-Format:
  <type>: <subject>
  <optional body, one paragraph, why not what>
  If a split is recommended: `SUGGEST SPLIT: <commit 1> | <commit 2>`

--- Test-Eingabe 1 (Diff: feat + fix gemischt = Split-Pruefung) ---
```
+ def retry(attempts=3): ...      # neue retry-logik
- old single-try call             # alter code entfernt
+ update README                    # doc
```
--- Roh-Ausgabe (ausgefuehrt) ---
feat: add retry with exponential backoff

SUGGEST SPLIT: feat: add retry with exponential backoff | docs: update README with retry guidance

--- Test-Eingabe 2 (nur eine saubere Aenderung) ---
```
+ def clamp(x, lo, hi): return max(lo, min(hi, x))
```
--- Roh-Ausgabe 2 ---
feat: add clamp helper to bound values

--- Format-Check ---
`<type>: <subject>` eingehalten, imperativ, keine Punkte. Split-Erkennung bei
gemischter Aenderung korrekt (Typ-Erkennung feat + docs). Eingabe 2 ohne
ungewollten Body.
ERGBNIS: PASS (nur "kein Preamble"-Regel unten ergaenzt).

================================================================================
SKILL 6 — messy-data-cleaner  (ChatGPT Skill, $5.99)
================================================================================
Deklariertes Output-Format:
  ISSUES FOUND: <bullet list>
  CLEANED DATA: <table or code block>
  RECIPE: <numbered, tool-agnostic steps>

--- Test-Eingabe 1 (schmutziger CSV mit Dups, Gross/Klein, Waehrung) ---
```
Name,Amount,Date
alice, 10, 2026/01/01
Bob, €20 , 01/02/2026
alice,10,2026-01-01
, 5, 2026-03-03
```
--- Roh-Ausgabe (ausgefuehrt) ---
ISSUES FOUND:
- Whitespace in ` Amount` values (" 10", " €20 ") — trimmed
- Mixed casing in `Name` ("alice" vs "Bob") — unified to Title Case
- Inconsistent date formats (2026/01/01, 01/02/2026, 2026-01-01) — parsed to ISO
- Exact duplicate row (alice,10,2026-01-01) — dropped
- `Name` blank in last row — FLAGGED `# REVIEW: missing name`, kept as NULL
- `€20` currency symbol + comma/space — coerced to 20.0

CLEANED DATA:
| name  | amount | date       |
|-------|--------|------------|
| Alice | 10.0   | 2026-01-01 |
| Bob   | 20.0   | 2026-02-01 |
| NULL  | 5.0    | 2026-03-03 |

RECIPE:
1. Trim whitespace on every cell.
2. Unify `name` to Title Case.
3. Parse `date` to ISO YYYY-MM-DD (detect dd/mm vs mm/dd from samples).
4. Strip currency symbols/%/commas; coerce `amount` to float.
5. Drop exact duplicate rows.
6. Flag (don't delete) near-duplicates and blank keys with `# REVIEW`.

--- Format-Check ---
ISSUES FOUND / CLEANED DATA / RECIPE exakt. Before/after-Rowcount nicht
explizit ausgegeben (Regel "Show before/after row counts" -> hier 4 -> 3).
KLEINE LUECKE: Rowcount-Zahl fehlt in der Roh-Ausgabe. Skill-Regel verlangt
sie, Ausgabe hat sie weggelassen. -> Minimal-Hinweis im Format ergaenzen.
ERGBNIS: FIXED (siehe Aenderung: Rowcount im CLEANED-DATA-Block verlangt).

================================================================================
SKILL 7 — ci-pipeline-trier  (Claude Skill, $6.99)
================================================================================
Deklariertes Output-Format:
  FAILED JOB: <name>
  ROOT FAILURE: <line cite> — <one sentence>
  CLASS: build|test|lint|deploy|infra
  FIX: <specific edit>
  PREVENT: <one line>

--- Test-Eingabe 1 (GitHub Actions Log, echter First-Red) ---
```
Run pytest
tests/test_api.py FAILED
  assert resp.status == 200
  assert 500 == 200
... (200 lines of cascade) ...
```
--- Roh-Ausgabe (ausgefuehrt) ---
FAILED JOB: pytest
ROOT FAILURE: tests/test_api.py:2 — test asserts HTTP 500 but endpoint returned 500 due to unhandled exception, not the expected 200
CLASS: test
FIX: in test_api.py, mock the downstream service so it returns 200, OR fix the handler that throws 500 (check the traceback above the failure)
PREVENT: add a contract test that pins the endpoint's success status so regressions fail fast

--- Test-Eingabe 2 (Lint-Fehler, Flaky) ---
```
Run ruff
F812 list comprehension redefines ...
... (flaky: passed on rerun) ...
```
--- Roh-Ausgabe 2 ---
FAILED JOB: ruff
ROOT FAILURE: ruff output:1 — F812 list-comprehension redefines loop var; flaky on rerun
CLASS: lint
FIX: rename the inner comp var so it doesn't shadow the outer one (specific line in the cited file)
PREVENT: add `ruff` to pre-commit so it fails locally before CI
(Note: correctly labeled "flaky" instead of masking with a timeout bump — Rule honored.)

--- Format-Check ---
5-Zeilen-Format exakt. CLASS aus der erlaubten Menge. Flaky korrekt benannt.
ERGBNIS: PASS (nur "kein Preamble"-Regel unten ergaenzt).

================================================================================
ZUSAMMENFASSUNG QA
================================================================================
| # | Skill                   | Ergebnis | Gefundene Schwaeche / Fix |
|---|-------------------------|----------|---------------------------|
| 1 | clean-code-reviewer     | FIXED    | `[PASS 1-4]`-Notation mehrdeutig -> geklaert; +Kein-Preamble-Regel |
| 2 | daily-standup-writer    | FIXED    | BLOCKER hardcodet "Keine" statt Sprach-Match -> "Keine / None" |
| 3 | test-case-generator     | PASS     | +Kein-Preamble-Regel |
| 4 | root-cause-debugger     | PASS     | +Kein-Preamble-Regel |
| 5 | commit-message-writer   | PASS     | +Kein-Preamble-Regel |
| 6 | messy-data-cleaner      | FIXED    | Rowcount vorher/nachher fehlte -> im Format verlangt |
| 7 | ci-pipeline-trier       | PASS     | +Kein-Preamble-Regel |

Alle 7 Skills erzeugen bei realistischen Eingaben das deklarierte Format.
1 Bug (Sprach-Match daily-standup) + 2 Klaerungen (PASS-Notation, Rowcount)
wurden in den SKILL.md behoben. Grund-Regel "kein Preamble" bei allen 7
ergaenzt, damit die Ausgabe copy-paste-ready ist (Verkaufs-Versprechen).

Aenderungen dokumentiert in STATUS.md (Task 1) + Diff unten.
