# LLM-Review der 7 Agent-Skills (Ticket G — Rechenpower-Selbstverbesserung)


## ci-pipeline-trier.md

The user wants me to act as a Senior Prompt Engineer and review the provided SKILL.md for weaknesses based on 5 specific criteria:
1. Mehrdeutige Formulierungen im Output-Format (Ambiguous formulations in output format)
2. Fehlende Edge-Case-Regeln (Missing edge-case rules)
3. Halluzinations-Risiko (Hallucination risk)
4. Fehlende "Output nur, kein Preamble"-Regel (Missing "output only, no preamble" rule) - wait, the file actually HAS this rule at the bottom: "Output ONLY the FAILED JOB…PREVENT block. No preamble ("Here is…"/"Sure, …")." But maybe it's not strict enough or placed weirdly? Or maybe I should check if it's fully covered. Actually the prompt says "Pruefe diese SKILL.md auf Schwachstellen" including "Fehlende 'Output nur, kein Preamble'-Regel". The file has it, but maybe it's weak or could be strengthened/placed better? Or maybe the user thinks it's missing but it's there? I should point out that while it exists, it could be more strictly enforced or combined with "no markdown code block wrapping if not needed" or similar. Wait, the instruction says "Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund." So I need to provide concrete applicable improvements. If something is already there but weak, I improve it. If something is missing, I add it (old text snippet might be the surrounding context or I state what to add). Actually, the instruction says "den exakten alten Text-Ausschnitt" - if it's missing, I can quote the section where it should be inserted.

Let's analyze the SKILL.md:

Current content:
```
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
- Output ONLY the FAILED JOB…PREVENT block. No preamble ("Here is…"/"Sure, …").
```

Weaknesses to address:

1. Mehrdeutige Formulierungen im Output-Format:
- `<name>` is ambiguous: is it the job name from the YAML or the workflow name? Should specify "exact job_id from CI config".
- `<line cite>` is ambiguous: should it be the line number, the exact error string, or both?
- `<specific edit>` is ambiguous: should it be a code diff, a file path, or a command?
- The backticks in the output format might imply markdown code block, but the rule says output ONLY the block. Could be misinterpreted as wrapping in ```.
- "ROOT FAILURE: <line cite> — <one sentence>" combines explain and cite but process step 3 says EXPLAIN is separate. Actually output format doesn't have EXPLAIN field, it merges it into ROOT FAILURE. That's fine but `<line cite>` is vague.

2. Fehlende Edge-Case-Regeln:
- What if there are multiple independent jobs failing simultaneously (parallel jobs)? "First red" might be ambiguous if jobs run in parallel and logs are interleaved.
- What if the log is truncated and the root cause isn't visible?
- What if no failure is found (green pipeline pasted by mistake)?
- What if the failure is in a matrix build?

3. Halluzinations-Risiko:
- The model might invent a log line or cite a line that doesn't exist. Need rule: "Only cite lines verbatim from the provided log."
- "Minimal change" might lead to model inventing API calls. Need to ground fixes in the actual log/code context provided.
- The classification list is fixed but model might output something else; enforce strict enum.

4. Fehlende "Output nur, kein Preamble"-Regel:
- It exists but is at the bottom. Also doesn't forbid post-amble (e.g., "Let me know if you need more help"). And doesn't forbid wrapping in markdown code fences if not requested. Strengthen it.

5. Schwache Beispiele:
- There are NO examples at all. The prompt says "Schwache Beispiele" (weak examples) implying they might be missing or weak. They are missing entirely. Need to add a strong example.

Now, structure the response:
Markdown block.
For each change: exact old text snippet, new text, 1 sentence reason.

Let's map changes to the 5 criteria.

**Criterion 1: Ambiguous output format**
Old:
```
## Output format
`FAILED JOB: <name>`
`ROOT FAILURE: <line cite> — <one sentence>`
`CLASS: build|test|lint|deploy|infra`
`FIX: <specific edit>`
`PREVENT: <one line>`
```
New:
```
## Output format
FAILED JOB: <exact job_id from CI YAML, e.g. "build-and-test">
ROOT FAILURE: Line <#>: "<verbatim error snippet from log>" — <one sentence expectation vs reality>
CLASS: build|test|lint|deploy|infra
FIX: <file_path + minimal diff or command, no prose>
PREVENT: <one line concrete action>
```
Reason: Removes ambiguity by specifying exact expected content types and sources for each placeholder.

**Criterion 2: Missing edge-case rules**
Old:
```
## Rules
- Only the FIRST failure matters for the verdict; list others as "cascade".
- Don't suggest bump


## clean-code-reviewer.md

The user wants me to act as a Senior Prompt Engineer and review a provided SKILL.md file for specific weaknesses:
1. Mehrdeutige Formulierungen im Output-Format (Ambiguous formulations in output format)
2. Fehlende Edge-Case-Regeln (Missing edge-case rules)
3. Halluzinations-Risiko (Hallucination risk)
4. Fehlende "Output nur, kein Preamble"-Regel (Missing "output only, no preamble" rule) - wait, actually looking at the SKILL.md, it says "Output ONLY the review. No preamble ("Here is…"/"Sure, …"), no closing wrap-up." So that rule IS present. But let me check if it's strong enough or if there's a subtlety. Actually the prompt says "Pruefe diese SKILL.md auf Schwachstellen: ... 4. Fehlende "Output nur, kein Preamble"-Regel". But the file HAS "Output ONLY the review. No preamble...". Wait, let me re-read. Maybe the user wants me to check if it's missing or weak? Or maybe they think it's missing but it's there? Actually, the instruction says "Pruefe diese SKILL.md auf Schwachstellen: ... 4. Fehlende "Output nur, kein Preamble"-Regel". But the file clearly has it. However, the user says "Sei praezise, keine Einleitung" and "Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund." So I should point out that it's actually present but maybe could be strengthened, OR maybe I should look closer. Wait, actually looking at the output format section: "End with: `VERDICT: ship | ship-with-fixes | block` and one-line reason. Output ONLY the review. No preamble ("Here is…"/"Sure, …"), no closing wrap-up." It's there. But maybe the user's list is a generic checklist and I should only fix what is actually weak. But the user explicitly says "Pruefe... auf Schwachstellen: 1... 2... 3... 4... 5...". If 4 is not a weakness (because it's present), I should maybe note that it's present but could be made more explicit regarding markdown formatting? Or perhaps I should treat the instruction as: check these 5 categories and provide concrete applicable improvements. If something is not a weakness, maybe I don't need to change it, but the user says "Fuer jede Aenderung". Let me look at the 5 points:

1. Mehrdeutige Formulierungen im Output-Format: 
   - "For each finding, prefix the pass number you are in (1=CORRECTNESS, 2=SECURITY, 3=EDGE CASES, 4=CLARITY):" -> "you are in" is ambiguous if multiple findings in same pass? Actually it says "prefix the pass number you are in". That's okay but "file:line" is ambiguous if it's not a file review but a pasted snippet? "Never invent line numbers" is in rules, but output format says "file:line". That's ambiguous/contradictory. If no file/line, what then?
   - "one sentence" - ambiguous length?
   - "suggested fix" - could be ambiguous.

2. Fehlende Edge-Case-Regeln:
   - The process mentions edge cases in pass 3, but the "Rules" section doesn't specify what to do if no edge cases found (should it output "none" or stay silent?). Also no rule about what to do if code is perfect.

3. Halluzinations-Risiko:
   - "Never invent line numbers. Quote the code you mean." -> Good, but "file:line" in output format forces line numbers. If code is provided as raw text without lines, model might invent lines to fit format. That's a hallucination risk.
   - "If you can't verify, say 'I don't know' — never guess." -> Good, but could be strengthened regarding assumptions about intent.

4. Fehlende "Output nur, kein Preamble"-Regel:
   - Actually present: "Output ONLY the review. No preamble...". But maybe the user thinks it's missing? Or maybe I should make it stricter (e.g., no markdown code block wrapping the whole output if not needed, or specifying exactly the format). Actually, looking closely: The output format says "End with: VERDICT...". But doesn't explicitly forbid conversational filler inside the findings (e.g., "I noticed that..."). The rule says "Output ONLY the review" but maybe it should be in the Output format section itself to be tighter.

5. Schwache Beispiele:
   - There are NO examples at all in the SKILL.md. That's a weakness. The user points out "Schwache Beispiele" (weak examples) implying they might be missing or bad. They are missing entirely. So I should add a concrete example.

Let me structure the response as requested:
"Antworte mit KONKRETEN, anwendbaren Verbesserungen als Markdown-Block:
Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund.
Sei praezise, keine Einleitung."

So I will produce a markdown block (maybe using blockquotes or just a list of changes). The user says "als Markdown-Block" and "Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund."

I will use a format like:
```markdown
## Änderung 1: Output-Format Mehrdeutigkeit (file:line)
**Alter Text:**
`[P1] SEVERITY(low|med|high) — file:line — one sentence — suggested fix`
**Neuer Text:**
`[P1] SEVERITY(low|med|high) — location (file:line OR quoted snippet) — one sentence — suggested fix`
**Grund:** Vermeidet Halluzination von Zeilennummern wenn nur Code-Snippets ohne Zeilen gegeben sind.

## Änderung 2: ...
```

Wait, the user said "Antworte mit KONKRETEN, anwendbaren Verbesserungen als Markdown-Block:" and "Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund. Sei praezise, keine Einleitung."

So I should not have an introduction. Just the markdown block with the changes.

Let me go through the 5 points and formulate exact old/new text.

**Point 1: Mehrdeutige Formulierungen im Output-Format**
Old:


## commit-message-writer.md

The user wants me to act as a Senior Prompt Engineer and review a SKILL.md file for weaknesses based on 5 specific criteria:
1. Mehrdeutige Formulierungen im Output-Format (Ambiguous formulations in output format)
2. Fehlende Edge-Case-Regeln (Missing edge-case rules)
3. Halluzinations-Risiko (Hallucination risk)
4. Fehlende "Output nur, kein Preamble"-Regel (Missing "output only, no preamble" rule) - wait, looking at the file, there IS a rule: "Output ONLY the message. No preamble ("Here is…"/"Sure, …") or thank-you." But maybe it's weakly placed or could be stronger/contextualized regarding the SUGGEST SPLIT part?
5. Schwache Beispiele (Weak examples) - there are NO examples in the SKILL.md at all. That's a major weakness.

Let me go through each point and provide concrete, applicable improvements as a Markdown block:
For each change: exact old text snippet, new text, and 1 sentence reason.
Precise, no introduction.

Let's analyze the SKILL.md content:

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
- Output ONLY the message. No preamble ("Here is…"/"Sure, …") or thank-you.

---

Now, checking the 5 weaknesses:

1. Mehrdeutige Formulierungen im Output-Format:
- The output format shows `<type>: <subject>` and then `<optional body, one paragraph, why not what>`. But it also says "If a split is recommended: `SUGGEST SPLIT: ...`". Is the SUGGEST SPLIT part of the block or separate? Ambiguous. Also `<type>` is ambiguous - should it be exactly from the list? What if multiple? 
- "one paragraph" vs "body line only if reason isn't obvious" in process step 3 says "body line" (singular) but output format says "one paragraph". Inconsistent/ambiguous.
- Old: 
```
<type>: <subject>

<optional body, one paragraph, why not what>
```
If a split is recommended: `SUGGEST SPLIT: <commit 1> | <commit 2>`
New: Clarify that split replaces or precedes, and clarify body is max 1 paragraph or single line.

2. Fehlende Edge-Case-Regeln:
- What if input is empty? What if no clear type? What if diff is huge? What if breaking change (conventional commits use `!` or `BREAKING CHANGE:`)? No rule for breaking changes.
- Old: `2. Summarize the WHY in the subject (<= 50 chars, imperative: "add", not "added").`
- New: add breaking change rule? Or add edge case section.
- Old: `## Process` ... `4. If the diff mixes unrelated changes, suggest splitting into 2+ commits.`
- New: Add edge cases like empty input, breaking changes.

3. Halluzinations-Risiko:
- Rule says "Never invent file names not in the input." But what about inventing *reasons* (WHY) not in the diff? Step 2 says "Summarize the WHY". If the why isn't in the diff, the model might hallucinate a why. 
- Old: `2. Summarize the WHY in the subject (<= 50 chars, imperative: "add", not "added").`
- New: `2. Summarize the change in the subject (<= 50 chars, imperative: "add", not "added"). Only state a "why" if it is explicitly mentioned in the input; otherwise describe the "what" concisely.`
- Also old: `- Never invent file names not in the input.` -> expand to never invent reasons/context.

4. Fehlende "Output nur, kein Preamble"-Regel:
- Actually it's there at the bottom: `- Output ONLY the message. No preamble ("Here is…"/"Sure, …") or thank-you.` But it's listed as a bullet in Rules, and it doesn't explicitly cover the SUGGEST SPLIT case (should that also have no preamble?). And it's a bit weak/at the end. Could be made a top-level explicit constraint.
- Old: `- Output ONLY the message. No preamble ("Here is…"/"Sure, …") or thank-you.`
- New: Make it a bold standalone directive and include split output.

5. Schwache Beispiele:
- There are NO examples. Absolutely none. This is the biggest gap.
- Old: (The whole file has no examples section)
- New: Add an `## Examples` section.

Let me structure the response exactly as requested:
"Antworte mit KONKRETEN, anwendbaren Verbesserungen als Markdown-Block:
Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund.
Sei praezise, keine Einleitung."

So I will produce a Markdown block (probably using `> ` or just a section, but "als Markdown-Block" means within ```markdown or just markdown formatted). I'll use a series of blockquotes or just headers with old/new/grund. Actually, "Markdown-Block" could mean a code block with markdown, or just markdown text. I'll provide standard markdown with clear delimiters.

Let's define the changes:

**Change 1 (Mehrdeutige Formulierungen im Output-Format / Weak examples)**
Old:
```
## Output format
```
<type>: <subject>

<optional body, one paragraph, why not what>
```
If a split is recommended: `SUGGEST SPL


## daily-standup-writer.md

The user wants me to act as a Senior Prompt Engineer and review a SKILL.md file for weaknesses based on 5 specific criteria:
1. Mehrdeutige Formulierungen im Output-Format (Ambiguous formulations in output format)
2. Fehlende Edge-Case-Regeln (Missing edge case rules)
3. Halluzinations-Risiko (Hallucination risk)
4. Fehlende "Output nur, kein Preamble"-Regel (Missing "output only, no preamble" rule) - wait, the file actually HAS this rule at the end: "Output ONLY the standup. No preamble ("Here is…"/"Sure, …")." But maybe it needs to be stronger or placed better? Or maybe the instruction says "Fehlende" but I should note if it's actually present but weak? Actually, looking at the prompt: "4. Fehlende 'Output nur, kein Preamble'-Regel". The file has it, but maybe it's not strict enough or doesn't cover postamble? Or maybe I should point out that while present, it's at the bottom and could be ambiguous about formatting? Wait, the instruction says "Pruefe diese SKILL.md auf Schwachstellen: ... 4. Fehlende 'Output nur, kein Preamble'-Regel". I should check if it's actually missing or weak. It says "Output ONLY the standup. No preamble...". That's present. But maybe it doesn't forbid markdown code blocks wrapping or explanations after? Or maybe the user thinks it's missing but it's there, so I should correct it or strengthen it? The prompt says "Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund." I should treat the "weaknesses" as things to fix. If #4 is listed as a thing to check, and it's technically there but maybe not robust (e.g., allows trailing comments, or doesn't specify exact format), I can improve it. Actually, the user says "Pruefe... auf Schwachstellen: 1... 2... 3... 4... 5...". They want me to find these weaknesses. If #4 is actually present in the text ("Output ONLY the standup. No preamble..."), then maybe the weakness is that it's not explicit enough about *no postamble* or *no markdown fences*? Or maybe the user made a mistake and I should point out that it exists but is weak? I will treat it as: the rule exists but is insufficient/weak (e.g., doesn't forbid wrapping in code blocks or adding postscript). Actually, re-reading: "Fehlende 'Output nur, kein Preamble'-Regel" - maybe they consider it missing because it's buried at the end and not in the Output section? I'll improve it to be more strict and central.

Let's go through each point:

**1. Mehrdeutige Formulierungen im Output-Format**
Old:
```
- GESTERN: completed work, outcomes not activity
- HEUTE: the single most important next thing
- BLOCKER: real impediments only; if none, write "Keine" (DE) or "None" (EN), matching the user's language
```
Weakness: "plain German or English (match user)" is in the intro of Output, but the BLOCKER rule specifies "matching the user's language" again - slightly redundant but okay. "1-3 bullets" - does that mean per section or total? "Three sections, each 1-3 bullets" -> that's clear actually. But "outcomes not activity" is a bit abstract. Also, the format of the headers: should they be markdown headers or just text? "Three sections" - is it `## GESTERN` or `- GESTERN:`? The example uses `- GESTERN:`. That's a bullet, not a section header. Ambiguous.
Also: "plain German or English (match user)" - what if user writes in Spanish? "match user" implies match input language, but only DE/EN specified in BLOCKER.
Improvement: Make the format explicit (e.g., use exactly `GESTERN:` / `HEUTE:` / `BLOCKER:` as labels, not markdown H2). Specify language fallback.

Old text snippet:
`Three sections, each 1-3 bullets, plain German or English (match user):`
New:
`Exactly three labeled blocks using the format \`GESTERN:\`, \`HEUTE:\`, \`BLOCKER:\` (one per line, followed by 1-3 bullets). Use the user's input language; if not DE/EN, default to English.`
Reason: Removes ambiguity about section formatting and language fallback.

Old text snippet:
`- GESTERN: completed work, outcomes not activity`
New:
`- GESTERN: completed work described as verifiable outcomes (e.g., "API latency reduced by 20%"), not process or activity`
Reason: Clarifies "outcomes not activity" with a concrete definition to prevent vague bullets.

**2. Fehlende Edge-Case-Regeln**
Old:
`## Rules`
`- Lead with outcome ("Login fixed" not "Worked on login").`
`- No jargon padding. Under 120 words total.`
`- If input is ambiguous, summarize what you inferred before the update.`
`- Output ONLY the standup. No preamble ("Here is…"/"Sure, …").`

Missing edge cases:
- What if input is empty?
- What if user provides work that spans more than "yesterday" (e.g., last week)?
- What if HEUTE has multiple equal priorities? Rule says "single most important" but edge case: tie?
- What if input is already a perfect standup?
- What if commits are merge commits or dependency bumps with no "outcome"?

Add edge case rules.
Old snippet:
`## Rules
- Lead with outcome ("Login fixed" not "Worked on login").`
New:
`## Rules
- If input is empty or contains no actionable work, return only "Keine Eingabe / No input provided" in the matched language.
- Ignore merge commits, version bumps, and automated CI messages unless they contain user-facing outcomes.
- Lead with outcome ("Login fixed" not "Worked on login").`
Reason: Covers empty input and noise in git commits as concrete edge cases.

**3. Halluzinations-Risiko**
Old:
`- Lead with outcome ("Login fixed" not "Worked on login").`
Risk: Model might infer outcomes not stated in input (e.g., "Login fixed" when commit says "Refactored auth module"). The rule "If input is ambiguous, summarize what you inferred before the update" actually *encourages* inference, which can lead to hallucination if it infers wrong outcomes.
Old snippet:
`If input is ambiguous, summarize what you inferred before the update.`
New:
`If


## messy-data-cleaner.md

The user wants me to act as a Senior Prompt Engineer and review a SKILL.md file for specific weaknesses:
1. Mehrdeutige Formulierungen im Output-Format (Ambiguous formulations in the output format)
2. Fehlende Edge-Case-Regeln (Missing edge-case rules)
3. Halluzinations-Risiko (Hallucination risk)
4. Fehlende "Output nur, kein Preamble"-Regel (Missing "output only, no preamble" rule) - wait, the SKILL.md actually HAS this rule at the bottom: "Output ONLY the ISSUES…RECIPE block. No preamble ("Here is…"/"Sure, …")." But maybe it needs to be stronger or more explicit, or maybe the instruction says "check if it's missing" and if it's there, improve it? Actually, looking at the prompt: "Pruefe diese SKILL.md auf Schwachstellen: ... 4. Fehlende 'Output nur, kein Preamble'-Regel". The file has it, but maybe it's weak or placed poorly or could be more strict. Or maybe I should treat it as "improve the existing one to be bulletproof". Actually the prompt says "Fehlende... Regel" as a category to check. Since it's present but perhaps not fully robust (e.g., doesn't forbid explanations outside the block, or trailing commentary), I will improve it.
5. Schwache Beispiele (Weak examples) - there are NO examples in the SKILL.md. So I need to add them or specify them.

The user wants:
- KONKRETEN, anwendbaren Verbesserungen als Markdown-Block
- Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund.
- Sei praezise, keine Einleitung.

Let's go through the weaknesses:

1. Mehrdeutige Formulierungen im Output-Format:
Old:
```
## Output format
`ISSUES FOUND: <bullet list>`
`CLEANED DATA: <table or code block>`  (state row count before → after, e.g. "4 → 3 rows")
`RECIPE: <numbered, tool-agnostic steps>`
```
Issues: "<table or code block>" is ambiguous. Should specify format (e.g., Markdown table). "bullet list" not specified if it should be markdown bullets. The parentheses note about row count is informal.
New:
```
## Output format
`ISSUES FOUND:` (followed by a Markdown bullet list, one issue per line)
`CLEANED DATA:` (followed by a Markdown table exactly matching the normalized schema; immediately below it write: `Row count: <before> -> <after>`)
`RECIPE:` (followed by a Markdown numbered list of tool-agnostic steps)
```
Grund: Eliminiert die Mehrdeutigkeit zwischen Tabellen- und Codeblock-Format und erzwingt ein einheitliches, maschinenlesbares Markdown-Layout.

2. Fehlende Edge-Case-Regeln:
Old:
```
## Rules
- Never overwrite a value you're unsure about — flag it (`# REVIEW: <reason>`).
- Show before/after row counts so the user sees what changed.
- If a column's meaning is ambiguous, ask or label the assumption explicitly.
- Output ONLY the ISSUES…RECIPE block. No preamble ("Here is…"/"Sure, …").
```
(We will modify the Rules section to add edge cases, but we need to isolate the change or replace the whole block? The instruction says "exakten alten Text-Ausschnitt, den neuen Text". I can take the `## Rules` block or just add to it. Let's take the old Rules block and add edge cases.)
Actually, better to take the specific lines or the section. Let's take the whole Rules section as old and add edge cases.
Old:
```
## Rules
- Never overwrite a value you're unsure about — flag it (`# REVIEW: <reason>`).
- Show before/after row counts so the user sees what changed.
- If a column's meaning is ambiguous, ask or label the assumption explicitly.
- Output ONLY the ISSUES…RECIPE block. No preamble ("Here is…"/"Sure, …").
```
New:
```
## Rules
- Never overwrite a value you're unsure about — flag it (`# REVIEW: <reason>`).
- Show before/after row counts so the user sees what changed.
- If a column's meaning is ambiguous, ask or label the assumption explicitly.
- Output ONLY the ISSUES…RECIPE block. No preamble ("Here is…"/"Sure, …").
- Edge cases: If input has zero rows, output `CLEANED DATA: <empty>` and note `Row count: 0 -> 0`. If a cell contains only whitespace, treat as NULL. If date parsing fails, flag with `# REVIEW: unparseable date` instead of guessing.
```
Grund: Definiert explizite Verhaltensweisen für leere Inputs, reine Whitespace-Zellen und Parsing-Fehler, um Inkonsistenzen zu vermeiden.

3. Halluzinations-Risiko:
Old:
```
2. CLEAN (in order): trim whitespace -> unify casing -> parse dates to ISO (YYYY-MM-DD) -> coerce numbers (strip currency/%/commas) -> drop exact duplicates -> flag, don't silently delete, near-duplicates.
```
(The risk is "unify casing" might arbitrarily change data meaning, or "coerce numbers" might invent values. Also "flag near-duplicates" without defining similarity threshold is a hallucination risk.)
Better to take the CLEAN step and the PROFILE step.
Old:
```
1. PROFILE — State the columns, detected types, and obvious issues (blanks, dupes, mixed formats).
2. CLEAN (in order): trim whitespace -> unify casing -> parse dates to ISO (YYYY-MM-DD) -> coerce numbers (strip currency/%/commas) -> drop exact duplicates -> flag, don't silently delete, near-duplicates.
```
New:
```
1. PROFILE — State the columns, detected types (based ONLY on provided data), and obvious issues (blanks, exact dupes, mixed formats). Do not infer external context.
2. CLEAN (in order): trim whitespace -> unify casing ONLY for categorical/string columns where it does not alter meaning (e.g., lowercase emails, not free text) -> parse dates to ISO (YYYY-MM-DD) using explicit formats found in PROFILE -> coerce numbers (strip currency/%/commas) using only visible characters -> drop exact duplicates -> flag near-duplicates ONLY if similarity is >90% on all columns.
```
Grund: Reduziert Halluzinations-Risiko, indem Inference auf sichtbare Daten beschränkt und Casing- sowie Duplikat


## root-cause-debugger.md

The user wants me to act as a Senior Prompt Engineer and review a SKILL.md file for weaknesses based on 5 specific criteria:
1. Mehrdeutige Formulierungen im Output-Format (Ambiguous formulations in output format)
2. Fehlende Edge-Case-Regeln (Missing edge-case rules)
3. Halluzinations-Risiko (Hallucination risk)
4. Fehlende "Output nur, kein Preamble"-Regel (Missing "output only, no preamble" rule) - wait, looking at the SKILL.md, there IS a rule: "Output ONLY the SYMPTOM…FIX block. No preamble ("Here is…"/"Sure, …")." But the user asks to check for "Fehlende 'Output nur, kein Preamble'-Regel" - maybe it's there but weak, or maybe they want me to verify/strengthen it? Actually, the prompt says "Pruefe diese SKILL.md auf Schwachstellen: ... 4. Fehlende 'Output nur, kein Preamble'-Regel". Even though there is a rule, it might be considered weak or not strict enough (e.g., doesn't forbid postamble, doesn't forbid markdown wrapping if it breaks parsing, etc.). Or maybe I should point out that while it exists, it's not enforcing raw output strictly enough (e.g. backticks might cause confusion, or it doesn't say "no explanations outside the block").
5. Schwache Beispiele (Weak examples) - there are NO examples in the SKILL.md. That's a clear weakness.

The user wants me to respond with CONCRETE, applicable improvements as a Markdown block:
For each change: exact old text snippet, new text, and 1 sentence reason.
Precise, no introduction.

Let's go through the criteria and find specific fixes:

**1. Mehrdeutige Formulierungen im Output-Format**
Old:
```
`SYMPTOM: <one line>`
`ROOT CAUSE: <layer + one sentence>`
`EVIDENCE: <what proves it, cite pasted code/trace>`
`NEXT CHECK: <one concrete step to confirm>`
`FIX (only after NEXT CHECK passes): <smallest change>`
```
Issues:
- "layer + one sentence" is ambiguous about format.
- "cite pasted code/trace" is ambiguous (how? line numbers?).
- The backticks around the format template might make the model output markdown code blocks instead of raw text. This connects to point 4.
- "only after NEXT CHECK passes" is ambiguous: does the model output FIX conditionally or always leave it blank? It says "FIX (only after NEXT CHECK passes):" but doesn't say what to do if it hasn't passed (e.g., user hasn't run it yet). The model is generating text, it can't know if the user ran it. So this is ambiguous: should the model output the FIX proactively with a caveat, or output "PENDING: run NEXT CHECK"?

Improvement for ambiguity:
Old: `ROOT CAUSE: <layer + one sentence>`
New: `ROOT CAUSE: [network|parse|state|concurrency|config|other]: <one sentence stating cause>`
Reason: Removes ambiguity about how to format the layer and cause.

Old: `EVIDENCE: <what proves it, cite pasted code/trace>`
New: `EVIDENCE: <file:line or trace line number> — <observation>`
Reason: Forces precise citation format to avoid vague referencing.

Old: `FIX (only after NEXT CHECK passes): <smallest change>`
New: `FIX: <smallest change, or "BLOCKED: awaiting NEXT CHECK result" if not yet verified>`
Reason: Clarifies that the model must output the block completely and handles the impossible "only after passes" temporal logic for a static response.

**2. Fehlende Edge-Case-Regeln**
Old:
```
## Rules
- Never edit code before the hypothesis is testable.
- Distinguish "I know" from "I suspect" — label each.
- If the pasted material is insufficient, ask for the exact missing artifact; don't invent a stack trace.
- Output ONLY the SYMPTOM…FIX block. No preamble ("Here is…"/"Sure, …").
```
New (add rules):
```
## Rules
- Never edit code before the hypothesis is testable.
- Distinguish "I know" from "I suspect" — label each.
- If the pasted material is insufficient, ask for the exact missing artifact; don't invent a stack trace.
- Output ONLY the SYMPTOM…FIX block. No preamble ("Here is…"/"Sure, …").
- If multiple independent root causes are possible, output one SYMPTOM/ROOT CAUSE block per cause, separated by a blank line.
- If the error is a known 3rd-party library bug, state the library version and link-free reference in ROOT CAUSE and skip LOCALIZE code citation.
```
Actually, let's pick the most relevant edge cases:
- Multiple errors / concurrent causes.
- No code pasted, only error text.
- The "cannot reproduce yet" from phase 1 needs to reflect in output.

Let's do:
Old:
```
- If the pasted material is insufficient, ask for the exact missing artifact; don't invent a stack trace.
```
New:
```
- If the pasted material is insufficient, ask for the exact missing artifact; don't invent a stack trace.
- If phase 1 yields "cannot reproduce yet", output SYMPTOM and ROOT CAUSE: "unknown — cannot reproduce", then NEXT CHECK must be a repro step.
- If multiple distinct failures are in the paste, output separate SYMPTOM/ROOT CAUSE/EVIDENCE/NEXT CHECK/FIX blocks per failure.
```
Reason: Covers non-reproducible states and multi-error pastes as explicit edge cases.

**3. Halluzinations-Risiko**
Old:
```
2. LOCALIZE — Trace the failure to the layer (network, parse, state, concurrency, config). Cite the line/file from the pasted code only.
```
New:
```
2. LOCALIZE — Trace the failure to the layer (network, parse, state, concurrency, config). Cite the line/file from the pasted code ONLY; if not present in paste, state "no code pasted" and do not infer filenames.
```
Reason: Prevents the model from hallucinating file paths or line numbers not provided in the input.

And maybe in Rules:
Old: `- Never edit code before the hypothesis is testable.`
New: `- Never edit code before the hypothesis is testable. Never suggest a FIX that introduces APIs or functions not present in the pasted context or standard library of the stated language.`
Reason: Mitigates hallucination of non-existent helper functions in the fix.

**4. Fehlende "Output


## test-case-generator.md

The user wants me to act as a Senior Prompt Engineer and review the provided SKILL.md for weaknesses based on 5 specific criteria:
1. Mehrdeutige Formulierungen im Output-Format (Ambiguous formulations in output format)
2. Fehlende Edge-Case-Regeln (Missing edge-case rules)
3. Halluzinations-Risiko (Hallucination risk)
4. Fehlende "Output nur, kein Preamble"-Regel (Missing "output only, no preamble" rule) - wait, the SKILL.md actually HAS this rule at the bottom: "Output ONLY the test cases. No preamble ("Here is…"/"Sure, …")." But maybe it's not strict enough or placed weirdly, or maybe the user wants me to check if it's missing/weak? Actually the prompt says "Pruefe diese SKILL.md auf Schwachstellen: ... 4. Fehlende 'Output nur, kein Preamble'-Regel". The file actually has it, but perhaps it's weak or could be strengthened, or maybe the user thinks it's missing but it's there. I should note that it exists but is weak/needs reinforcement regarding postamble too, or maybe the user meant it's technically there but formulated as a "Rule" at the end rather than being explicit in the Output format section. Actually, looking closely: the rule says "Output ONLY the test cases. No preamble". But it doesn't forbid postamble (like "Let me know if you need more"). Also, the "If behavior is ambiguous, list the assumptions you made before generating" under Input contradicts the "Output ONLY the test cases" rule if assumptions are listed in the output. That's a conflict! That's a real weakness. The Input section says "If behavior is ambiguous, list the assumptions you made before generating." But the Rules section says "Output ONLY the test cases. No preamble". So if ambiguous, it must output assumptions (which is not test cases) AND only output test cases? That's a contradiction/ambiguity.

Let me go through the 5 points systematically and provide concrete applicable improvements as a Markdown block with: exact old text snippet, new text, 1 sentence reason.

Criteria check:
1. Mehrdeutige Formulierungen im Output-Format:
- `End with a one-line coverage gap note (what you could NOT derive from the input).` -> This contradicts "Output ONLY the test cases" or is ambiguous about format. Also the format string `TC-{n} [P0|P1|P2] — given: <input> — when: <action> — then: <expected>` uses em-dashes and placeholders but doesn't specify if `<input>` should be literal code or natural language. Also "TC-{n}" - is n global or per category?
- "given: <input> — when: <action> — then: <expected>" is Gherkin-ish but "input" vs "action" might be ambiguous for a pure function (input is the arg, action is calling the function). It's okay but could be stricter.

2. Fehlende Edge-Case-Regeln:
- Under Process -> EDGE CASES: "empty/null, boundary values, off-by-one, max size, unicode/encoding." This is a list but not a rule that it MUST cover at least one of each if applicable, or how to handle when not applicable. Also concurrency/race conditions missing. Also "negative numbers" if numeric.

3. Halluzinations-Risiko:
- "No code you can't justify. If the function isn't shown, generate from the spec and say so." -> But the rule says "Output ONLY the test cases". If it says "generated from spec" inside the output, that breaks the rule. Also, it might hallucinate specific framework (Jest, Pytest) even though format is framework-agnostic. The description says "in a runnable format" but output format is just TC- lines. That's a mismatch -> hallucination risk of "runnable" vs actual format.
- Also: "Accept: a function signature, a REST/GraphQL endpoint, or 5-10 lines of spec." If user gives a function signature only (e.g., `def add(a,b): ...` without body), the model might hallucinate the behavior. The rule says "If the function isn't shown, generate from the spec" but signature is not spec.

4. Fehlende "Output nur, kein Preamble"-Regel:
- The rule exists but is at the bottom and contradicts the "list assumptions" instruction. Also doesn't forbid postamble/closing remarks. And doesn't explicitly forbid markdown code fences if not needed, or explanations per case.

5. Schwache Beispiele:
- There are NO examples at all in the SKILL.md. The prompt says "Schwache Beispiele" (weak examples) implying they might be missing or weak. They are completely missing. Need to add a concrete example.

Now, structure the answer exactly as requested:
"Antworte mit KONKRETEN, anwendbaren Verbesserungen als Markdown-Block:
Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund.
Sei praezise, keine Einleitung."

So I will produce a Markdown block (probably using headings or a list or a table, but the instruction says "Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund." I can use bold labels or a specific format).

Let's draft the changes:

Change 1 (Addressing ambiguity in output format + contradiction with assumptions + preamble):
Old:
```
If behavior is ambiguous, list the assumptions you made before generating.
```
New:
```
If behavior is ambiguous, emit a single `ASSUMPTIONS:` block strictly before the test cases containing only bullets, then proceed to test cases.
```
Grund: Dies verhindert den Widerspruch zur "Output ONLY"-Regel, indem Annahmen formal als erlaubter Präfix definiert werden.

Change 2 (Output format ambiguity - coverage gap note contradicts ONLY test cases):
Old:
```
End with a one-line coverage gap note (what you could NOT derive from the input).
```
New:
```
Emit the coverage gap note as a final line prefixed with `GAPS: ` (e.g., `GAPS: Timeout behavior undetermined from signature alone.`) without any other trailing text.
```
Grund: Die explizite Präfix-Angabe `GAPS:` macht das Format eindeutig und kompatibel mit der Strikt-Ausgabe-Regel.

Change 3 (Output format template ambiguity):
Old:
```
For each case: `TC-{n} [P0|P1|P2] — given: <input> — when: <action> — then: <expected>`
```
New:
```
For each case use
