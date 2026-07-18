# WAYFINDER MAP — new-business: Live-Gang + Traffic + erster Sale

**Label:** `wayfinder:map`
**Charted:** 2026-07-18 (autonomous, user grant: alle hard stops aufgehoben)
**Tracker:** local-markdown (kein issue-tracker installiert; Map = diese Datei, Tickets = `docs/wayfinder/<slug>.md`)
**Status:** charting (T1/T3/T4 resolved; T2 blocked; T5 offen; ADR-0018 Produkt-Pivot aktiv = neue Frontier)

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
- **Last ~2h (autonomous, 2026-07-18 06:09–10:00)** — Pivot + Pipeline gebaut + Sale-Rail LIVE:
  ADR-0010 (Stripe Payment Links), ADR-0011 (Payhip via User-Override, Stripe Backup),
  ADR-0012 (Cross-Wire Stripe↔Gumroad), Betriebs-Charta, SEO (sitemap/robots),
  Landingpage-/Publish-Pipeline, repo-agnostische Cron-Skripte.
  **08:00–10:00 (2h-cron-Fenster):** 8 live Stripe Payment Links erstellt + Site published
  (MEASURED: Produktseiten haben https://buy.stripe.com/... Buttons, "Jetzt kaufen");
  Download-Gate ADR-0013 + Spec TB-8/9/10; SEO/Pivot-Research TB-11/12; stripe_links.json gitignored.
- **T2 status-check 10:00 (2h-cron)** — weiter BLOCKED durch Gumroad 10/Tag-Limit.
  STORE total=5 drafts=5 published=0; 3 Drafts fehlen (Moby-Dick/Dracula/Frankenstein).
  04:00-Retry-Cron (58f0ebc08d11) läuft weiter, kein manueller Push (Limit = hart, kein ToS-Bypass).
  Nächster echter Sale läuft jetzt über Stripe-Links (nicht Gumroad-Publish) → T3/T5-Fokus.
- **Last ~2h (autonomous, 2026-07-18 10:00–12:00)** — 2 neue PD-Bücher live (Stripe-Rail):
  TB-14 "A Tale of Two Cities" (Gutenberg 98) + ADR-0014 (create_link-Redirect-Fix auf Deliverable);
  TB-15 "Jane Eyre" (Gutenberg 1260) + ADR-0015. Jeweils Preview-Landingpage, Deliverable (Download-Gate),
  Stripe-Kauf-Link. Pipeline jetzt 10 Bücher (8 + 2 neu), alle via Stripe verkaufbar.
  **T2 status-check 12:00 (2h-cron)** — STORE unverändert total=5 drafts=5 published=0;
  jetzt 5 Drafts fehlen (Moby-Dick/Dracula/Frankenstein + neu: A Tale of Two Cities, Jane Eyre),
  weiter BLOCKED durch Gumroad 10/Tag-Limit (04:00-Retry-Cron). Pages HTTP 200. 0 Sales (sales.log fehlt).
- **2h-cron status-check 14:01 (2026-07-18)** — KEINE neuen Produkte/Verkäufe in 12:00–14:00.
  STORE unverändert total=5 drafts=5 published=0; T2 weiter BLOCKED (Gumroad 10/Tag-Limit:
  `upload_missing_drafts.py` meldet DAILY LIMIT HIT, alle 8 Drafts fehlen; 04:00-Retry-Cron
  `58f0ebc08d11` läuft, Fenster resettet ~24h nach erstem Create heute früh — kein manueller Push,
  kein ToS-Bypass). Pages HTTP 200 (erreichbar). 0 Sales (sales.log fehlt).
  **Sale-Rail MEASURED funktionsfähig (unterstützt T4/T5):** 3 Stripe-Buy-Links → HTTP 200;
  4 Download-Gates (/dl/<hash>/<slug>.html) → HTTP 200; robots.txt Disallow /dl/ korrekt,
  sitemap.xml vorhanden. Erster Sale über Stripe-Links jederzeit möglich sobald Traffic da.

- **2h-cron status-check 16:01 (2026-07-18)** — letzte ~2h (14:01–16:01): 1 autonomer Commit `1ee6ef1` (15:42):
  ADR-0013 `create_link` idempotent (REUSE statt Neu-Generierung) + **13 Link-Seiten** auf konsistente
  Stripe-Links im Registry aktualisiert (MEASURED: 13 index.html geändert, Pages HTTP 200). Mehr als
  diese 1 Änderung passierte nicht. STORE unverändert total=5 drafts=5 published=0; 8 Drafts fehlen,
  weiter BLOCKED durch Gumroad 10/Tag-Limit (`upload_missing_drafts.py` -> DAILY LIMIT HIT; 04:00-Retry-Cron
  `58f0ebc08d11` läuft, kein manueller Push, kein ToS-Bypass). Pages HTTP 200 (erreichbar).
  0 Sales (sales.log fehlt; `sale_poller.py` live: "0 new sales", detektiert price>0).
- **2h-cron status-check 18:01 (2026-07-18)** — letzte ~2h (16:01–18:01): autonomer PRODUKT-PIVOT
  (ADR-0018) zu Lese-Begleitern (Study Guides) + 2 neue Bücher live. 9 Commits lagen lokal,
  NICHT gepusht → live-Site war hinkend (hatte Stripe-Buttons, aber kein Begleiter-Inhalt).
  Dieser Cron hat die 9 Commits gepusht → CI-Deploy erfolgt: Begleiter-Inhalt JETZT LIVE
  (MEASURED: live /1260/ hat 9 "Begleiter"-Matches; neue Bücher /768/ + /215/ = HTTP 200).
  Inhalt des Fensters: TB-17/ADR-0017 "Wuthering Heights" (Gutenberg 768) live; TB-18
  "The Call of the Wild" (Gutenberg 215) live; TB-19/ADR-0018 Study-Guide-Generator
  (13 Guides, 4 Tests grün) + TB-19b LLM-Fill (11/13 mit echtem LLM-Inhalt tencent/hy3:free
  gefüllt, 25913 korrupt übersprungen, 1 ohne Inhalt) + Begleiter-Deliverables/Landingpages.
  Push verifiziert KEINE Secrets im Diff. STORE unverändert total=5 drafts=5 published=0;
  8 Drafts fehlen, T2 weiter BLOCKED (Gumroad 10/Tag: `upload_missing_drafts.py` -> DAILY LIMIT HIT;
  04:00-Retry-Cron `58f0ebc08d11` läuft, kein manueller Push, kein ToS-Bypass). Pages HTTP 200
  (erreichbar, jetzt mit Begleiter-Inhalt). 0 Sales (sales.log fehlt; Sale-Rail Stripe messbereit).
  **Nächstes Wayfinder-Ticket: T5 (Publish-Strategie)** bleibt offen — braucht Nutzer-Entscheidung
  (Publish allein = 0 Traffic, Discover braucht $100). Fokus lag auf Produktwert statt T5.
- **T3 — Distribution-Kanal-Entscheidung** — RESOLVED 2026-07-18 (per Betriebs-Charta/Nutzer):
  Kanal = **SEO-Landingpages (GitHub Pages) zuerst**. Autonomes Social-Posting (Pinterest/Reddit)
  ausdrücklich NICHT erlaubt (freigabepflichtig, Hard Stop). Pinterest-/Reddit-Details -> Out-of-Scope.
  Nächstes offenes Ticket: **T5** (Publish-Strategie).

## Open Tickets (Frontier)

- ~~**T1 — GitHub Pages Deployment** (`task`) — RESOLVED 2026-07-18.~~ (siehe Decisions so far)
- **T2 — 3 fehlende Drafts live** (`task`, AFK via Cron): 2701/345/84 warten auf 04:00-Retry-Cron
  (`58f0ebc08d11`). BLOCKED by Gumroad 10/Tag-Limit (MEASURED: Fenster resettet ~24h nach
  erstem Create heute früh). Resolve wenn STORE: total=8 drafts=8 published=0.
- ~~**T3 — Distribution-Kanal-Entscheidung** (`grilling`) — RESOLVED 2026-07-18 (siehe Decisions so far).~~
  Kanal = SEO-Landingpages (Charta: kein autonomes Social-Posting). Pinterest/Reddit -> Out-of-Scope.
  **Nächstes offenes Ticket: T5** (Publish-Strategie).
- ~~**T4 — First-Sale-Measurement** (`research`) — RESOLVED 2026-07-18.~~ (siehe Decisions so far)
- **T5 — Publish-Strategie** (`grilling`) — NÄCHSTES OFFENES TICKET: wann/wie Drafts→published? Discover braucht $100 Sales
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
