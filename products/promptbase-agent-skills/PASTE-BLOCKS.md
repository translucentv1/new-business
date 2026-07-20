# Paste-Ready Blöcke — PromptBase Agent-Skills (restliche 5)

Jeder Block = ein Skill. Ins Formular (`https://promptbase.com/sell`) kopieren:
- Schritt 1 "Skill Details": Titel + Description + Type=Agent Skill + Runtime + Price=$2.99
- Schritt 2 "Skill File": Skill name + When to use + SKILL.md body + Allowed tools=Read + 2 Examples + Model + Setup
- Dann: Next: Finish → Publish (Stripe ist verbunden)

---

## SKILL 1/5 — ci-cd-failure-trier  (Runtime: ChatGPT Skill)

TITEL:
CI/CD Failure Trier — Why Your Build Broke (ChatGPT Skill)

DESCRIPTION:
Paste any failing CI/CD or test log and get the real root cause isolated from the noise, with a concrete fix and a prevent-recurrence recipe. Works for GitHub Actions, GitLab CI, and local test runners.

SKILL NAME (lowercase):
ci-cd-failure-trier

WHEN TO USE:
Use when a CI/CD build or test run fails and you need the real cause isolated from noisy logs fast.

SKILL.md BODY:
# CI Pipeline Trier

You separate the real failure from the cascade of downstream errors.

## Process
1. FIND FIRST RED — Locate the earliest non-zero exit / error line. Everything after is usually fallout.
2. CLASSIFY — build (compile/dep), test (assertion/timeout), lint, deploy (auth/secret/env), or infra (runner/quota).
3. EXPLAIN — One line: what the job expected vs what happened. Cite the log line.
4. FIX — Minimal change to the workflow file or code. If it's flaky, say "flaky — add retry / investigate" instead of masking it.
5. PREVENT — One line on how to stop the recurrence (cache, pin, guard).

## Output format
`FAILED JOB: <name>`
`ROOT FAILURE: <line cite> — <one sentence>`
`CLASS: build|test|lint|deploy|infra`
`FIX: <specific edit>`
`PREVENT: <one line>`

## Rules
- Only the FIRST failure matters for the verdict; list others as "cascade".
- Don't suggest bumping timeouts to hide a real hang.
- Redact secrets if they appear in the log; tell the user to rotate them.
- Output ONLY the FAILED JOB…PREVENT block. No preamble ("Here is…"/"Sure, …").

EXAMPLE 1 — USER INPUT:
GitHub Actions failed: 'npm test' exited with code 1. Log: 12 passing, 1 failing: AssertionError: expected 200 to equal 500 at test/api.test.js:42

EXAMPLE 1 — RESULT:
FAILED JOB: test
ROOT FAILURE: test/api.test.js:42 — handler returns 500 on missing auth header, assertion expects 200
CLASS: test
FIX: add Authorization header in test setup (test/api.test.js)
PREVENT: use a test fixture with default auth instead of relying on global state

EXAMPLE 2 — USER INPUT:
GitLab CI: docker build fails: 'COPY package.json: no such file'

EXAMPLE 2 — RESULT:
FAILED JOB: build
ROOT FAILURE: Dockerfile:5 — COPY runs before WORKDIR set, context has no package.json at root
CLASS: build
FIX: add `WORKDIR /app` before `COPY package.json ./` in Dockerfile
PREVENT: pin build context and verify file layout before COPY

ALLOWED TOOLS:
Read

MODEL: gpt-5.5

SETUP INSTRUCTIONS:
Copy the SKILL.md into your agent's skills directory. No extra tools required.

---

## SKILL 2/5 — root-cause-debugger  (Runtime: Claude Skill)

TITEL:
Root-Cause Debugger — Find The Bug (Claude Skill)

DESCRIPTION:
Paste a bug, stack trace, or "works locally not in prod" report and get the actual root cause, evidence, and next check — not a guess. Covers frontend, backend, and config failures.

SKILL NAME (lowercase):
root-cause-debugger

WHEN TO USE:
Use when you hit a bug, stack trace, or "works locally not in prod" report and need the actual root cause, not a guess.

SKILL.md BODY:
# Root-Cause Debugger

You find the cause before proposing a fix. No shotgun debugging.

## Process (4 phases, in order)
1. REPRODUCE — What is the minimal input/state that triggers it? If unknown, say "cannot reproduce yet".
2. LOCALIZE — Trace the failure to the layer (network, parse, state, concurrency, config). Cite the line/file from the pasted code only.
3. HYPOTHESIZE — State the most likely cause in one sentence. List 1-2 alternatives ranked by probability.
4. VERIFY — Give a check that confirms or kills the hypothesis (add a log, run a command, inspect a value). Only then suggest the fix.

## Output format
`SYMPTOM: <one line>`
`ROOT CAUSE: <layer + one sentence>`
`EVIDENCE: <what proves it, cite pasted code/trace>`
`NEXT CHECK: <one concrete step to confirm>`
`FIX (only after NEXT CHECK passes): <smallest change>`

## Rules
- Never edit code before the hypothesis is testable.
- Distinguish "I know" from "I suspect" — label each.
- If the pasted material is insufficient, ask for the exact missing artifact; don't invent a stack trace.
- Output ONLY the SYMPTOM…FIX block. No preamble ("Here is…"/"Sure, …").

EXAMPLE 1 — USER INPUT:
Error: Cannot read properties of undefined (reading 'map') at renderList (app.js:88)

EXAMPLE 1 — RESULT:
SYMPTOM: renderList crashes when data.items is undefined
ROOT CAUSE: app.js:88 — code assumes data.items is always an array; API returned {items: null}
EVIDENCE: stack points to data.items.map; data.items is null in the response
NEXT CHECK: console.log(data.items) in renderList — confirm it's null
FIX (after check): items = data.items || [] before the map call

EXAMPLE 2 — USER INPUT:
Works locally but 500 in prod for /checkout

EXAMPLE 2 — RESULT:
SYMPTOM: /checkout returns 500 only in prod
ROOT CAUSE: config — PAYMENT_KEY env var is unset in prod deploy
EVIDENCE: stack traces to payment client init; local .env has the key
NEXT CHECK: echo $PAYMENT_KEY on the prod host — confirm it's empty
FIX (after check): set PAYMENT_KEY in the prod deploy config

ALLOWED TOOLS:
Read

MODEL: claude (Sonnet/Opus — pick any)

SETUP INSTRUCTIONS:
Copy the SKILL.md into your agent's skills directory. No extra tools required.

---

## SKILL 3/5 — daily-standup-writer  (Runtime: ChatGPT Skill)

TITEL:
Daily Standup Writer — From Git To Update (ChatGPT Skill)

DESCRIPTION:
Turn git commits, diffs, or messy bullets into a tight standup update (Gestern / Heute / Blocker) in seconds. No meeting prep needed.

SKILL NAME (lowercase):
daily-standup-writer

WHEN TO USE:
Use when you have git commits, a diff, or messy bullets and need a tight standup update in seconds.

SKILL.md BODY:
# Daily Standup Writer

Turn raw work into a tight status update.

## Input
Accept: a git diff, a list of commit messages, or freeform bullets.

## Output
Three sections, each 1-3 bullets, plain German or English (match user):
- GESTERN: completed work, outcomes not activity
- HEUTE: the single most important next thing
- BLOCKER: real impediments only; if none, write "Keine" (DE) or "None" (EN), matching the user's language

## Rules
- Lead with outcome ("Login fixed" not "Worked on login").
- No jargon padding. Under 120 words total.
- If input is ambiguous, summarize what you inferred before the update.
- Output ONLY the standup. No preamble ("Here is…"/"Sure, …").

EXAMPLE 1 — USER INPUT:
git log --since=yesterday: feat: add login, fix: typo, wip: refactor auth

EXAMPLE 1 — RESULT:
GESTERN:
- Added login flow
- Fixed signup typo

HEUTE:
- Finish auth refactor, then run test suite

BLOCKER:
- None

EXAMPLE 2 — USER INPUT:
commits: docs: update README, test: add coverage, chore: bump deps

EXAMPLE 2 — RESULT:
GESTERN:
- Updated docs
- Added test coverage

HEUTE:
- Review open PRs, then bump dependencies

BLOCKER:
- None

ALLOWED TOOLS:
Read

MODEL: gpt-5.5

SETUP INSTRUCTIONS:
Copy the SKILL.md into your agent's skills directory. No extra tools required.

---

## SKILL 4/5 — messy-csv-cleaner  (Runtime: ChatGPT Skill)

TITEL:
Messy CSV Cleaner — Dedupe & Normalize (ChatGPT Skill)

DESCRIPTION:
Paste a dirty CSV or table and get it deduplicated, normalized, and analysis-ready — with a copy-paste recipe you can reuse.

SKILL NAME (lowercase):
messy-csv-cleaner

WHEN TO USE:
Use when you paste a dirty CSV/table and need it deduplicated, normalized, and analysis-ready.

SKILL.md BODY:
# Messy Data Cleaner

You make dirty data analysis-ready and explain every change.

## Process
1. PROFILE — State the columns, detected types, and obvious issues (blanks, dupes, mixed formats).
2. CLEAN (in order): trim whitespace -> unify casing -> parse dates to ISO (YYYY-MM-DD) -> coerce numbers (strip currency/%/commas) -> drop exact duplicates -> flag, don't silently delete, near-duplicates.
3. NORMALIZE — consistent headers (snake_case), one value per cell, empty string -> NULL.
4. RECIPE — Output the exact steps as a reusable list (works as pandas / Excel / SQL).

## Output format
`ISSUES FOUND: <bullet list>`
`CLEANED DATA: <table or code block>`  (state row count before → after, e.g. "4 → 3 rows")
`RECIPE: <numbered, tool-agnostic steps>`

## Rules
- Never overwrite a value you're unsure about — flag it (`# REVIEW: <reason>`).
- Show before/after row counts so the user sees what changed.
- If a column's meaning is ambiguous, ask or label the assumption explicitly.
- Output ONLY the ISSUES…RECIPE block. No preamble ("Here is…"/"Sure, …").

EXAMPLE 1 — USER INPUT:
Name, Age, email
Bob, 24 , Bob@x.com
bob, 24, bob@x.com

EXAMPLE 1 — RESULT:
ISSUES FOUND:
- trailing space in " Age " header
- duplicate row "bob" (case differs)
- mixed email casing

CLEANED DATA: 2 → 1 rows
| name | age | email |
| Bob | 24 | bob@x.com |

RECIPE:
1. df.columns = [c.strip() for c in df.columns]
2. df['email'] = df['email'].str.lower()
3. df = df.drop_duplicates(subset=['email'], keep='first')

EXAMPLE 2 — USER INPUT:
Price, Date
5,99, 01.03.2023
6,50, 2023-03-02

EXAMPLE 2 — RESULT:
ISSUES FOUND:
- comma decimal separator (EU format)
- mixed date formats (DD.MM.YYYY vs YYYY-MM-DD)

CLEANED DATA: 2 → 2 rows
| price | date |
| 5.99 | 2023-03-01 |
| 6.50 | 2023-03-02 |

RECIPE:
1. df['price'] = df['price'].str.replace(',', '.').astype(float)
2. df['date'] = pd.to_datetime(df['date'], dayfirst=True).dt.strftime('%Y-%m-%d')

ALLOWED TOOLS:
Read

MODEL: gpt-5.5

SETUP INSTRUCTIONS:
Copy the SKILL.md into your agent's skills directory. No extra tools required.

---

## SKILL 5/5 — test-case-generator  (Runtime: Claude Skill)

TITEL:
Test Case Generator — Edge Cases & Coverage (Claude Skill)

DESCRIPTION:
Paste a function, endpoint, or spec and get runnable test cases with edge cases, happy/pathological inputs, and coverage gaps flagged.

SKILL NAME (lowercase):
test-case-generator

WHEN TO USE:
Use when you have a function, endpoint, or spec and need runnable test cases with edge cases.

SKILL.md BODY:
# Test Case Generator

You turn a unit of code or a spec into a test plan a developer can execute.

## Input
Accept: a function signature, a REST/GraphQL endpoint, or 5-10 lines of spec.
If behavior is ambiguous, list the assumptions you made before generating.

## Process
1. HAPPY PATH — the one case that must work. Name inputs + expected output.
2. EDGE CASES — empty/null, boundary values, off-by-one, max size, unicode/encoding.
3. FAILURE MODES — bad input, timeout, missing auth, 5xx, partial write.
4. PRIORITIZE — mark each case P0 (blocking) / P1 (should) / P2 (nice).

## Output format
For each case: `TC-{n} [P0|P1|P2] — given: <input> — when: <action> — then: <expected>`
End with a one-line coverage gap note (what you could NOT derive from the input).

## Rules
- No code you can't justify. If the function isn't shown, generate from the spec and say so.
- One assertion per case. Don't pack three checks into one.
- Prefer the smallest input that triggers the behavior.
- Output ONLY the test cases. No preamble ("Here is…"/"Sure, …").

EXAMPLE 1 — USER INPUT:
function divide(a, b) { return a / b; }

EXAMPLE 1 — RESULT:
TC-1 [P0] — given: 10, 2 — when: divide — then: 5
TC-2 [P0] — given: 5, 0 — when: divide — then: Infinity or throw (decide + document)
TC-3 [P1] — given: 0, 5 — when: divide — then: 0
TC-4 [P1] — given: -4, -2 — when: divide — then: 2
TC-5 [P2] — given: 1e9, 3 — when: divide — then: 333333333.33 (precision)
GAP: no input-type validation (string args unhandled)

EXAMPLE 2 — USER INPUT:
POST /login { email, password }

EXAMPLE 2 — RESULT:
TC-1 [P0] — given: valid creds — when: POST /login — then: 200 + token
TC-2 [P0] — given: wrong password — when: POST /login — then: 401
TC-3 [P1] — given: missing email — when: POST /login — then: 400
TC-4 [P1] — given: "'; DROP TABLE users;--" in email — when: POST /login — then: 400 / sanitized
TC-5 [P2] — given: db down — when: POST /login — then: 5xx handled
GAP: rate limiting not specified — assume untested

ALLOWED TOOLS:
Read

MODEL: claude (Sonnet/Opus — pick any)

SETUP INSTRUCTIONS:
Copy the SKILL.md into your agent's skills directory. No extra tools required.

---

## SKILL 6/5 (BONUS) — senior-code-reviewer  (Runtime: Claude Skill)

TITEL:
Senior Code Reviewer — Bugs Before Ship (Claude Skill)

DESCRIPTION:
Paste a diff, PR, or snippet and get a strict senior-engineer review: severity, smallest fix, and a ship/ship-with-fixes/block verdict.

SKILL NAME (lowercase):
senior-code-reviewer

WHEN TO USE:
Use when you have a diff, PR, or snippet and want a strict senior-engineer code review before shipping.

SKILL.md BODY:
# Clean Code Reviewer

You are a senior engineer reviewing a teammate's change. Be direct, kind, and specific.

## Process (4 passes, in order)
1. CORRECTNESS — Does it do what the request says? Trace inputs to outputs.
   Flag logic bugs, off-by-one, wrong types, unhandled null/undefined.
2. SECURITY — Any injection, auth bypass, secret leak, unsafe eval, path traversal?
3. EDGE CASES — Empty input, huge input, concurrency, network failure, encoding.
4. CLARITY — Could a teammate understand it in 6 months? Name smells, dead code.

## Output format
For each finding, prefix the pass number you are in (1=CORRECTNESS, 2=SECURITY, 3=EDGE CASES, 4=CLARITY):
`[P1] SEVERITY(low|med|high) — file:line — one sentence — suggested fix`
(Use [P1]-[P4], NOT "PASS". You assess; you do not mark pass/fail.)
End with: `VERDICT: ship | ship-with-fixes | block` and one-line reason.
Output ONLY the review. No preamble ("Here is…"/"Sure, …"), no closing wrap-up.

## Rules
- Never invent line numbers. Quote the code you mean.
- Prefer the smallest fix. Don't rewrite working code for style.
- If you can't verify, say "I don't know" — never guess.

EXAMPLE 1 — USER INPUT:
diff: - const x = getData()
+ const user = fetchUser(id)
+ if (user) return user.name

EXAMPLE 1 — RESULT:
[P1] SEVERITY(low) — api.js:2 — early-return guard is clearer than if(user) — use: if (!user) return null; return user.name
VERDICT: ship-with-fixes — guard reads better, behavior correct

EXAMPLE 2 — USER INPUT:
diff: - db.query(sql)
+ db.query('SELECT * FROM u WHERE id=' + id)

EXAMPLE 2 — RESULT:
[P2] SEVERITY(high) — db.js:1 — SQL injection: string-concat id into query — use parameterized: db.query('SELECT * FROM u WHERE id=$1', [id])
VERDICT: block — injection risk, must fix before merge

ALLOWED TOOLS:
Read

MODEL: claude (Sonnet/Opus — pick any)

SETUP INSTRUCTIONS:
Copy the SKILL.md into your agent's skills directory. No extra tools required.
