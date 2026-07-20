# SKILL QA-LOG (Ticket A) — MEASURED 2026-07-20 20:37
Modell: tencent/hy3:free | 7 Skills auf realistischem Input getestet

## commit-message-writer: PASS (finish=stop)
  Checks: {'type_prefix': True, 'no_preamble': True}
  Output (excerpt):
```
fix: convert audio to wav before whisper_cli call

Ensures whisper_cli receives wav format regardless of input codec.
```

## ci-pipeline-trier: PASS (finish=stop)
  Checks: {'has_failed_job': True, 'has_fix': True}
  Output (excerpt):
```
FAILED JOB: npm ci
ROOT FAILURE: ENOENT: no such file or directory, open package-lock.json — `npm ci` requires a committed `package-lock.json` for reproducible clean installs but the file is absent from the checkout.
CLASS: build
FIX: Commit `package-lock.json` to the repository (preferred), or change the workflow command from `npm ci` to `npm install` if a lockfile is intentionally not used.
PREVENT: Keep `package-lock.json` version-controlled and rely on `npm ci` in CI to fail fast on lockfile drift.
```

## root-cause-debugger: PASS (finish=stop)
  Checks: {'has_symptom': True, 'has_root_cause': True}
  Output (excerpt):
```
SYMPTOM: renderList throws TypeError reading 'map' of undefined at app.js:42 in prod only, not locally.
ROOT CAUSE (SUSPECT): Data/state layer — renderList receives an undefined array from an environment-dependent source (API response, env var, or async fetch) that is populated locally but missing/undefined in prod after deploy.
EVIDENCE: Stack trace shows `.map` called on undefined at app.js:42; the local-success/prod-failure pattern indicates an environment-specific data or config gap rather than a logic bug that would fail everywhere.
NEXT CHECK: In prod, log the exact argument passed to re
```

## daily-standup-writer: PASS (finish=stop)
  Checks: {'has_gestern': True, 'has_heute': True, 'has_blocker': True}
  Output (excerpt):
```
GESTERN:
- Auth spec completed, defining authentication requirements

HEUTE:
- Progress the checkout refactor

BLOCKER:
- Waiting on API team for /users endpoint
```

## messy-data-cleaner: PASS (finish=length)
  Checks: {'mentions_dedupe': True, 'mentions_normalize': True}
  Output (excerpt):
```
We need to follow the instructions exactly. The user provided a CSV snippet:
name,age,city
Max,28,Berlin
max,,berlin
Anna,34,München
Anna,34,Munich
(blank row)
Tom,NA,Hamburg

We must output ONLY the ISSUES FOUND / CLEANED DATA / RECIPE block. No preamble.

First, profile: columns: name (string), age (mixed: numbers, blank, "NA"), city (string, with variations like Berlin/berlin, München/Munich). Issues: 
- Row2: "max" lowercase, age blank, city "berlin" lowercase.
- Row3: Anna, 34, München (umlaut)
- Row4: Anna, 34, Munich (English spelling) -> near-duplicate of row3? Different city spelling,
```

## test-case-generator: PASS (finish=length)
  Checks: {'has_p0': True, 'has_given_when_then': True}
  Output (excerpt):
```
The user wants me to generate test cases for the function:
```python
def divide(a,b): return a/b
```

Per instructions:
- Input: function signature `def divide(a,b): return a/b`
- Process:
  1. HAPPY PATH
  2. EDGE CASES
  3. FAILURE MODES
  4. PRIORITIZE (P0/P1/P2)
- Output format: `TC-{n} [P0|P1|P2] — given: <input> — when: <action> — then: <expected>`
- End with a one-line coverage gap note.
- Rules: No preamble. Only test cases. One assertion per case.

Let's derive test cases:

Happy path:
TC-1 [P0] — given: a=10, b=2 — when: divide(10,2) — then: returns 5.0

Edge cases:
TC-2 [P1] — given
```

## clean-code-reviewer: PASS (finish=length)
  Checks: {'has_p1_p4': True, 'has_verdict': True}
  Output (excerpt):
```
We need to review the provided code snippet:

def get(u):
  x = db.query('SELECT * FROM u WHERE id='+u)
  return x

We need to do 4 passes: correctness, security, edge cases, clarity.

We must output findings with prefix [P1] etc., severity, file:line (but we don't have file/line; we can say "snippet:1" or just quote code. The instruction: "Never invent line numbers. Quote the code you mean." So we can use something like `[P1] SEVERITY — <quoted code> — ...` or we can say "line 1" if we assume the def is line 1? But we shouldn't invent line numbers. Better to quote the code snippet. The instru
```
