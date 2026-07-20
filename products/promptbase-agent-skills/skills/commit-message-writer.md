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
