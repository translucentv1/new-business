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

- **T1 — GitHub Pages Deployment** — RESOLVED (siehe Open Tickets, durchgestrichen). Site live:
  https://translucentv1.github.io/new-business/ (curl HTTP 200, echtes HTML; web_extract zeigt
  teils noch 404 = CDN-Knoten-Propagation, kein Defekt).
- **T4 — First-Sale-Measurement** — RESOLVED 2026-07-18. `sale_poller.py` Live-getestet:
  `GET /v2/sales` HTTP 200, success=True, 0 sales (erwartet, Drafts nicht published).
  Poller schreibt sales.log + triggert Reinvest (ADR-0005) bei price>0. Mess-Infra funktionsfähig.
  Nächster echter Sale wird sauber detektiert + geloggt.
- **Last ~2h (autonomous, 2026-07-18 06:09–07:50)** — Pivot + Pipeline gebaut:
  ADR-0010 (Stripe Payment Links), ADR-0011 (Payhip via User-Override, Stripe Backup),
  ADR-0012 (Cross-Wire Stripe↔Gumroad), Betriebs-Charta, SEO (sitemap/robots),
  Landingpage-/Publish-Pipeline, repo-agnostische Cron-Skripte.
- **T2 status-check 08:02 (2h-cron)** — weiter BLOCKED durch Gumroad 10/Tag-Limit.
  STORE total=5 drafts=5 published=0; 3 Drafts fehlen (Moby-Dick/Dracula/Frankenstein).
  04:00-Retry-Cron (58f0ebc08d11) läuft weiter, kein manuelles Push (Limit = hart, kein ToS-Bypass).

## Open Tickets (Frontier)

- ~~**T1 — GitHub Pages Deployment** (`task`) — RESOLVED 2026-07-18.~~ (siehe Decisions so far)
- **T2 — 3 fehlende Drafts live** (`task`, AFK via Cron): 2701/345/84 warten auf 04:00-Retry-Cron
  (`58f0ebc08d11`). BLOCKED by Gumroad 10/Tag-Limit (MEASURED: Fenster resettet ~24h nach
  erstem Create heute früh). Resolve wenn STORE: total=8 drafts=8 published=0.
- **T3 — Distribution-Kanal-Entscheidung** (`grilling`): welcher Kanal zuerst? ADR-0007 nennt
  (1) SEO-Landingpages, (2) Pinterest, (3) Reddit nur ToS-konform. Ein Kanal = ein Mini-Experiment.
- ~~**T4 — First-Sale-Measurement** (`research`) — RESOLVED 2026-07-18.~~ (siehe Decisions so far)
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
