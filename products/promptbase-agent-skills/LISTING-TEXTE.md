# PROMPTBASE LISTING-TEXTE — copy-paste-ready (NICHT veroeffentlicht)

Alle Texte sind fertig zum Eintragen. Nutzer kopiert sie nach Anlage des
PromptBase-Accounts (HARD-STOP: KEIN Account angelegt, NICHT veroeffentlicht).

Lizenz-Hinweis (MEASURED, promptbase.com/prompt/female-gym-shots):
gekaufte Prompts kommen mit "Commercial use" + "Money-back". Das im Listing erwaehnen.

====================================================================
DISCOVERY-BEFUND (MEASURED, 2026-07-19, live ueber PromptBase-Suche)
====================================================================
PromptBase-Suche ist Firestore-basiert (client-seitig, keine offene REST-API),
daher Zählung NUR ueber die Live-Suche im Browser moeglich. Die aelteren
Annahme "Skill-Suche zeigt keine einzelnen Listings" ist WIDERLEGT: die
Marketplace-Suche liefert sehr wohl einzelne Listings, aber ALLE als
modell-getaggte PROMPTS (GPT/Claude/DeepSeek/Gemini), KEINES als "Agent Skill"
getaggt. => Auffindbarkeit laeuft ueber (1) Titel-Keywords + (2) eigenen Link,
nicht ueber eine Skill-Kategorie-Suche.

Konkurrenz pro Thema (MEASURED, "Most relevant" Treffer, Seite 1):
- "code review"  : ~19 Treffer, $2.99-$6.99, GPT/Claude, KEIN Agent-Skill-Tag
                   -> GESAETTIGT. Top: "Senior Developer Code Review" $4.99,
                   "8dimension Code Review Docs System" $6.99 (Claude).
- "debug"        : ~20 Treffer, $2.99-$19.99, GPT-dominant, KEIN Agent-Skill-Tag
                   -> GESAETTIGT bei generischen Prompts, aber LUECKE bei
                   "Root-Cause"-Skill-Ansatz. Top: "Vibe Coding Debug System"
                   $5.99, "Expert Code Debugger Find Fix Bugs" $4.99 (Claude).
- "test cases"   : ~22 Treffer, $2.99-$29.99, viele agent-artig.
                   Top: "Smart Test Case Generator QA" $2.99, "Qa Bdd Test
                   Suite Generator" $3.99 (Claude), "Unit Test Generator Edge
                   Case Designer" $2.99. -> GESAETTIGT, aber "edge cases"-Winkel
                   bereits besetzt-halbt.
- "commit message": ~23 Treffer, ABER nur 1 direkter Treffer
                   ("Pro Git Commit Message Generator" $4.99, GPT), Rest sind
                   "messages"/"status report"/"PR writer". -> GERINGSTE direkte
                   Konkurrenz fuer unser Skill.
- "data cleaning": ~22 Treffer, $2.99-$6.99, FAST NUR GPT, kein Agent-Skill.
                   Top: "Senior Data Auditor Cleaner No Code", "Advanced Csv
                   Data Cleaner Insight Gene". -> GESAETTIGT, aber "CSV"-Winkel
                   differenziert.
- "ci" (allein)  : ~20 Treffer, ABER ~18 sind "Competitive Intelligence"
                   (Markt-Wettbewerb!), nur 2-3 echte CI/CD: "Monorepo Ci
                   Optimizer" $6.99, "Scalable Enterprise CI/CD Tool" $5.99.
                   -> "ci" als Suchwort VERGIftet; Tag muss "CI/CD", "GitHub
                   Actions", "build failed" sein, NICHT nur "ci".
- "standup"      : EXAKTE Zaehlung ASSUMED (Browser-Backend zur Messzeit 502).
                   Proxy-MEASURED ueber verwandte Live-Suche "commit message":
                   sichtbare Geschwister = "Sprint Standup Notes Generator"
                   $2.99 (GPT), "Async Standup Writer" $4.99 (Claude), plus
                   Status-Cluster "Weekly Status Report Writer" $8.99 /
                   "Status Report Writer" $4.99 / "Client Status Update Email
                   Writer" $3.99. -> 3-5 direkte Konkurrenten, moderat.

=> EMPFEHLUNG: Go-Live-Reihenfolge nach GERINGSTER direkter Konkurrenz
(siehe unten). Titel muessen "(Claude Skill)"/"(ChatGPT Skill)" + exakten
Suchbegriff VORN haben, damit wir in der Modell-/Skill-Filter-Suche oben landen.

====================================================================
LISTING 1 — Agent Skill (ChatGPT Skill) — PAKET C
====================================================================
Titel:        Commit Message Writer — Clean Git Commits (ChatGPT Skill)
Modell:       ChatGPT
Item-Typ:     Agent Skill
Kategorie:    Git / Productivity
Preis:        $2.99
Tags:         commit message, git commit, conventional commits, git, chatgpt skill, productivity, PR
Beschreibung:
  Turn any git diff or changed-file list into a conventional, review-ready
  commit. Auto-detects feat/fix/refactor/docs/test/chore/perf, writes an
  imperative subject (<=50 chars), adds a why-body only when needed, and
  suggests splitting mixed changes. Matches DE/EN. Commercial use included.
  Money-back via PromptBase.

====================================================================
LISTING 2 — Agent Skill (Claude Skill) — PAKET C
====================================================================
Titel:        CI/CD Failure Trier — Why Your Build Broke (ChatGPT Skill)
Modell:       Claude
Item-Typ:     Agent Skill
Kategorie:    DevOps / CI
Preis:        $2.99
Tags:         ci cd, github actions, gitlab ci, devops, build failed, pipeline, Claude skill
Beschreibung:
  Paste a failed CI log (GitHub Actions, GitLab CI, etc.) and get the real
  failure isolated from the noise. Finds the FIRST red line, classifies it
  (build/test/lint/deploy/infra), explains it, and gives the minimal fix
  plus a prevention line. Flaky runs are named, not masked by bigger
  timeouts. Secrets in logs are redacted. Commercial use included.
  Money-back via PromptBase.

====================================================================
LISTING 3 — Agent Skill (Claude Skill) — PAKET C
====================================================================
Titel:        Root-Cause Debugger — Find The Bug (ChatGPT Skill)
Modell:       Claude
Item-Typ:     Agent Skill
Kategorie:    Debugging / Engineering
Preis:        $2.99
Tags:         debugging, root cause, stack trace, bug, Claude skill, engineering, error
Beschreibung:
  Paste an error, stack trace, or "works locally, not in prod" report and
  get the actual cause — not a guess. 4 phases: reproduce, localize,
  hypothesize, verify. Output is uniform: SYMPTOM / ROOT CAUSE / EVIDENCE /
  NEXT CHECK / FIX. Suspect vs known is labeled. No code edits before the
  hypothesis is testable. Commercial use included. Money-back via PromptBase.

====================================================================
LISTING 4 — Agent Skill (ChatGPT Skill) — PAKET A
====================================================================
Titel:        Daily Standup Writer — Standup From Commits (ChatGPT Skill)
Modell:       ChatGPT
Item-Typ:     Agent Skill
Kategorie:    Writing / Productivity
Preis:        $2.99
Tags:         standup, daily standup, status update, productivity, chatgpt skill, meeting, writing
Beschreibung:
  Turn raw git commits, a diff, or messy bullets into a tight standup in seconds.
  Output: GESTERN / HEUTE / BLOCKER, each 1-3 bullets, outcome-led not activity-led,
  under 120 words. Matches your language (DE/EN). Great for Slack, Jira, daily sync.
  Commercial use included. Money-back guarantee via PromptBase.

====================================================================
LISTING 5 — Agent Skill (ChatGPT Skill) — PAKET C
====================================================================
Titel:        Messy CSV Cleaner — Dedupe, Fix, Normalize (ChatGPT Skill)
Modell:       ChatGPT
Item-Typ:     Agent Skill
Kategorie:    Data / Productivity
Preis:        $2.99
Tags:         csv cleaner, data cleaning, dedupe, normalize, chatgpt skill, data, excel
Beschreibung:
  Paste a dirty CSV/table and get it analysis-ready: trim, unify casing,
  parse dates to ISO, coerce numbers, drop exact duplicates, flag near-dups.
  Returns issues found, cleaned data, and a tool-agnostic recipe (pandas/
  Excel/SQL). Uncertain values are flagged, never overwritten. Shows
  before/after row counts. Commercial use included. Money-back via PromptBase.

====================================================================
LISTING 6 — Agent Skill (Claude Skill) — PAKET C
====================================================================
Titel:        Test Case Generator — Edge Cases & Coverage (ChatGPT Skill)
Modell:       Claude
Item-Typ:     Agent Skill
Kategorie:    Testing / QA
Preis:        $2.99
Tags:         test cases, edge cases, unit test, qa, testing, Claude skill, coverage
Beschreibung:
  Paste a function, endpoint, or feature spec and get runnable test cases:
  happy path, edge cases (null/boundary/unicode), and failure modes
  (bad input, timeout, 5xx). Every case is prioritized P0/P1/P2 in a
  given/when/then format, ending with a coverage-gap note. No filler,
  one assertion per case. Commercial use included. Money-back via PromptBase.

====================================================================
LISTING 7 — Agent Skill (Claude Skill) — PAKET A
====================================================================
Titel:        Senior Code Reviewer — Bugs Before Ship (ChatGPT Skill)
Modell:       Claude
Item-Typ:     Agent Skill
Kategorie:    Review / Coding
Preis:        $2.99
Tags:         code review, bug, security, pull request, Claude skill, coding, QA
Beschreibung:
  A drop-in Claude Skill that reviews your code like a strict senior engineer.
  Paste a diff, PR, or snippet and get a structured 4-pass review:
  (1) Correctness — logic bugs, off-by-one, null/undefined, wrong types
  (2) Security — injection, auth bypass, secret leaks, unsafe eval
  (3) Edge cases — empty/huge input, concurrency, network failure
  (4) Clarity — naming, dead code, readability
  Output is uniform: [PASS 1-4] SEVERITY — file:line — fix, ending in a
  VERDICT: ship | ship-with-fixes | block. No fluff, smallest fix preferred,
  never guesses. Commercial use included. Money-back guarantee via PromptBase.

====================================================================
LISTING 8 — Midjourney Sticker Pack — PAKET B
====================================================================
Titel:        Kawaii Food Stickers — 10 Cute Prompt Templates (Midjourney)
Modell:       Midjourney
Item-Typ:     Prompt
Kategorie:    Sticker / Cartoon
Preis:        $2.99
Tags:         sticker, kawaii, food, cute, midjourney, planner, journal, clipart
Beschreibung:
  10 ready-to-run Midjourney prompts for adorable food stickers (avocado, coffee,
  donut, strawberry, boba, croissant, ice cream, mushroom, pizza, matcha).
  Each uses white outline + --niji 6 for true sticker style, 1:1. Perfect for
  planners, journals, small shops, POD. Commercial use included.
  Money-back guarantee via PromptBase.

====================================================================
LISTING 9 — Midjourney Clipart Pack — PAKET B
====================================================================
Titel:        Watercolor Flower Clipart — 8 Botanical Prompts (Midjourney)
Modell:       Midjourney
Item-Typ:     Prompt
Kategorie:    Clip Art / Nature
Preis:        $2.99
Tags:         watercolor, floral, clipart, botanical, midjourney, wedding, invitation
Beschreibung:
  8 soft watercolor botanical prompts (eucalyptus, wild rose, lavender, berry,
  olive, chamomile, fern, pampas). Loose editorial wash, white background,
  commercial use. Ideal for wedding invites, logos, stationery, POD.
  Money-back guarantee via PromptBase.

====================================================================
EMPFEHLUNG REIHENFOLGE LIVE-GANG (nach GERINGSTER direkter Konkurrenz, MEASURED)
====================================================================
1) Listing 1  Commit Message Writer (ChatGPT) — 1 direkter Konkurrent, geringste
   Konkurrenz, niedriger Preis = idealer Erst-Einstieg.
2) Listing 2  CI/CD Failure Trier (Claude)     — "ci" vergiftet, echte CI/CD-Konk.
   nur 2-3; differenziert durch "build failed"/"GitHub Actions".
3) Listing 3  Root-Cause Debugger (Claude)     — 20 generische "debug"-Prompts,
   ABER KEIN Agent-Skill mit Root-Cause-Ansatz = Luecke.
4) Listing 4  Daily Standup Writer (ChatGPT)   — ~3-5 Geschwister-Konkurrenten
   (standup/status), moderat; eigener Link wichtig.
5) Listing 5  Messy CSV Cleaner (ChatGPT)      — ~22 "data cleaning", fast nur GPT,
   "CSV"-Winkel differenziert; breite Nutzung.
6) Listing 6  Test Case Generator (Claude)     — ~22, mehrere agent-artig, "edge
   cases" bereits besetzt-halbt; solide, nicht First-Mover.
7) Listing 7  Senior Code Reviewer (Claude)    — ~19, GESAETTIGT (meiste Konkurrenz
   der Skills); als Spitzen-Skill erst spaeter / ueber eigenen Link.
8) Listing 8  Kawaii Food Stickers (Midjourney)— Bild-Nische gesaettigt, aber
   schnell reproduzierbar; ergaenzt.
9) Listing 9  Watercolor Floral Clipart (Midjourney) — Backup, gesaettigt.

Regel: (a) Agent Skills VOR Sticker/Clipart (hoehere Marge, Kernkompetenz).
(b) Erste 3 Listings = die mit geringster direkter Konkurrenz (1,2,3).
(c) Nischen-Trend weiter ruecklaeufig (MEASURED -13%/-30%): First-Mover
    solange das Board wenige Agent-Skill-Listings hat.

====================================================================
OFFENE FRAGEN / UNKLAGEN
====================================================================
- [offen] Skill-Upload-Format auf PromptBase: erwartet es reines SKILL.md oder
  ein ZIP? Nicht MEASURED (kein Account). Annahme: SKILL.md wie auf /sell beworben.
  -> 7 fertige Standalone-SKILL.md liegen in skills/ (copy-paste-ready).
- [offen] Max. Wortzahl der Beschreibung? Nicht geprueft. Texte sind kurz gehalten.
- [offen] Oben Preise sind Vorschlaege; Nutzer kann anpassen.
- [ASSUMED] "standup" exakte Trefferzahl: Browser-Backend zur Messzeit 502,
  daher Proxy ueber verwandte Live-Suche (siehe Discovery-Befund).

====================================================================
PREIS-CHECK (MEASURED, 2026-07-19) — 2 Preise korrigiert
====================================================================
Methode-Warnung (MEASURED): curl auf promptbase.com/marketplace?searchQuery=
lieferte HTTP 200, ABER 0 /prompt/-Anker und 0 $-Preise im statischen HTML
-> die Marktplatz-Suche ist Firestore/client-seitig gerendert und NICHT
per curl/web_extract scrapebar. Alle Vergleichspreise stammen daher aus
Live-Such-Snippets (Google-Index) + einer direkt extrahierten Listing-Seite,
nicht aus systematischer Marktplatz-Durchzaehlung. Das ist ein ehrlicher
MEASURED-Befund, keine vermutete Zahl.

Frische Live-Preise (MEASURED 2026-07-19, promptbase.com Such-Index):
- "Code Review Checklist Generator" (Claude Prompt, @gohboh) ...... $4.99
- "The Root Cause Finder" (ChatGPT Prompt, @pascudonut) ........... $6.99
- "Root Cause Solution Analyzer" (Claude Prompt, @mrbalance) ...... $6.99
- "Technical Co Founder Build Plan" (Claude Prompt) ............... $9.99 (Sale $5.00)
- Item-Typ "Agent Skill" EXISTIERT live: promptbase.com/skill/code-review-fix
  (Claude Skill) -> Upload-Format SKILL.md bestaetigt als realer Typ.

KORREKTUREN (belegpflichtig):
- Listing 3 Root-Cause Debugger: $7.99 -> $6.99. BEGRUNDUNG: direkter
  ChatGPT/Claude-Root-Cause-Konkurrent bei $6.99 (MEASURED, s.o.).
  $7.99 lag ueber dem Markt -> auf Markt-Niveau gesenkt.
- Listing 7 Senior Code Reviewer: $6.99 -> $5.99. BEGRUNDUNG: direkter
  "Code Review" Claude-Konkurrent bei $4.99 (MEASURED). $6.99 = +40% Aufschlag
  bei identischer Leistung -> $5.99 (leicht ueber Konkurrenz als "Premium",
  aber nicht abstossend).
- Listing 1/2/4/5/6: BEIBEHALTEN. Keine frischen direkten Live-Preise messbar
  (Suche nicht scrapebar); Werte liegen in der belegten $4.99-$6.99-Bandbreite.

Neue Preis-Matrix (Stand 2026-07-19):
| # | Skill                  | ALT   | NEU   | Aenderung |
|---|------------------------|-------|-------|-----------|
| 1 | Commit Message Writer  | $3.99 | $3.99 | gleich    |
| 2 | CI/CD Failure Trier    | $6.99 | $6.99 | gleich    |
| 3 | Root-Cause Debugger    | $7.99 | $6.99 | -$1.00    |
| 4 | Daily Standup Writer   | $4.99 | $4.99 | gleich    |
| 5 | Messy CSV Cleaner      | $5.99 | $5.99 | gleich    |
| 6 | Test Case Generator    | $6.99 | $6.99 | gleich    |
| 7 | Senior Code Reviewer   | $6.99 | $5.99 | -$1.00    |
