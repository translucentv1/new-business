# PAKET A — Agent Skills (Claude Skill + ChatGPT Skill)

## Nischen-Wahl (MEASURED belegt)
- PromptBase "Agent Skills" ist ein NEUER Item-Typ (SKILL.md files).
  Quelle: https://promptbase.com/sell ("Sell AI prompts or agent skills (SKILL.md files)")
- Marketplace-Share (MEASURED, https://promptbase.com/popular-models, Updated Jul 13 2026):
  "Claude Skill" = 3% (Rang 6), "ChatGPT Skill" = 1% (Rang 8).
  -> Nischen sind JUNG und UNGESAETTIGT im Vergleich zu Image-Prompts
     (ChatGPT Image 49%, Midjourney 20%).
- Die Skill-Marketplace-Liste (https://promptbase.com/marketplace?itemType=skill&sortBy=score)
  zeigte bei "Most Popular Skills of All time" KEINE einzelnen Listings,
  NUR Filter-Kategorien (Coding, DevOps, Writing, Productivity, Refactor,
  Review, Testing, Research, Workflow, Git, Frontend, Backend, Data, Docs,
  Debug, Gaming, Fashion, Food). -> Marktluecke: konkrete, sofort nutzbare
  Skills fehlen weitgehend.
- Gebuehr (MEASURED, /sell): 0% ueber eigenen Link, 20% ueber Marketplace.
- Auszahlung (MEASURED, /sell): Stripe oder Zoneless (NICHT eingerichtet).

## Empfehlung
Diese Nische hat die beste Chance bei niedrigster Konkurrenz, weil:
(1) Hermes/Skill-Engineering die Kernkompetenz ist, (2) die Kategorie neu ist,
(3) die Preise fuer Skills hoeher sein koennen als $2.99-Image-Prompts
(Text/"One Person Business Builder" $9.99 MEASURED bei business-Suche).

## Skill 1 — "Hermes Clean Code Reviewer" (Claude Skill)
- Modell: Claude (Claude Skill)
- Kategorie: Review / Coding
- Vorgeschlagener Preis: $6.99 (Text-Skill, hoeher als Image-Prompts;
  Referenz: business GPT-Prompts bis $9.99 MEASURED)
- Vorgeschlagener Titel: "Senior Code Reviewer — Catches Bugs Before They Ship (Claude Skill)"
- SKILL.md (der verkaufte Inhalt):

---
name: clean-code-reviewer
description: Use when asked to review code, a pull request, or a diff for bugs, security issues, and quality. Runs a structured multi-pass review.
---

# Clean Code Reviewer

You are a senior engineer reviewing a teammate's change. Be direct, kind, and specific.

## Process (4 passes, in order)
1. CORRECTNESS — Does it do what the request says? Trace inputs to outputs.
   Flag logic bugs, off-by-one, wrong types, unhandled null/undefined.
2. SECURITY — Any injection, auth bypass, secret leak, unsafe eval, path traversal?
3. EDGE CASES — Empty input, huge input, concurrency, network failure, encoding.
4. CLARITY — Could a teammate understand it in 6 months? Name smells, dead code.

## Output format
For each finding: `[PASS 1-4] SEVERITY(low|med|high) — file:line — one sentence — suggested fix`
End with: `VERDICT: ship | ship-with-fixes | block` and one-line reason.

## Rules
- Never invent line numbers. Quote the code you mean.
- Prefer the smallest fix. Don't rewrite working code for style.
- If you can't verify, say "I don't know" — never guess.
---

## Skill 2 — "Daily Standup Writer" (ChatGPT Skill)
- Modell: ChatGPT (ChatGPT Skill)
- Kategorie: Writing / Productivity
- Vorgeschlagener Preis: $4.99
- Vorgeschlagener Titel: "Instant Daily Standup & Status Update Writer (ChatGPT Skill)"
- SKILL.md:

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
- BLOCKER: real impediments only; if none, write "Keine"

## Rules
- Lead with outcome ("Login fixed" not "Worked on login").
- No jargon padding. Under 120 words total.
- If input is ambiguous, summarize what you inferred before the update.
---

## Preview-Bild-Konzept (fuer Listing-Cover)
- Skill 1: Screenshot-Mockup eines Code-Review-Diffs mit gruenen/roten Markierungen
  + Badge "Claude Skill". Tool: kann mit ChatGPT Image oder Midjourney gerendert
  werden (Prompt liegt in Paket B-Stil), aber HARD-STOP: kein Account, daher nur
  Konzept-Beschreibung, kein echtes Bild generiert.
- Skill 2: Mockup eines Standup-Tickets (Jira/Slack-Stil) mit den 3 Sektionen.

## Status
- Prompts + SKILL.md + Titel + Beschreibung + Preview-Konzept: FERTIG (lokal).
- Veröffentlichung: NICHT erfolgt (HARD-STOP). Nutzer muss Account + Stripe/Zoneless anlegen.
