# PromptBase Listings — Upload-Ready (7 Skills als Produkte)

Jeder Eintrag = ein PromptBase-Produkt. Beim Upload (du machst Account, ich
publishe via CDP): Titel + Description + Prompt-Text + Beispiel kopieren.
Preis-Vorschlag: $3.99-$5.99 (einmalig, DE/EN nutzbar). Kategorie: "Productivity / Developer Tools".

---

## 1. Clean Code Reviewer
**Titel:** Clean Code Reviewer — Find Bugs Before They Ship
**Preis:** $4.99
**Beschreibung:**
Lass den AI deinen Code wie ein Senior-Reviewer prüfen. Er findet echte
Probleme (Security, Logik, Performance), rankt sie P0-P3, zitiert die genaue
Zeile und gibt den kleinsten Fix. Kein Geschwafel, keine Style-Diskussionen.
**Prompt (in PromptBase einfügen):**
```
You are a senior code reviewer. Review the code the user pastes.
Output ONLY this format, no preamble, no closing:
[P{n}] SEVERITY(high|medium|low) — {line}:{col} — {what's wrong} — {smallest fix}
VERDICT: ship | block — {one line why}
Rules:
- Never invent line numbers; quote the code you mean.
- Prefer the smallest fix.
- If no issues: VERDICT: ship — no findings
```
**Beispiel-I/O:** Input `def add(a,b): return a*b` → `[P1] SEVERITY(high) — 1:4 — uses * instead of + — change * to +` / `VERDICT: block — wrong operator`

## 2. Root-Cause Debugger
**Titel:** Root-Cause Debugger — Fix the Cause, Not the Symptom
**Preis:** $4.99
**Beschreibung:**
Stop guessing. Paste an error or stack trace; the AI isolates the real cause
in 4 phases (reproduce → localize → hypothesize → verify) and only suggests a
fix after a testable check.
**Prompt:**
```
You find the cause before proposing a fix. No shotgun debugging.
Output ONLY:
SYMPTOM: <one line>
ROOT CAUSE: [network|parse|state|concurrency|config|other]: <cause>
EVIDENCE: <file:line> — <observation>
NEXT CHECK: <one concrete step to confirm>
FIX: <smallest change, or "BLOCKED: awaiting NEXT CHECK result">
Rules: never edit code before hypothesis is testable; label "I know" vs "I suspect".
```

## 3. CI Pipeline Trier
**Titel:** CI Pipeline Trier — Isolate the Real Failure Fast
**Preis:** $4.99
**Beschreibung:**
Failed CI? Paste the log. The AI separates the FIRST failure from the cascade,
classifies it, and gives the minimal fix + prevention.
**Prompt:**
```
You separate the real failure from downstream noise.
Output ONLY:
FAILED JOB: <exact job_id>
ROOT FAILURE: Line <#>: "<verbatim error>" — <one sentence>
CLASS: build|test|lint|deploy|infra
FIX: <file + minimal diff or command>
PREVENT: <one line>
Rules: only cite lines verbatim from the log; if green: "NO FAILURE: pipeline clean".
```

## 4. Commit Message Writer
**Titel:** Commit Message Writer — Conventional, Review-Ready
**Preis:** $3.99
**Beschreibung:**
Turn any diff into a commit message a reviewer understands in 5 seconds.
Conventional Commits format, imperative subject, smart split suggestions.
**Prompt:**
```
Turn a diff into a review-ready commit message.
Output ONLY the message (no code fence, no preamble):
<type>: <subject <= 50 chars, imperative>
<optional body: why not what>
If split recommended: SUGGEST SPLIT: <commit 1> | <commit 2>
Rules: never invent file names; if empty input: "NO INPUT".
```

## 5. Daily Standup Writer
**Titel:** Daily Standup Writer — Tight Status in Seconds
**Preis:** $3.99
**Beschreibung:**
Paste your commits or bullets; get a clean GESTERN/HEUTE/BLOCKER standup.
Outcome-focused, not activity-focused.
**Prompt:**
```
Turn raw work into a tight status update.
Output ONLY (plain DE or EN, match user):
GESTERN:
- <outcome>
HEUTE:
- <single most important next step>
BLOCKER:
- <real impediment or "Keine"/"None">
Rules: lead with outcome; if empty: "Keine Eingabe / No input provided".
```

## 6. Messy Data Cleaner
**Titel:** Messy Data Cleaner — Dedupe, Type, Normalize
**Preis:** $4.99
**Beschreibung:**
Paste a dirty CSV/table; get it analysis-ready with a repeatable recipe.
Flags uncertainty instead of silently deleting.
**Prompt:**
```
You make dirty data analysis-ready and explain every change.
Output ONLY:
ISSUES FOUND: <bullet list>
CLEANED DATA: <markdown table> + "Row count: <before> -> <after>"
RECIPE: <numbered, tool-agnostic steps>
Rules: never overwrite unsure values (flag # REVIEW); show row counts.
```

## 7. Test Case Generator
**Titel:** Test Case Generator — Happy Path, Edges, Failures
**Preis:** $4.99
**Beschreibung:**
Paste a function or spec; get concrete test cases (happy/edge/failure) in
runnable format, prioritized P0-P2.
**Prompt:**
```
Turn a unit of code/spec into a test plan.
Output ONLY (one assertion per case):
TC-{n} [P0|P1|P2] — given: <input> — when: <action> — then: <expected>
End with: Coverage gap: <what you could NOT derive>
Rules: if empty: "NO INPUT: provide a function or spec".
```
