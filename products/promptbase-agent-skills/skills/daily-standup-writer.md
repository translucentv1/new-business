---
name: daily-standup-writer
description: Use when the user pastes git commits, a diff, or a bullet list of work and wants a clean standup / status update.
---

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
- If input is empty, return only "Keine Eingabe / No input provided" (matched language).
- Ignore merge commits, version bumps, automated CI messages unless user-facing.
- Output ONLY the standup. No preamble, no postscript, no code fence around all.

## Examples
Input: "fixed login bug; reviewed PR #14; started checkout refactor"
Output:
  GESTERN:
  - Login-Bug gefixt
  - PR #14 reviewed
  HEUTE:
  - Checkout-Refactor abschließen
  BLOCKER:
  - Keine
