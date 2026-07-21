# GO-LIVE-PLAYBOOK — PromptBase Agent-Skills (fuer den Nutzer)

PRAEZISE, nummerierte Schritte. HARD-STOPS (Konto/Keys/Auszahlung/Veröffentlichung)
liegen beim NUTZER — Hermes hat nichts davon getan. Jeder Schritt sagt: was
klicken + welches Artefakt kopieren. Quellen: MEASURED (promptbase.com/sell,
promptbase.com/popular-models) bzw. ASSUMED (noch nicht im Account geprüft).

Arbeitsordner mit allen Artefakten (MEASURED 2026-07-21, korrigiert):
C:\\Users\\phili\\new-business\\products\\promptbase-agent-skills\\
  - LISTING-TEXTE.md              (9 copy-paste-ready Listings, scharf nach SEO)
  - skills\\*.md                    (7 fertige Standalone-SKILL.md, 1:1 Upload)
  - covers\\*.png                   (3 fertige Cover-PNGs, PIL gerendert, verifiziert)
  - GO-LIVE-PLAYBOOK.md            (dies hier)
  - PAKET-A / -B / -C             (Hintergrund + volle SKILL.md-Inhalte)

ACHTUNG: PromptBase cappt neue Sellers bei 2 PENDING Listings (MEASURED).
Heisst: erst 2 hochladen, abwarten bis review frei gibt (Stunden bis 1-2 Tage),
dann die restlichen 5. Liste 1+2 zuerst (geringste Konkurrenz).

================================================================================
SCHRITT 1 — PromptBase-Account anlegen
================================================================================
1.1  Browser: https://promptbase.com/login  → "Sign up" (E-Mail + Passwort)
     oder "Continue with Google".
1.2  Bestaetigungs-Mail oeffnen, Link klicken, Login abschliessen.
1.3  Oben rechts auf "Sell" klicken → Landest auf https://promptbase.com/sell
     (MEASURED: dort steht "Sell AI prompts or agent skills (SKILL.md files)").
ARTERAKT: Konto existiert, du bist auf der Sell-Seite.

================================================================================
SCHRITT 2 — Auszahlung verbinden (Stripe ODER Zoneless)
================================================================================
2.1  Auf /sell (oder Profil → Payouts) "Connect payout" / "Connect Stripe"
     klicken. (MEASURED: PromptBase bietet Stripe ODER Zoneless an.)
2.2  ENTSCHEIDUNG (Hinweis, keine Kontrolle durch Hermes):
     - Stripe:  fuer dich als Kleinunternehmer sauber, Auszahlung auf dein
       Bankkonto; Pflicht = echte Daten (KEINE Platzhalter DE123456789 /
       beispiel.com — siehe business-Hard-Stops).
     - Zoneless: alternative Plattform, falls du kein Stripe willst.
2.3  Stripe-OAuth durchklicken, Live-Mode (nicht Test), eigenes Bankkonto
     hinterlegen. KYC-Daten ehrlich ausfuellen.
ARTERAKT: Grüner Haken "Payouts connected" in den Seller-Settings.

================================================================================
SCHRITT 3 — ERSTE 3 LISTINGS einstellen (niedrigste Konkurrenz zuerst)
================================================================================
Empfohlene Reihenfolge (siehe LISTING-TEXTE.md, MEASURED-Konkurrenz):
  Listing 1 = Commit Message Writer (1 direkter Konkurrent)
  Listing 2 = CI/CD Failure Trier  (echte CI/CD-Konk. nur 2-3)
  Listing 3 = Root-Cause Debugger  (20 generische, KEINE als Agent-Skill)

Für JEDES der 3 Listings gleich ablaufen:

3.0  Auf /sell → "Create" / "New listing" → Item-Typ = "Agent Skill"
     (nicht "Prompt"). (ASSUMED: Item-Typ waehlbar; MEASURED war nur der
     Hinweistext auf /sell.)
3.1  TITEL: kopiere aus LISTING-TEXTE.md den genauen Titel inkl.
     "(Claude Skill)" / "(ChatGPT Skill)" — exakter Suchbegriff steht VORN.
3.2  MODELL: Claude bzw. ChatGPT (wie im Listing angegeben).
3.3  KATEGORIE: wie im Listing (Git/DevOps/Debugging).
3.4  PREIS: $2.99 (Sprint-Preis fuer alle 7 Skills, einheitlich - User-Entscheidung TB-28)
3.5  BESCHREIBUNG: kompletten Block aus LISTING-TEXTE.md kopieren
     (inkl. "Commercial use included. Money-back via PromptBase.").
3.6  TAGS: alle Tags aus LISTING-TEXTE.md 1:1 uebernehmen (Komma-getrennt).
     WICHTIG bei Listing 2: "ci cd" + "github actions" + "build failed"
     (NIEMALS nur "ci" — das wird von "Competitive Intelligence" ueberschwemmt).
3.7  SKILL-DATEI HOCHLADEN: die Datei aus skills\ kopieren/einhaengen:
     - Listing 1 → skills\commit-message-writer.md
     - Listing 2 → skills\ci-pipeline-trier.md
     - Listing 3 → skills\root-cause-debugger.md
     (Falls PromptBase ein ZIP will statt Einzel-SKILL.md: die eine .md in
     einen Ordner packen, zippen, hochladen. Inhalt identisch.)
3.8  PREVIEW-BILD: siehe SCHRITT 4 (Cover rendern, dann hier einhaengen).
3.9  "Publish" klicken. Wiederholen für Listing 2 und 3.

ARTERAKT: 3 Agent-Skill-Listings live, mit eigenem Verkaufslink.

================================================================================
SCHRITT 4 — Preview-Bilder (Cover je Listing) — 3 BEREITS VORHANDEN
================================================================================
MEASURED: 3 fertige Cover-PNGs (1000x1000, PIL-gerendert, verifiziert) liegen in:
C:\\Users\\phili\\new-business\\products\\promptbase-agent-skills\\covers\\
  - cover-commit-message-writer.png  (ChatGPT Skill, blau)
  - cover-ci-pipeline-trier.png       (Claude Skill, rot fix)
  - cover-root-cause-debugger.png     (Claude Skill, Lupe)

Einfach als Preview-Bild bei PromptBase hochladen. Fuer die restlichen 4 Skills
(Listing 4-7) musst du Cover selbst rendern (Canva/Slides/PIL) ODER die 3
vorhandenen mit anderem Titel-Namen nachbaun. PromptBase akzeptiert Listings
auch OHNE Cover, aber Cover steigern CTR deutlich.

================================================================================
SCHRITT 5 — Eigener Link (0%) vs Marketplace (20%)
================================================================================
MEASURED (/sell): 0% Gebühr über EIGENEN Link, 20% über den Marketplace.
Regel:
- EIGENER LINK (0%): immer wenn DU den Käufer bringst — also Post in
  WhatsApp-Gruppen, eigener Link in Bio, im neu-business-Funnel, in E-Mails.
  Den Link kopierst du von deiner Live-Listing-Seite
  (promptbase.com/prompt/<slug>) → "Copy share link" / Adresszeile.
- MARKETPLACE (20%): nur wenn Käufer DICH ueber die PromptBase-Suche finden.
  Den mußt du nicht extra bedienen — er greift automatisch, wenn jemand
  ueber die Marketplace-Suche landet.
STRATEGIE: Erste Verkaeufe ueber EIGENEN LINK (0% Margenverlust) treiben;
Marketplace-Sichtbarkeit kommt als Bonus, solange du Titel/Keywords scharf
hast (siehe LISTING-TEXTE.md Discovery-Befund).

================================================================================
SCHRITT 6 — Rest-Katalog ausrollen (nach ersten 3)
================================================================================
Wie Schritt 3, aber fuer Listing 4-9 in der empfohlenen Reihenfolge:
  4 Daily Standup Writer  → skills\daily-standup-writer.md
  5 Messy CSV Cleaner      → skills\messy-data-cleaner.md
  6 Test Case Generator    → skills\test-case-generator.md
  7 Senior Code Reviewer   → skills\clean-code-reviewer.md
  8 Kawaii Food Stickers   → nur Prompt-Text aus LISTING-TEXTE.md (Midjourney)
  9 Watercolor Clipart     → nur Prompt-Text aus LISTING-TEXTE.md (Midjourney)
HINWEIS: 8/9 sind Midjourney-PROMPTS (Item-Typ "Prompt"), keine SKILL.md.
Cover dafuer: gerenderte Sticker/Blumen-Beispielbilder (aus den MJ-Prompts).

================================================================================
CHECKLISTE (abhaken)
================================================================================
[ ] Schritt 1: PromptBase-Account
[ ] Schritt 2: Stripe/Zoneless verbunden
[ ] Schritt 3: Listing 1,2,3 live (Titel/Tag/Preis/SKILL.md aus Artefakten)
[ ] Schritt 4: 3 Preview-Bilder gerendert + hochgeladen
[ ] Schritt 5: eigener Verkaufslink kopiert, in eigenen Kanälen geteilt
[ ] Schritt 6: Listing 4-9 ausgerollt

BELEGPFLICHT: Alle MEASURED-Angaben stammen aus Live-Prüfung (promptbase.com/
search, /sell, /popular-models, 2026-07-19). Schritte, die einen Account/
Upload erfordern, sind ASSUMED bis du sie im Konto verifizierst.
