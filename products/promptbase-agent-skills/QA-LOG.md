# SKILL QA-LOG (Ticket A) — MEASURED 2026-07-20 23:04
Modell: tencent/hy3:free | 7 Skills auf realistischem Input getestet

## commit-message-writer: PROBLEM (finish=length)
  Checks: {'type_prefix': False, 'no_preamble': True}
  Output (excerpt):
```
The user is giving me an input that looks like a simulated call to the skill, but wait—the system instruction earlier was: "Act as a Senior Prompt Engineer and improve the provided SKILL.md file according to specific rules... Answer ONLY with the improved SKILL.md (including frontmatter)."

But now the user says: "Input: git diff: changed whispercpp_stt.py to convert audio to wav via ffmpeg before calling whisper_cli. Produce your output per your instructions."

This is a bit of a role-play twist. The user is acting as if they are the system invoking the *improved skill* on a sample input, OR 
```

## ci-pipeline-trier: PASS (finish=length)
  Checks: {'has_failed_job': True, 'has_fix': True}
  Output (excerpt):
```
The user is providing a sample input (a failed CI log snippet) and asking me to "Produce your output per your instructions."

Wait, let me re-read the system prompt / original instruction.
The system prompt said: "The user wants me to act as a Senior Prompt Engineer and improve a given SKILL.md file."
Then the user (in this turns) gave me:
"Input:
GitHub Actions run failed:
Error: process '/usr/bin/npm' failed with exit code 1
at Run npm ci
ENOENT: no such file or directory, open package-lock.json

Produce your output per your instructions."

Ah, this is a test of the *improved SKILL.md* I was
```

## root-cause-debugger: PROBLEM (finish=length)
  Checks: {'has_symptom': False, 'has_root_cause': True}
  Output (excerpt):
```
The user wants me to act as the root-cause debugger. They've given me an error:

```
TypeError: Cannot read properties of undefined (reading 'map')
    at renderList (app.js:42)
Works locally, crashes in prod after deploy.
```

And they want me to follow my instructions: 4 phases in order:
1. REPRODUCE — What is the minimal input/state that triggers it? If unknown, say "cannot reproduce yet".
2. LOCALIZE — Trace the failure to the layer (network, parse, ... (the instructions got cut off but I can infer the rest: state, render, etc.)
3. (probably) HYPOTHESIZE / IDENTIFY ROOT CAUSE
4. (probably)
```

## daily-standup-writer: PROBLEM (finish=length)
  Checks: {'has_gestern': False, 'has_heute': True, 'has_blocker': False}
  Output (excerpt):
```
The user is giving me an input that looks like a standup draft and says "Produce your output per your instructions." But wait, my instructions as the Senior Prompt Engineer were to *improve the SKILL.md file* and reply ONLY with the improved SKILL.md. However, the user's new message says: "Input: Today I fixed login bug... Produce your output per your instructions."

This is a test. The user is acting as if they are the end-user of the skill, providing the raw input, and asking me to produce the output "per your instructions" (meaning per the SKILL.md I just crafted, or per the original person
```

## messy-data-cleaner: PROBLEM (finish=length)
  Checks: {'mentions_dedupe': False, 'mentions_normalize': True}
  Output (excerpt):
```
We need to act as the improved SKILL.md would instruct. The user gave an input: a CSV snippet with some issues. We must output ONLY the three sections: ISSUES FOUND, CLEANED DATA, RECIPE, strictly following the format defined in the improved SKILL.md we just created (but note: the user is asking us to "Produce your output per your instructions." That means we should behave as the skill instructs, outputting the cleaning result for this input. However, the system prompt earlier said: "Reply ONLY with the improved SKILL.md including frontmatter." But that was for the previous turn where we were 
```

## test-case-generator: PASS (finish=stop)
  Checks: {'has_p0': True, 'has_given_when_then': True}
  Output (excerpt):
```
Assumptions:
- Function operates on numeric types (int/float) as no type hints given.
- Python 3 true division semantics apply (returns float).
- No input validation; b=0 raises ZeroDivisionError, non-numeric raises TypeError.
- No side effects.

TC-1 [P0] — given: a=10, b=2 — when: call divide(10, 2) — then: returns 5.0
TC-2 [P0] — given: a=10, b=0 — when: call divide(10, 0) — then: raises ZeroDivisionError
TC-3 [P1] — given: a=0, b=5 — when: call divide(0, 5) — then: returns 0.0
TC-4 [P1] — given: a=1.5, b=0.5 — when: call divide(1.5, 0.5) — then: returns 3.0
TC-5 [P2] — given: a=-10, b=2 — 
```

## clean-code-reviewer: PASS (finish=length)
  Checks: {'has_p1_p4': True, 'has_verdict': True}
  Output (excerpt):
```
The user is providing an example input and asking me to "Produce your output per your instructions."

Wait, let me re-read the conversation. The user's first message was a system/persona instruction: "You are a Senior Prompt Engineer... improve this SKILL.md...". Then they gave the original SKILL.md. Then in the second turn, the user says: "Input: def get(u): x = db.query('SELECT * FROM u WHERE id='+u) return x. Produce your output per your instructions."

But wait, the user's first message said: "Answer ONLY with the improved SKILL.md (including frontmatter)." So in the first turn, I should h
```
