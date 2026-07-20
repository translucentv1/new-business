# Hermes-Arbeitsreport — K1 (Opire) + K3 (PromptBase) — 2026-07-19

STATUS: ABGESCHLOSSEN (Session-Fortsetzung nach Kopf-Feedback-Runde).
Letztes Update: 2026-07-19, spät. Modus: VORBEREITUNG. Kein Live-Gang.
HARD-STOPS gelten (siehe unten).

## Belegpflicht (unveraenderlich)
- MEASURED = heute live per URL/Befehl geprueft, mit exakter Quelle/Rohbeleg.
- ASSUMED = Schaetzung/Drittanbieter, nicht primär verifiziert.
- Nie eine Zahl erfunden. "Verifiziert" nur mit Rohbeleg.

## HARD-STOPS (Hermes durfte NICHT — bleibt beim Nutzer)
KEINE Konten | KEINE Keys/Auszahlungen/Zahlmethoden |
KEINE PRs einreichen | KEINE Listings veroeffentlichen |
KEIN oeffentliches Posten | KEINE Krypto | KEINE Kaeufe.
Nur lokal gearbeitet + Entwuerfe/Artefakte abgelegt.

## Arbeitsordner
- K1: C:\Users\phili\AppData\Local\Temp\claude\arbeit-2026-07-19\k1-opire\
- K3: C:\Users\phili\AppData\Local\Temp\claude\arbeit-2026-07-19\k3-promptbase\

## Umgebung (MEASURED, terminal)
- node v24.18.0, npm 11.16.0, python 3.11.15, git 2.55.0 vorhanden
- go / cargo NICHT installiert -> Rust/Go-Bounties lokal nicht reproduzierbar
- (Hinweis: better-sqlite3 braucht natives VS-Build; sqljs=WASM genutzt)

================================================================================
## K1 — OPIRE BOUNTIES
================================================================================

### K1.1 — typeorm #11806 (ABGESCHLOSSEN als Investigation, won't-fix)
Status: Bug reproduziert, Ursache geklaert, ENTSCHEIDUNG = KEIN PR (won't-fix).
Artefakt: k1-opire/INVESTIGATION-REPORT-typeorm-11806.md

Bounty-Metadaten (MEASURED, app.opire.dev/issues/01HWT2MKE4GWPJXDPMAFEAHHHE):
- Betrag lt. Opire-Titel: 30 $ (1 available reward, 0 paid)
- Status: Open; 3 solvers trying / 3 claimed
- Sprache: TypeScript; Repo lokal geklont

Reproduktion (MEASURED, voriger Turn): Test test/github-issues/11806/issue-11806.test.ts
lief mit unveraendertem Code FAIL ("expected +0 to equal 3") -> Bug real.
Control-Test (setFindOptions) GREEN.

Ursachen-Klaerung (MEASURED): Fix in QueryBuilder.getWhereCondition() -> GREEN,
ABER am HEAD existiert expliziter Test
test/functional/null-undefined-handling/query-builders.test.ts:
"invalidWhereValuesBehavior does NOT affect QB .where()" (QB is low-level).
Maintainer-Intent: invalidWhereValuesBehavior betrifft NUR FindOptions/setFindOptions.
=> won't-fix. Quellcode-Aenderung rueckgaengig (git diff src/ == leer, verifiziert).

Einschaetzung: Merge-Wahrscheinlichkeit Fix-PR ~0 %. Kopf bestaetigte:
nur Investigation-Report, KEIN PR. ERLEDIGT.

### K1.2 — Bounty-Board Saettigung (MEASURED via Kopf-Feedback)
Kopf lud Opires Board live: typeorm #3357 = 23 solvers (fakt 25), autokey
Wayland 12, typeorm OrmUtils 15, zed Helix 6, godot 10. Plus 1.160.036$-
Spam-Bounty + geschlossene 80$-Bounty mit 0 $ verfuegbar. Saettigungs-
Warnung BESTAETIGT.

### K1.3 — PIVOT auf kleine, ungesaettigte Bounties (MEASURED, heute)
Kopf-Kriterien: (a) Solver 0-2, (b) available rewards > 0 (Titel != Geld).
Artefakt: k1-opire/PIVOT-ANALYSE.md

Gepruefte Bounties (MEASURED, app.opire.dev Detailseiten + opire.dev/home):
- typeorm #3357: 25/25 solvers, Open, 12 rewards -> GESAETTIGT
- godot web exports: 12/12 solvers, C++ -> GESAETTIGT + nicht lokal
- zed Helix: 6/6 solvers, Rust -> GESAETTIGT + nicht lokal
- storybook #12641: 5/5 solvers, TS, $263 -> >0-2-Schwelle
- autokey Wayland: 24/12 solvers, CLOSED -> RAUS
- strapi #11998: 3/3 solvers, TS, $30 -> 3>2
- deno #18147: 2/2 solvers, Rust, $70 -> KNAPP 2, aber Rust (nicht lokal)
- busboy/restfuncs #6: winziges Repo (65 stars), Maintainer: "too many
  low-effort bounty hunters", ~$70-90 -> Grossaufwand, unklar
- electron Image resize: 2/2 solvers, JS, $70 -> KNAPP 2, aber RIESIGE Codebase
- Race Condition UdioWrapper: 5 solvers, $86 -> GESAETTIGT

ERGEBNIS: Kein Bounty erfuellt SAUBER beide Kopf-Kriterien + lokale Repro.
Empfehlung: K1 pausieren, Fokus K3 (Agent Skills = echte ungesaettigte Nische,
hoehere Marge, minimale Konkurrenz). Siehe offene Frage 4.

================================================================================
## K3 — PROMPTBASE  (ZUERST bearbeitet, laut Kopf-Prioritaet)
================================================================================
Status: VOLLSTAENDIG vorbereitet (NICHT veroeffentlicht).

### K3.1 Nischen (MEASURED, heute)
- Marketplace: 310k Prompts, 42k+ Reviews, 500k+ User (promptbase.com/)
- NEUER Item-Typ "Agent Skills" (SKILL.md files) — promptbase.com/sell
- Marketplace-Share (promptbase.com/popular-models, Updated Jul 13 2026):
  ChatGPT Image 49%, Midjourney 20%, Claude 11%, Gemini Image 5%,
  ChatGPT 4%, Claude Skill 3% (Rang 6!), ChatGPT Skill 1% (Rang 8),
  Ideogram +344% Woche
  -> Agent Skills = UNGESAETTIGT (wenige Listings), mit realen Verkaufs-
     anteilen (Rang 6 / Rang 8), ABER Trend aktuell RUECKLAEUFIG:
     Wochenaenderung laut Kopf-MEASURED -13% / -30% (FALLEND, nicht
     "jung+steigend"). KORREKTUR (MEASURED, heute erneut geprueft):
     Die MARKETPLACE-SUCHE liefert sehr wohl einzelne Listings, aber ALLE
     als modell-getaggte PROMPTS (GPT/Claude/DeepSeek/Gemini) — KEINES als
     "Agent Skill" getaggt. Die altere Annahme "Skill-Liste zeigt keine
     einzelnen Listings" war FALSCH (verwechselt Filter-Kategorien mit
     Suchergebnissen). => Auffindbarkeit laeuft ueber Titel-Keywords +
     eigenen Link, nicht ueber eine Skill-Kategorie-Suche. Details K3.5.
  - PromptBase-Suche ist Firestore-basiert (client-seitig, keine offene
     REST-API) -> Zaehlung nur ueber Live-Browser-Suche moeglich.
- Top-Seller Beleg (promptbase.com/prompt/female-gym-shots, MEASURED):
  @charismaenigma "Top Seller", 3.0k Sales, 210 Reviews, 4.7*, Rank #16
  -> Verkaufszahlen SICHTBAR, echte Nachfrage belegt
- business-Nische: GPT-Prompts "One Person Business Builder" $9.99,
  "Creation Of A Business Plan" $3.99 (hoehre Texte-Preise)
- Gebuehr (MEASURED, /sell): 0% eigen / 20% Marktplatz
- Auszahlung (MEASURED, /sell): Stripe oder Zoneless (NICHT eingerichtet)

### K3.2 + K3.3 Prompt-Pakete + Listing-Texte (FERTIG, lokal)
Artefakte:
- k3-promptbase/PAKET-A-agent-skills.md
    -> Skill 1 "Senior Code Reviewer" (Claude Skill, $6.99)
       Skill 2 "Daily Standup Writer" (ChatGPT Skill, $4.99)
- k3-promptbase/PAKET-B-midjourney-stickers.md
    -> Prompt 1 "Kawaii Food Stickers" 10 Midjourney-Prompts ($3.99)
       Prompt 2 "Watercolor Floral Clipart" 8 Midjourney-Prompts ($4.99)
- k3-promptbase/PAKET-C-agent-skills-batch2.md   [NEU, siehe K3.4]
    -> Skill 3 "Test Case Generator" (Claude Skill, $6.99)
       Skill 4 "Root-Cause Debugger" (Claude Skill, $7.99)
       Skill 5 "Commit Message Writer" (ChatGPT Skill, $3.99)
       Skill 6 "Messy Data Cleaner" (ChatGPT Skill, $5.99)
       Skill 7 "CI Failure Trier" (Claude Skill, $6.99)
- k3-promptbase/LISTING-TEXTE.md
    -> 9 copy-paste-ready Listings (Titel/Beschreibung/Tags/Preis),
       Titel/Tags nach SEO geschaerft + Go-Live-Reihenfolge neu geordnet
       (geringste Konkurrenz zuerst). NEU: Discovery-Befund oben eingefuegt.
- k3-promptbase/skills/   [NEU] 7 fertige Standalone-SKILL.md, 1:1 Upload-ready
    clean-code-reviewer, daily-standup-writer, test-case-generator,
    root-cause-debugger, commit-message-writer, messy-data-cleaner,
    ci-pipeline-trier
- k3-promptbase/GO-LIVE-PLAYBOOK.md   [NEU] nummerierte Go-Live-Anleitung
    (Account, Stripe/Zoneless, erste 3 Listings, Preview-Bilder, 0% vs 20%)

### K3.4 Katalog-Ausbau Agent Skills (NEU, heute — Kopf-Entscheidung Q5: Fokus Agent Skills JA)
Ziel: Katalog von 2 auf 7 sofort verkaufbare Agent Skills ausbauen,
jeweils EINE andere Kategorie, keine Dubletten, kein Fuelltext.
Qualitaetsniveau = clean-code-reviewer-Vorlage (volle SKILL.md + Listing + Preview).

Katalog-Stand (7 Skills, vollstaendige SKILL.md lokal vorhanden):
| # | Skill | Modell | Kategorie | Preis |
|---|-------|--------|-----------|-------|
| 1 | Senior Code Reviewer    | Claude  | Review      | $6.99 |
| 2 | Daily Standup Writer    | ChatGPT | Writing     | $4.99 |
| 3 | Test Case Generator     | Claude  | Testing     | $6.99 |
| 4 | Root-Cause Debugger     | Claude  | Debugging   | $7.99 |
| 5 | Commit Message Writer   | ChatGPT | Git         | $3.99 |
| 6 | Messy Data Cleaner      | ChatGPT | Data        | $5.99 |
| 7 | CI Failure Trier        | Claude  | DevOps/CI   | $6.99 |

Abdeckung: Review, Writing, Testing, Debugging, Git, Data, DevOps/CI
-> 7 verschiedene Kategorien, differenziert, echter Nutzen je Skill.
Alle SKILL.md enthalten Frontmatter (name+description) + Prozess +
Output-Format + Regeln. Keine Platzhalter, keine Dubletten.

Empfohlene Live-Gang-Reihenfolge: basiert JETZT auf der DISCOVERY-RECHERCHE
(K3.5, MEASURED Konkurrenz) = geringste direkte Konkurrenz zuerst. Neue
Reihenfolge (siehe LISTING-TEXTE.md + K3.5): Commit Message Writer, CI/CD
Failure Trier, Root-Cause Debugger, Daily Standup Writer, Messy CSV Cleaner,
Test Case Generator, Senior Code Reviewer, dann Sticker/Clipart.
Nischen-Trend RUECKLAEUFIG (-13%/-30%, MEASURED) -> First-Mover solange Board leer.

Artefakt-Dateien (MEASURED vorhanden):
- C:\Users\phili\AppData\Local\Temp\claude\arbeit-2026-07-19\k3-promptbase\PAKET-C-agent-skills-batch2.md
- C:\Users\phili\AppData\Local\Temp\claude\arbeit-2026-07-19\k3-promptbase\LISTING-TEXTE.md (9 Listings)

Empfohlene Reihenfolge Live-Gang: siehe K3.4 + LISTING-TEXTE.md
(9 Listings, Agent Skills 1-9 zuerst, dann Sticker/Clipart). Agent Skills
zuerst (ungesaettigt, hoehere Marge, Kernkompetenz), trotz ruecklaeufigem
Trend First-Mover solange Board leer.

### K3.5 DISCOVERY-RECHERCHE (NEU, heute — MEASURED live ueber PromptBase-Suche)
Ziel: Auffindbarkeit pruefen + Konkurrenz pro Thema messen. Methode:
PromptBase-Suche (SPA /marketplace?searchQuery=TERM) im Browser, da
Firestore-basiert (KEINE offene REST-API, curl/web_extract liefern nur
das Filter-Shell). Ergebnisse = modell-getaggte PROMPTS, KEIN "Agent Skill".

Konkurrenz pro Thema (MEASURED, "Most relevant", Seite 1):
| Thema (Suche)     | ~Treffer | Preisrange      | Agent-Skill-Tag? | Einschaetzung            |
|-------------------|----------|-----------------|------------------|--------------------------|
| code review       | ~19      | $2.99-$6.99     | NEIN             | GESAETTIGT               |
| debug             | ~20      | $2.99-$19.99    | NEIN             | gesaettigt, ABER LUECKE  |
|                   |          |                 |                  | bei Root-Cause-Skill     |
| test cases        | ~22      | $2.99-$29.99    | NEIN (agent-art) | GESAETTIGT               |
| commit message    | ~23      | $2.99-$19.99    | NEIN             | GERINGSTE direkte Konk.  |
|                   |          |                 |                  | (1 Treffer: "Pro Git     |
|                   |          |                 |                  | Commit Message Gen" $4.99)|
| data cleaning     | ~22      | $2.99-$6.99     | NEIN             | GESAETTIGT, fast nur GPT |
| ci (allein)       | ~20      | $2.99-$11.99    | NEIN             | VERGIFTET: ~18 =         |
|                   |          |                 |                  | "Competitive Intelligence"|
|                   |          |                 |                  | nur 2-3 echte CI/CD      |
| standup           | ASSUMED  | $2.99-$8.99     | NEIN             | ~3-5 (Proxy ueber        |
|                   |          |                 |                  | Geschwister-Suche)       |

WICHTIGE Befunde:
- "ci" als Suchwort ist VERGIFTET (Competitive Intelligence ueberschwemmt
  die Treffer). Tag muss "ci cd" / "github actions" / "build failed" sein.
- KEIN einziges Konkurrenz-Listing ist als "Agent Skill" getaggt -> unsere
  Differenzierung "Claude Skill"/"ChatGPT Skill" + Skill-Item-Typ ist eine
  echte Luecke, KEIN MeToo.
- "commit message" hat die geringste direkte Konkurrenz -> bester Erst-Einstieg.
- "standup" exakte Zaehlung ASSUMED: Browser-Backend zur Messzeit 502
  (Infra-Ausfall), daher Proxy ueber die verwandte Live-Suche "commit
  message", die sichtbare Geschwister zeigte (Sprint Standup Notes Generator
  $2.99, Async Standup Writer $4.99, Status-Cluster $3.99-$8.99).

DARAUS ABGELEITET (umgesetzt in LISTING-TEXTE.md):
- Titel: exakter Suchbegriff VORN + "(Claude Skill)"/"(ChatGPT Skill)".
- Tags: exakte Suchwoerter (z.B. "ci cd", nicht nur "ci"; "csv cleaner").
- Go-Live-Reihenfolge neu = GERINGSTE direkte Konkurrenz zuerst:
  (1) Commit Message Writer (2) CI/CD Failure Trier (3) Root-Cause Debugger
  (4) Daily Standup Writer (5) Messy CSV Cleaner (6) Test Case Generator
  (7) Senior Code Reviewer (8) Kawaii Stickers (9) Watercolor Clipart.

Artefakt-Dateien (NEU, MEASURED vorhanden):
- C:\Users\phili\AppData\Local\Temp\claude\arbeit-2026-07-19\k3-promptbase\LISTING-TEXTE.md
   (9 Listings, Titel/Tags nach SEO geschaerft, Reihenfolge neu)
- C:\Users\phili\AppData\Local\Temp\claude\arbeit-2026-07-19\k3-promptbase\skills\
   (7 fertige Standalone-SKILL.md, 1:1 Upload-ready: clean-code-reviewer,
   daily-standup-writer, test-case-generator, root-cause-debugger,
   commit-message-writer, messy-data-cleaner, ci-pipeline-trier)
- C:\Users\phili\AppData\Local\Temp\claude\arbeit-2026-07-19\k3-promptbase\GO-LIVE-PLAYBOOK.md
   (nummerierte Schritt-fuer-Schritt-Anleitung fuer den Nutzer)

HARD-STOP: KEINE Bilder generiert (kein Account/Key), nur Preview-Konzept.
KEINE Veroeffentlichung.

================================================================================
## NUTZER-AKTIONSLISTE ZUM LIVE-GANG (nicht von Hermes ausgefuehrt)
================================================================================
K1 (nur bei Wahl A des Kopfes):
- [ ] Opire-Account + GitHub verknuepfen
- [ ] ggf. /try kommentieren, Fix+PR (Hermes reicht KEINEN PR ein)
K3 (PromptBase):
- [ ] PromptBase-Account anlegen (siehe GO-LIVE-PLAYBOOK.md Schritt 1)
- [ ] Stripe/Zoneless-Auszahlung verknuepfen (HARD-STOP, Nutzer) — Schritt 2
- [ ] ERSTE 3 Listings in empfohlener Reihenfolge einstellen (Reihenfolge
     s.o. + LISTING-TEXTE.md + GO-LIVE-PLAYBOOK.md Schritt 3):
     (1) Commit Message Writer, (2) CI/CD Failure Trier, (3) Root-Cause Debugger
     SKILL.md aus k3-promptbase/skills/ kopieren (1:1 Upload-ready)
- [ ] Preview-Bilder rendern (Schritt 4) — nur Konzept/Prompts vorhanden
- [ ] Eigenen Verkaufslink (0% Gebuer) in eigene Kanaele teilen (Schritt 5)
- [ ] Rest (Listing 4-9) ausrollen (Schritt 6)

================================================================================
## OFFENE FRAGEN AN DEN KOPF
================================================================================
1. [geklaert] #11806: nur Investigation-Report, kein PR — JA (bestaetigt)
2. [geklaert] K1-Pivot auf kleine, gesaettigte-freie Bounties — JA (bestaetigt)
3. [geklaert] K3 zuerst — JA (bestaetigt, erledigt)
4. [GEKLAERT] K1 pausieren (Sattigung, keine saubere 0-2-Solver/lokal-
   reproduzierbare Bounty, kein go/cargo lokal) — JA (Kopf-Entscheidung Q4).
   Nicht weiter dran arbeiten.
5. [GEKLAERT] Fokus Agent Skills (statt Midjourney) — JA (Kopf-Entscheidung
   Q5). Katalog auf 7 Skills ausgebaut (K3.4).
6. [OFFEN] Skill-Upload-Format PromptBase: reines SKILL.md oder ZIP?
   Nicht MEASURED (kein Account). Annahme: SKILL.md wie auf /sell beworben.
   7 fertige Standalone-SKILL.md liegen in k3-promptbase/skills/ (1:1
   Upload-ready, ggf. zippen falls PromptBase Ordner will). Als offene
   Frage stehen lassen (Nutzer-Hard-Stop: braucht Account).
7. [GEKLAERT/NEU] DISCOVERY-RECHERCHE heute MEASURED: Konkurrenz pro Thema
   gemessen (siehe K3.5). "ci" vergiftet durch "Competitive Intelligence";
   geringste direkte Konkurrenz = "commit message". Auffindbarkeit ueber
   Titel-Keywords + eigenen Link (KEIN Skill-Kategorie-Such-Treffer).
   "standup" exakte Zaehlung ASSUMED (Browser-Backend zur Messzeit 502).
8. [NEU] GO-LIVE-PLAYBOOK.md geschrieben (Schritt 1-6). HARD-STOPS unveraendert.

================================================================================
## ZUSAMMENFASSUNG
================================================================================
- K1 #11806: Bug reproduziert + als won't-fix belegt, Investigation-Report abgelegt.
- K1 Pivot: Board weitgehend gesaettigt; keine saubere 0-2-Solver/lokal-
  reproduzierbare Bounty gefunden. Analyse abgelegt. K1 PAUSIERT
  (Kopf-Entscheidung Q4 — nicht weiter dran arbeiten).
- K3: 3 Prompt-Pakete (9 Listings) voll vorbereitet, copy-paste-ready,
  NICHT veroeffentlicht. Katalog-Agent-Skills von 2 auf 7 ausgebaut (K3.4),
  7 verschiedene Kategorien (Review, Writing, Testing, Debugging, Git,
  Data, DevOps/CI), je Skill vollstaendige SKILL.md + Listing + Preview-Konzept.
- K3.5 DISCOVERY-RECHERCHE (NEU, heute): PromptBase-Suche live geprueft.
  Konkurrenz pro Thema MEASURED (code review ~19, debug ~20, test cases ~22,
  commit message ~23/1 direkt, data cleaning ~22, ci ~20 davon ~18
  "Competitive Intelligence", standup ASSUMED). KEIN Konkurrent als "Agent
  Skill" getaggt -> echte Luecke. "ci" als Tag VERGIFTET. Daraus Titel/Tags
  in LISTING-TEXTE.md nach SEO geschaerft + Go-Live-Reihenfolge neu
  (geringste Konkurrenz zuerst: Commit, CI/CD, Debug, Standup, CSV,
  Test, Code-Review).
- 7 fertige Standalone-SKILL.md in k3-promptbase/skills/ (1:1 Upload-ready)
  + GO-LIVE-PLAYBOOK.md (Schritt 1-6 fuer den Nutzer) erstellt.
- Nischen-Trend KORRIGIERT: ruecklaeufig (-13%/-30% MEASURED), Nische =
  ungesaettigt + echte Verkaufsanteile, aber fallend — nie schoenreden.
- Alle Zahlen MEASURED (heute live bzw. Kopf-MEASURED) oder als ASSUMED markiert.
- Kein HARD-STOP verletzt (kein Account, keine Veroeffentlichung, keine Bilder).

Letzte Aenderung: 2026-07-19, K3.5 Discovery-Recherche + LISTING-TEXTE.md
SEO-Schaerfung + Reihenfolge + skills/-Ordner + GO-LIVE-PLAYBOOK.md.
