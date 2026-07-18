# WAYFINDER MAP — new-business: Live-Gang + Traffic + erster Sale

**Label:** `wayfinder:map`
**Charted:** 2026-07-18 (autonomous, user grant: alle hard stops aufgehoben)
**Tracker:** local-markdown (kein issue-tracker installiert; Map = diese Datei, Tickets = `docs/wayfinder/<slug>.md`)
**Status:** charting (noch keine Tickets resolved)

## Destination

Von "8 Drafts + Landingpages liegen lokal/teilweise live" zu einem **messbaren ersten Geschäftsbetrieb**:
alle 8 Produkte als Drafts live auf philippbehnisch.gumroad.com, `docs/site/` öffentlich erreichbar
(GitHub Pages), und ein **erster echter Sale (price>0)**, der die ADR-0005-Reinvest-Logik triggert.
Dahinter: Distribution-Kanäle (SEO / Pinterest / Reddit) als einzelne MEASURED Mini-Experimente.

## Notes

- Skill-Loop: `autonomous-business-design` (grill→spec→ticket→implement) für jede Entscheidung.
- Evidence: MEASURED vs ASSUMED zwingend. Keine erfundenen Zahlen (Besucher, Sales, Impressions).
- Gumroad Free-Tier: **10 Produkte/Tag** hartes Limit (MEASURED 2026-07-18) → 3 Drafts warten auf
  täglichen Retry-Cron (04:00, job `58f0ebc08d11`). DRAFTS only, nie auto-publish.
- Gewerbe angemeldet (user) → legal gap CLOSED. Kein spend/account/ToS-umgehung.
- Verifikation: nach jedem Code-Edit frischer Test-Lauf + ad-hoc temp-verify.

## Decisions so far

<!-- geschlossene Tickets kommen hierhin, eine Zeile + Link -->

## Open Tickets (Frontier)

- **T1 — GitHub Pages Deployment** (`task`): `docs/site/` zu GitHub Pages publizieren, damit
  Landingpages öffentlich erreichbar + crawlbar sind. Blocked by: Repo muss zu GitHub gepusht sein
  (remote fehlt aktuell — MEASURED: `git remote -v` leer in new-business).
- **T2 — 3 fehlende Drafts live** (`task`, AFK via Cron): 2701/345/84 warten auf 04:00-Retry.
  Resolve wenn STORE: total=8 drafts=8 published=0.
- **T3 — Distribution-Kanal-Entscheidung** (`grilling`): welcher Kanal zuerst? ADR-0007 nennt
  (1) SEO-Landingpages, (2) Pinterest, (3) Reddit nur ToS-konform. Ein Kanal = ein Mini-Experiment.
- **T4 — First-Sale-Measurement** (`research`): wie wird ein echter Sale sauber detektiert/poliert
  und ADR-0005-Reinvest getriggert? Sale-Poller existiert (`sale_poller.py`) — braucht Live-Test.
- **T5 — Publish-Strategie** (`grilling`): wann/wie Drafts→published? Discover braucht $100 Sales
  + Risk-Review → Publish allein bringt 0 Traffic. Bewusster separater Schritt.

## Not yet specified (fog)

- Pinterest-Setup-Details (Business-Account? API oder manuell? ToS für PD-Links?)
- Reddit-Subauswahl + Self-Promo-ToS (viele Subs verbieten Promo)
- Reinvest-Größe/Ablauf (ADR-0005 sagt "erste 100% belegter Gewinn → scraper/LLM") — konkrete Schwellen
- Rechtliche Feinheiten nach erstem Sale (Kleinunternehmerregelung melden, USt frei bis 25k/100k)

## Out of scope

- Paid Ads / Geld ausgeben für Traffic (widerspricht free-to-build + aktueller Reinvest-Logik).
- Account-Upgrade zu Gumroad-Pro nur fürs Limit (ToS/legal risk, nicht nötig bei 8 Produkten).
- Multi-Account / ToS-Umgehung des 10/Tag-Limits.
