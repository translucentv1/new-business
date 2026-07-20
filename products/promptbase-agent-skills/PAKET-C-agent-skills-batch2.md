# PAKET C — Agent Skills Batch 2 (5 weitere Skills)

Ergaenzung zu PAKET A (2 Skills). Fokus: Agent-Skills-Katalog ausbauen,
jeweils EINE andere hochwertige Kategorie, sofort verkaufbar, keine Dubletten,
kein Fuelltext. Jede SKILL.md ist vollstaendig (Frontmatter name+description +
Prozess + Output-Format + Regeln), Qualitaetsniveau wie "clean-code-reviewer".

Nischen-Trend-Korrektur (MEASURED, Kopf): Wochenaenderung Agent-Skills
-13% / -30% -> FALLEND, nicht "jung+steigend". Nische = UNGESAETTIGT
(wenige Listings), reale Verkaufsanteile (Claude Skill 3% Rang 6, ChatGPT
Skill 1% Rang 8), aber Trend aktuell RUECKLAEUFIG. Nie schoenreden.

====================================================================
SKILL 3 — "Test Case Generator" (Claude Skill) — Kategorie: Testing
====================================================================

- Modell: Claude (Claude Skill)
- Kategorie: Testing / QA
- Vorgeschlagener Preis: $6.99
- Vorgeschlagener Titel: "Test Case Generator — Edge Cases & Coverage (Claude Skill)"
- SKILL.md (verkaufter Inhalt):

---
name: test-case-generator
description: Use when the user pastes a function, endpoint, or feature spec and wants concrete test cases — happy path, edge cases, and failure modes — in a runnable format.
---

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

---

====================================================================
SKILL 4 — "Root-Cause Debugger" (Claude Skill) — Kategorie: Debugging
====================================================================

- Modell: Claude (Claude Skill)
- Kategorie: Debugging / Engineering
- Vorgeschlagener Preis: $7.99
- Vorgeschlagener Titel: "Root-Cause Debugger — Stop Guessing, Find The Bug (Claude Skill)"
- SKILL.md (verkaufter Inhalt):

---
name: root-cause-debugger
description: Use when the user pastes an error, stack trace, or "it works locally but not in prod" report and wants the actual cause, not a guess.
---

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

---

====================================================================
SKILL 5 — "Commit Message Writer" (ChatGPT Skill) — Kategorie: Git / Commit
====================================================================

- Modell: ChatGPT (ChatGPT Skill)
- Kategorie: Git / Productivity
- Vorgeschlagener Preis: $3.99
- Vorgeschlagener Titel: "Clean Commit Messages From Any Diff (ChatGPT Skill)"
- SKILL.md (verkaufter Inhalt):

---
name: commit-message-writer
description: Use when the user pastes a git diff or list of changed files and wants a conventional, review-ready commit message.
---

# Commit Message Writer

Turn a diff into a message a reviewer understands in 5 seconds.

## Input
Accept: a `git diff`, a list of file names, or "added X, fixed Y" bullets.

## Process
1. Detect the dominant change type -> prefix: feat / fix / refactor / docs / test / chore / perf.
2. Summarize the WHY in the subject (<= 50 chars, imperative: "add", not "added").
3. Add a body line only if the reason isn't obvious from the subject.
4. If the diff mixes unrelated changes, suggest splitting into 2+ commits.

## Output format
```
<type>: <subject>

<optional body, one paragraph, why not what>
```
If a split is recommended: `SUGGEST SPLIT: <commit 1> | <commit 2>`

## Rules
- Subject in imperative mood, no period at end.
- Never invent file names not in the input.
- Keep body under 72 chars/line. Match DE or EN to the user's diff comments.

---

====================================================================
SKILL 6 — "Messy Data Cleaner" (ChatGPT Skill) — Kategorie: Data-Cleaning
====================================================================

- Modell: ChatGPT (ChatGPT Skill)
- Kategorie: Data / Productivity
- Vorgeschlagener Preis: $5.99
- Vorgeschlagener Titel: "Messy CSV Cleaner — Dedupe, Fix, Normalize (ChatGPT Skill)"
- SKILL.md (verkaufter Inhalt):

---
name: messy-data-cleaner
description: Use when the user pastes a CSV snippet, table, or dataset sample and wants it cleaned — deduplicated, typed, normalized — with a repeatable recipe.
---

# Messy Data Cleaner

You make dirty data analysis-ready and explain every change.

## Process
1. PROFILE — State the columns, detected types, and obvious issues (blanks, dupes, mixed formats).
2. CLEAN (in order): trim whitespace -> unify casing -> parse dates to ISO (YYYY-MM-DD) -> coerce numbers (strip currency/%/commas) -> drop exact duplicates -> flag, don't silently delete, near-duplicates.
3. NORMALIZE — consistent headers (snake_case), one value per cell, empty string -> NULL.
4. RECIPE — Output the exact steps as a reusable list (works as pandas / Excel / SQL).

## Output format
`ISSUES FOUND: <bullet list>`
`CLEANED DATA: <table or code block>`
`RECIPE: <numbered, tool-agnostic steps>`

## Rules
- Never overwrite a value you're unsure about — flag it (`# REVIEW: <reason>`).
- Show before/after row counts so the user sees what changed.
- If a column's meaning is ambiguous, ask or label the assumption explicitly.

---

====================================================================
SKILL 7 — "CI Pipeline Trier" (Claude Skill) — Kategorie: DevOps / CI
====================================================================

- Modell: Claude (Claude Skill)
- Kategorie: DevOps / CI
- Vorgeschlagener Preis: $6.99
- Vorgeschlagener Titel: "CI Failure Trier — Why Your Build Broke (Claude Skill)"
- SKILL.md (verkaufter Inhalt):

---
name: ci-pipeline-trier
description: Use when the user pastes a failed CI log (GitHub Actions, GitLab CI, etc.) and wants the root failure isolated from the noise, plus the fix.
---

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

---

====================================================================
PREVIEW-BILD-KONZEPTE (Cover je Listing — nur Konzept, HARD-STOP: kein Bild)
====================================================================

- Skill 3 (Testing): Mockup eines Test-Dashboards mit gruenen/roten TC-Kacheln
  (P0/P1/P2), Badge "Claude Skill". Stil: sauberes Dev-Dashboard.
- Skill 4 (Debugging): Split-Screen "Symptom vs Root Cause" mit
  Stack-Trace-Zitat und Lupe auf eine Zeile. Badge "Claude Skill".
- Skill 5 (Git/Commit): Terminal-Fenster mit farbigem `feat:`-Commit
  ueber einem Diff. Badge "ChatGPT Skill".
- Skill 6 (Data): Vorher/Nachher-Tabelle (schmutzig -> sauber), Pfeil dazwischen,
  "dedupe / normalize" Labels. Badge "ChatGPT Skill".
- Skill 7 (DevOps/CI): CI-Log mit rot markierter "FIRST RED"-Zeile + gruenem
  "FIX"-Vorschlag daneben. Badge "Claude Skill".

====================================================================
STATUS
====================================================================
- 5 SKILL.md + Titel + Beschreibung + Preview-Konzept: FERTIG (lokal).
- Veröffentlichung: NICHT erfolgt (HARD-STOP). Nutzer muss Account +
  Stripe/Zoneless anlegen.
- Katalog jetzt: 7 Agent Skills gesamt (2 aus PAKET A + 5 aus PAKET C),
  verteilt auf Review, Writing, Testing, Debugging, Git, Data, DevOps.
