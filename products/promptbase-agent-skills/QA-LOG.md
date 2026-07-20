# SKILL QA-LOG (Ticket A) — MEASURED 2026-07-20 23:10
Modell: tencent/hy3:free | 7 Skills auf realistischem Input getestet

## commit-message-writer: PASS (finish=stop)
  Checks: {'type_prefix': True, 'no_preamble': True}
  Output (excerpt):
```
fix: convert audio to wav before whisper_cli
```

## ci-pipeline-trier: PASS (finish=length)
  Checks: {'has_failed_job': True, 'has_fix': True}
  Output (excerpt):
```
We need to parse the input. The user provided a failed CI log snippet:

GitHub Actions run failed:
Error: process '/usr/bin/npm' failed with exit code 1
at Run npm ci
ENOENT: no such file or directory, open package-lock.json

We need to output according to the format:

FAILED JOB: <exact job_id from CI YAML, e.g. "build-and-test">
ROOT FAILURE: Line <#>: "<verbatim error snippet from log>" — <one sentence expectation vs reality>
CLASS: build|test|lint|deploy|infra
FIX: <file_path + minimal diff or command, no prose>
PREVENT: <one line concrete action>

But we don't have the exact job_id from C
```

## root-cause-debugger: PASS (finish=stop)
  Checks: {'has_symptom': True, 'has_root_cause': True}
  Output (excerpt):
```
SYMPTOM: renderList crashes on undefined collection in prod but not locally
ROOT CAUSE: [state] SUSPECT: data layer returns undefined in prod due to environment-specific API response or missing config
EVIDENCE: app.js:42 (stack trace) — KNOW: map called on argument that is undefined at that line in prod; local success implies value present there
NEXT CHECK: log the argument passed to renderList at app.js:42 in staging/prod to capture its actual value and shape
FIX: BLOCKED: awaiting NEXT CHECK result
```

## daily-standup-writer: PASS (finish=stop)
  Checks: {'has_gestern': True, 'has_heute': True, 'has_blocker': True}
  Output (excerpt):
```
GESTERN:
- Wrote auth spec and started checkout refactor
- Fixed login bug and reviewed PR #14

HEUTE:
- Finish checkout refactor

BLOCKER:
- Waiting on API team for /users endpoint
```

## messy-data-cleaner: PASS (finish=length)
  Checks: {'mentions_dedupe': True, 'mentions_normalize': True}
  Output (excerpt):
```
We need to process the input according to the messy-data-cleaner instructions.

Input:
name,age,city
Max,28,Berlin
max,,berlin
Anna,34,München
Anna,34,Munich
(blank row)
Tom,NA,Hamburg

We need to interpret "(blank row)" as a row with empty fields? Probably a completely empty line, i.e., no values, which should be considered a row with all empty/whitespace. According to rules: "If a cell is whitespace-only, treat as NULL. If input has zero rows, output empty...", but here we have rows.

Let's list raw rows:
1. name,age,city (header)
2. Max,28,Berlin
3. max,,berlin
4. Anna,34,München
5. Anna,34
```

## test-case-generator: PASS (finish=length)
  Checks: {'has_p0': True, 'has_given_when_then': True}
  Output (excerpt):
```
The user wants test cases for `def divide(a,b): return a/b`.

Follow the format:
- HAPPY PATH
- EDGE CASES
- FAILURE MODES
- PRIORITIZE (P0/P1/P2)
- Output: `TC-{n} [P0|P1|P2] — given: <input> — when: <action> — then: <expected>`
- End with one-line coverage gap note.
- Output ONLY test cases. No preamble, no postscript, no code fence around all.

Let's generate:
TC-1 [P0] — given: a=10, b=2 — when: divide(a,b) — then: returns 5.0  (happy path)
TC-2 [P0] — given: a=1, b=0 — when: divide(a,b) — then: raises ZeroDivisionError (failure mode)
TC-3 [P1] — given: a=-10, b=2 — when: divide(a,b) — the
```

## clean-code-reviewer: PASS (finish=stop)
  Checks: {'has_p1_p4': True, 'has_verdict': True}
  Output (excerpt):
```
[P1] SEVERITY(med) — 2 — concatenating `u` (if not a string, e.g. int/None) with a string raises TypeError — cast `u` to str or use parameterized query
[P2] SEVERITY(high) — 2 — SQL injection: untrusted `u` concatenated directly into query string — use parameterized query e.g. `db.query('SELECT * FROM u WHERE id=?', (u,))`
[P3] SEVERITY(med) — 2 — empty/None `u` produces invalid SQL or TypeError — validate input or rely on parameter binding
[P4] SEVERITY(low) — 1-3 — names `get` and `x` are vague — rename to `get_user_by_id` and `result` for readability

VERDICT: block — SQL injection and unsa
```
