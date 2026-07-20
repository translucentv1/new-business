# SPEC — Agent-Skills-Bundle über den eigenen Funnel verkaufen

**Datum:** 2026-07-20 · **Autor:** Hermes (autonomer Cron) · **ADR:** 0020

## Problem (aus Käufer-Sicht)
Die 7 fertig gebauten + QA-ten Agent-Skills (`products/promptbase-agent-skills/skills/`)
liegen als unverkauftes Nebenprodukt. Ihr vorgesehener Vertriebsweg (PromptBase-
Marktplatz) ist vollständig durch Hard Stops blockiert (Account, Stripe-Payout-
Verbindung, Publishing, Bild-Generierung = alles USER). Die Skills sind aber
reine `.md`-Dateien — digitale Produkte, die exakt dem bereits live geschalteten
Template-Funnel (GitHub Pages + Stripe Payment Links, 0 % Gebühr) entsprechen.

## Lösung
Das Bundle wird als weiteres Template-Produkt in den bestehenden Funnel
eingehängt — **ohne Code-Änderung**, weil `publish_site.py` jedes
`products/templates/<id>/` (spec.json + deliverable/) automatisch zu Landingpage
+ Download-Deliverable + Stripe-Link verdrahtet.

- `products/templates/agent-skills-bundle/spec.json` (title, price_eur, audience, sections)
- `products/templates/agent-skills-bundle/deliverable/` = 7 SKILL.md + ANLEITUNG.md
- Funnel baut daraus: `docs/t/agent-skills-bundle/index.html` (Kaufbutton) +
  `docs/dl/<hash>/agent-skills-bundle.html` (Download, nur post-payment via
  Stripe-Redirect) + Stripe-Link `tpl:agent-skills-bundle`.

## User Stories
- Als Dev möchte ich 7 sofort kopierbare Skills kaufen, die ein festes
  Ausgabe-Format liefern (Review, Commit, CI-Debug, Standup, CSV, Test, Root-Cause).
- Als Betreiber möchte ich ein weiteres Live-Produkt im Funnel haben, das den
  ersten Sale näher bringt — ohne neue Accounts/Infra.

## Implementation / Testing Decisions
- Keine Änderung an `scripts/` nötig (Template-Mechanik wird wiederverwendet).
- Preis: **6,99 €** (Bundle-Intro; bewusst unter der Summe der Einzel-Listings
  ~35 $). ASSUMED-Geschäftsentscheidung — in `spec.json` jederzeit änderbar;
  Link via `stripe_uploader.py` neu erzeugbar.
- Qualität: Skills sind QA-t (STATUS.md: 3 FIXED, 4 PASS, alle mit
  "No-preamble"-Regel). Keine Platzhalter (gescannt: 0 Treffer).
- Nach Build: `test_download_gate.py` + `test_pd_processor.py` müssen grün
  bleiben (kein Code-Change → unkritisch, trotzdem verifiziert).
- Danach: commit (master) + `publish_site.py` (gh-pages) + Live-Check per curl 200.

## Out of Scope
- PromptBase-Listing / Account / Payouts (Hard Stop, USER).
- Preview-Bilder / Cover-PNGs (nur für PromptBase nötig, hier nicht).
- Einzelverkauf der 7 Skills (vorerst nur Bundle).
