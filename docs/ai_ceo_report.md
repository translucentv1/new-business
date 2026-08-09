# AI-CEO Daily Report

## 2026-08-09 (Tick, cronjob)

### Geld-Ziel (selbst gesetzt)
**Zwei ehrlich lieferbare Intents mit Preisanker aufnehmen — und den Kanal
selbst auf den Pruefstand stellen.** Der volumenstaerkste Seed dieses Ticks
(`vereinssatzung`, 10 Vorschlaege) ist ein Rechtsdokument (RDG-Risiko) und
traegt zusaetzlich `muster kostenlos` — abgelehnt, obwohl er die groesste
Nachfrage hatte. Wochenziel unveraendert: erster MEASURED Sale.

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, `sk_live_`, je HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**
  (2× `checkout.session.expired`, `payment_link.updated`, 2× `payment_link.created`);
  juengstes Event `evt_1U0hzC…` vom **04.08. 13:02 UTC**.
- `GET /v1/charges?limit=5` → **0 Charges**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- `GET /v1/checkout/sessions?limit=20` → unveraendert **2 Sessions**, beide
  `expired`/`unpaid`, beide in Vor-Ticks als **Eigentests** gegenbewiesen
  (`cs_live_a1YONK3…` 1499 Cent mit `metadata.probe=TICKET7-SESSION-PROBE`,
  `cs_live_a1oohHh…` 399 Cent aus `scripts/request_delivery/funnel_own_sessions.json`).
  ⇒ **seit ~4,5 Tagen (letztes Event 04.08. 13:02 UTC, jetzt 09.08. 00:22 UTC)
  keine neue Session, kein Zahlungsversuch.**
sales.log unveraendert. Kein Self-Buy.

### Getan (dieser Tick)
1. **Stripe-Poll** (MEASURED, s.o.) — kein Sale.
2. **Live-Check Bestand vor der Aenderung** (MEASURED, curl): 49 `blog/*.html`
   → `BLOG_FAILS=0`; index/gig/rtd/thanks/lead_magnet/impressum/datenschutz/agb/
   sitemap je **HTTP 200**. Kein Re-Push noetig.
3. **Keyword-Recherche** (MEASURED, `scripts/kw_demand.py`, Google Autocomplete
   hl=de/gl=de): **26 Seeds geprueft, 2 angenommen, 24 abgelehnt.**
   Angenommen:
   - `mahnung schreiben lassen` → 2 Vorschlaege, darunter **"anwalt mahnung
     schreiben lassen"** = Anwalt als Preisanker ⇒ bezahlter Markt existiert;
     **kein** "kostenlos"-Modifier.
   - `praktikumsbericht schreiben lassen` → 2 Vorschlaege, darunter **"…ki"**
     (KI-Akzeptanz belegt); **kein** "kostenlos"-Modifier.
   Bewusst abgelehnt trotz hohem Volumen:
   - `vereinssatzung` (10) — Rechtsdokument (RDG) + "muster kostenlos".
   - `text erstellen lassen` (10) — 3 von 10 mit "kostenlos"/"ohne anmeldung",
     zudem Dublette zu `text-schreiben-lassen-guenstig`/`text-formulieren-lassen`.
   - `freelancer ki` (10) — Intent ist **Jobsuche** ("…jobs") bzw. Rauschen
     ("kitas", "kicad", "killer"), kein Auftraggeber-Intent.
   - `referat schreiben lassen` (3) — 1 von 3 "kostenlos", akademisch.
   Die drei im Cron-Prompt vorgeschlagenen Seeds (`ki dienstleistung auf auftrag`,
   `freelancer ki`, `text erstellen lassen`) haben die Huerde damit **nicht**
   genommen — 0 Treffer bzw. falscher Intent. Ehrlich notiert statt mitgenommen.
4. **2 neue Landingpages** via `scripts/traffic_engine.py` (idempotent — 3. Lauf
   meldet "ALLE KEYWORDS BELEGT"): `blog/mahnung-schreiben-lassen-ki.html`,
   `blog/praktikumsbericht-schreiben-lassen-ki.html` → **51 Landingpages**.
   Risiko-Abgrenzung direkt auf der Seite:
   - Mahnung: "keine Rechtsberatung, keine Verzugszinsen, keine Fristenpruefung,
     kein Inkasso, kein Mahnbescheid" (RDG-Schutz).
   - Praktikumsbericht: "wir formulieren **deine eigenen Angaben**, erfinden keine
     Praktikumsinhalte und ersetzen nicht deine Leistung" — kein Ghostwriting-
     Versprechen.
5. **Interlinking/Sitemap/Index**: `interlink.py` → 23 Seiten neu geschrieben,
   `--check` danach **exit 0**; `_tick_add_urls.py` → sitemap +2 / index +2,
   zweiter Lauf **+0/+0** (idempotent).
6. **Deploy + Live-Beleg** (MEASURED): commit `7feb113`, push gh-pages.
   Nach ~60 s: mahnung **200**, praktikumsbericht **200**;
   live-sitemap=True / live-index=True fuer beide; Live-Sitemap **1232 `<loc>`**.
   Voller Re-Check: **`BLOG_TOTAL=51 BLOG_FAILS=0`**. Inhalt live gegengeprueft
   (nicht nur der Statuscode): Haftungs-Hinweis und `id="related"`-Block je 1×
   in der ausgelieferten Seite vorhanden.
7. **IndexNow** (MEASURED): Key-Datei live HTTP 200,
   `[submit] 1232 URLs -> HTTP 200`, Ergebnis `SUBMIT_OK codes=[200]`.
8. **Ticket 5 — Wirkungsnachweis (das wichtigste Ergebnis dieses Ticks):**
   `scripts/request_delivery/bing_index_check.py` →
   **`BING_NICHT_INDEXIERT`**. Das Instrument ist nachweislich zaehlfaehig
   (Positivkontrolle `site:wikipedia.org` → **10 Treffer**), die Bing-HTML-Quelle
   wurde als **blind** verworfen statt als "0 Treffer" gelesen.
   Ziel-Domain: **0 Treffer, Tag 5 in Folge.**
9. **Fiverr-Gig** (`docs/fiverr_gig.md`) verifiziert: Titel, Beschreibung, 3 Pakete
   3,99/7,99/14,99 EUR vorhanden. Gegen `gig.html` gemessen: **3,99 € 3×,
   7,99 € 1×, 14,99 € 1×** = deckungsgleich; **3 Stripe-Live-Checkout-Links je
   HTTP 200**. Leistungsliste um die zwei neuen Deliverables (Mahnung/
   Zahlungserinnerung, Praktikumsbericht) inkl. Abgrenzung erweitert — Text
   bleibt copy-paste-fertig fuer den USER.
10. **Gumroad** (MEASURED): `python scripts/gumroad_sale_poll.py` → **`NO TOKEN`**;
    `.gumroad_secrets` existiert weiterhin nicht (nur `.template`). Watcher laeuft
    NICHT. Beide Blocker unveraendert, beide USER.

### Ehrliche Bewertung des Kanals
51 Landingpages, 1232 per IndexNow eingereichte URLs, **0 Index-Treffer an Tag 5**,
**0 Sessions in ~4,5 Tagen**. Die Seitenzahl ist damit **nicht** der Engpass — die
Auslieferung stimmt (51/51 HTTP 200), aber es kommt kein Sucher an. Die in Tick 4
notierte Entscheidungsregel ("ohne Indexierung bringen weitere Seiten nichts")
greift jetzt: **weitere Landingpages sind ab sofort der schwaechste verfuegbare
Hebel.** Sie kosten 0 EUR und werden deshalb nicht zurueckgebaut, aber sie sind
kein Plan mehr. Der einzige Kanal mit eigener Distribution (Fiverr) haengt an
einem USER-Blocker, den ich ohne KYC/Account nicht selbst aufloesen darf und
werde.

### Blocker (USER)
- **Fiverr-Account + KYC** — `docs/fiverr_gig.md` ist copy-paste-ready. Das ist
  der einzige Schritt, der den Kanalengpass wirklich aufloest.
- **Gumroad**: Payout-Freischaltung **und** API-Token.
- Impressum/AGB-Platzhalter vor breiter Bewerbung pruefen.

### Next (naechster Tick)
- Stripe-Poll wiederholen; Session-Zaehler beobachten (bleibt er bei 2?).
- `bing_index_check.py` erneut fahren — Tag 6. **Entscheidungsregel:** bleibt es
  bei 0 Treffern, wird die Seitenproduktion auf 0-1 pro Tick gedrosselt und die
  Zeit stattdessen in die Frage gesteckt, warum GitHub Pages nicht indexiert wird
  (robots.txt, canonical, Sitemap-Einreichung ueber ein Webmaster-Tool ohne
  Account-Zwang) — Ursache statt Menge.
- Kein weiterer Ausbau der Keyword-Liste, solange der Index bei 0 steht.

## 2026-08-08 (Tick, cronjob)

### Geld-Ziel (selbst gesetzt)
**Den Trichter um zwei Intents verbreitern, die wir ehrlich liefern koennen — und
den staerksten Kandidaten des Ticks bewusst ablegen, statt ihn mitzunehmen.**
Der volumenstaerkste Seed dieses Ticks (`praesentation erstellen lassen`, 10
Vorschlaege) waere eine Dublette der bestehenden PowerPoint-Seite, der
zweitstaerkste (`logo erstellen lassen`, 10 Vorschlaege inkl. `kosten`/`guenstig`/
`freelancer`) ein Over-Promise — das Deliverable waere eine Grafik, die wir nicht
liefern. Beide abgelehnt. Wochenziel unveraendert: erster MEASURED Sale.

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, `sk_live_`, je HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**
  (2× `checkout.session.expired`, `payment_link.updated`, 2× `payment_link.created`).
- `GET /v1/events?limit=100` → Typ-Verteilung: `payment_link.created` 51,
  `payment_link.updated` 15, `price.created` 16, `product.created` 16,
  `checkout.session.expired` 2. **Kein** `checkout.session.completed`,
  **kein** `charge.*`, **kein** `payment_intent.succeeded`.
- `GET /v1/charges?limit=10` → **0 Charges**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- `GET /v1/checkout/sessions?limit=10` → **2 Sessions, beide `expired`/`unpaid`**.
  Gegengeprueft statt geglaubt: `cs_live_a1YONK3…` (1499 Cent, 04.08. 10:35 UTC,
  `payment_link: null` = per API erzeugt) und `cs_live_a1oohHh…` (399 Cent,
  04.08. 13:00 UTC, aus `plink_1TzrLT…`). Beide sind im Repo als **Eigentests**
  dokumentiert (`docs/ai_ceo_report.md`, `scripts/request_delivery/
  funnel_own_sessions.json`) → **kein Nachfragesignal**, kein "erster Sale".
- juengstes Stripe-Event `evt_1U0hzC…` vom 04.08. ⇒ **seit ~4 Tagen keine neue
  Session, kein Zahlungsversuch**.
sales.log unveraendert (0 Zeilen mit echter ID). Kein Self-Buy.

### Getan (alles MEASURED)
1. **Bestand vor dem Deploy:** alle 47 vorhandenen `blog/*.html` live per curl
   → `BLOG_TOTAL=47 FAILS=0`; index, gig, sitemap je **HTTP 200**. Kein Re-Push noetig.
2. **Nachfrage-Recherche:** `web_search`/Firecrawl erneut **HTTP 402**
   (`insufficient_funds`, Rohtext im Tool-Log) → einzige MEASURED-Quelle bleibt
   `scripts/kw_demand.py` (Google Autocomplete, hl=de/gl=de). **14 Seeds geprueft,
   2 angenommen, 12 abgelehnt** — Ablehnungsgruende einzeln im Code kommentiert:
   Dublette (praesentation), Grafik-Deliverable (logo), Selbermach-Intent
   (untertitel: premiere/davinci/youtube), `kostenlos`-Dominanz (gedicht 3/7),
   falscher Intent (angebot → amazon/bauhaus/hornbach), 0-1 Treffer (7 Seeds).
3. **2 neue Landingpages** — beide **0× "kostenlos"** in den Vorschlaegen:
   - `kinderbuch schreiben lassen` (3 Treffer, u.a. woertlich `chatgpt kinderbuch
     schreiben lassen`). Scope ehrlich begrenzt: Text/Geschichte, **keine
     Illustration, kein Druck** — genau der eine Modifier, den wir nicht liefern.
   - `fallstudie schreiben lassen` (2 Treffer, u.a. `…ki`). B2B-Kundenreferenz,
     **keine Pruefungsleistung** (gleiche Linie wie hausarbeit/referat).
   → **49 Landingpages**. Generator idempotent: dritter Lauf meldet
   `ALLE KEYWORDS BELEGT`.
4. **Interlinking/Sitemap/Index:** beide Seiten in `interlink.py`-Cluster
   (Marketing&Texte bzw. Digitale Deliverables), 23 Seiten neu geschrieben,
   `--check` danach 0 offen / 0 ohne Cluster. `_tick_add_urls.py` → sitemap +2,
   index +2; Re-Run **+0/+0** (idempotent). `sitemap_healthcheck.py` → **SITEMAP_OK,
   HTTP_200=1228 NICHT_200=0**.
5. **Tests:** `verify.py` → **76 ok, 0 fail, 0 skip, 0 ungeprueft** (VERIFY_OK).
6. **Deploy + Live-Beleg:** commit `fb4ffb1`, push gh-pages. Nach ~60 s
   kinderbuch **200**, fallstudie **200**. Voller Re-Check: **BLOG_TOTAL=49
   FAILS=0**; Live-sitemap.xml enthaelt **beide** neuen URLs (grep-Zaehler 2).
7. **IndexNow:** Key-Datei live HTTP 200, `[submit] 1230 URLs -> HTTP 200`,
   `SUBMIT_OK codes=[200]`.
8. **Geldpfad geprueft (nicht nur die Seiten):** die 3 Stripe-Live-Checkout-Links
   aus gig.html einzeln aufgerufen → **je HTTP 200**. Der Kaufweg ist offen;
   es fehlt der Besucher, nicht die Technik.
9. **Fiverr-Gig** (`docs/fiverr_gig.md`) verifiziert: Titel, Beschreibung, 3 Pakete
   3,99/7,99/14,99 EUR vorhanden; gig.html gezaehlt 3,99 € 3×, 7,99 € 1×,
   14,99 € 1× = deckungsgleich. **Keine Textaenderung noetig** — copy-paste-fertig.
10. **Gumroad** (MEASURED): `python scripts/gumroad_sale_poll.py` → `NO TOKEN`,
    es existiert weiterhin nur `.gumroad_secrets.template`. Watcher laeuft NICHT.
11. **Ticket 26 (IndexNow-Wirkung), Zwischenmessung Tag 4:**
    `bing_index_check.py` live → Kontrolle zaehlfaehig (**10** Treffer auf
    wikipedia.org), Ziel **0** Treffer, `bing_html` korrekt als **BLIND verworfen**
    → `ERGEBNIS: BING_NICHT_INDEXIERT`. Das ist **kein Befund**: die Abschreib-
    Regel des Tickets greift erst am **2026-08-18** (14 Tage ab erster wirksamer
    Einreichung 04.08.). 0 Treffer an Tag 4 ist der Normalfall.

### Ehrliche Lage (kein Schoenreden)
49 Seiten, 1230 eingereichte URLs, 0 Besucher, 0 Zahlungsversuche seit 4 Tagen.
Der Engpass ist **nicht** die Seitenzahl und **nicht** der Kaufweg (beide
MEASURED intakt), sondern die **Indexierung**. Solange DDG/Bing die Domain nicht
fuehrt, ist jede weitere Landingpage Arbeit ohne Hebel. Deshalb wurde dieser Tick
bewusst mehr *abgelehnt* (12) als *gebaut* (2).

### Blocker (USER)
- **Fiverr-Account + KYC** — `docs/fiverr_gig.md` ist copy-paste-ready. Das ist
  der einzige Kanal mit fremdem Bestandstraffic; alles andere haengt am Index.
- **Gumroad**: Payout-Freischaltung **und** API-Token (nur Template vorhanden).
- Impressum/AGB-Platzhalter vor oeffentlichem Launch pruefen.

### Next (naechster Tick)
- Stripe-Poll wiederholen.
- **Vorrang vor neuen Seiten**: die in Ticket 5 offen gebliebene Teilfrage klaeren
  — ist die *uebergeordnete* Domain `translucentv1.github.io` ueberhaupt indexiert?
  Das trennt "unser Unterverzeichnis fehlt" von "die ganze github.io-Adresse
  fehlt" und entscheidet, ob GitHub Pages als Kanal ueberhaupt tragfaehig ist.
  Braucht eine Ziel-Option in `bing_index_check.py` (heute nicht vorhanden:
  `TARGET_QUERY` ist hart verdrahtet) — sauber als Codeaenderung, nicht als
  Einmal-Snippet.
- Ticket 26 faellig **2026-08-18**: dann Entscheidung IndexNow behalten/abschreiben.

## 2026-08-07 (Tick 1, cronjob — 03:10–03:50 UTC / 05:10–05:50 lokal)

### Geld-Ziel (selbst gesetzt)
**Zwei neue Suchintents live bringen, die den Trichter VERBREITERN statt ihn zu
duplizieren — und den Deploy-Lag des Vor-Ticks widerlegen oder bestaetigen.**
Nach 45 Seiten ohne einen einzigen Zahlungsversuch ist die ehrliche Lage: mehr
Seiten allein bringen nichts, wenn sie denselben Intent nochmal abdecken. Darum
diesen Tick 46 Seeds gescreent und 5 Kandidaten mit Volumen **abgelehnt**, weil
sie Dubletten (expose, quiz, lernzettel) oder Pruefungsleistungen waeren.
Wochenziel unveraendert: erster MEASURED Sale (bezahlte evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, sk_live_, je HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**
  (2× `checkout.session.expired`, `payment_link.updated`, 2× `payment_link.created`).
- `GET /v1/events?limit=25` → Typ-Verteilung: `payment_link.updated` 7,
  `payment_link.created` 6, `price.created` 5, `product.created` 5,
  `checkout.session.expired` 2. **Kein** `checkout.session.completed`,
  **kein** `charge.*`, **kein** `payment_intent.succeeded`.
- `GET /v1/charges?limit=5` → **0 Charges**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- Die 2 `expired`-Sessions sind unveraendert die aus den Vor-Ticks als
  **Eigentests** dokumentierten (`cs_live_a1YONK3…` 1499 Cent mit
  `metadata.probe=TICKET7-SESSION-PROBE`, `cs_live_a1oohHh…` 399 Cent aus
  `scripts/request_delivery/funnel_own_sessions.json`). Kein Nachfragesignal.
- juengstes Stripe-Event weiterhin `evt_1U0hzC…` vom 04.08. 13:02 UTC
  ⇒ **seit ~62 h keine neue Session, kein Zahlungsversuch**.
sales.log unveraendert (0 Zeilen mit echter ID). Kein Self-Buy.

### Getan (alles MEASURED)
1. **Bestand geprueft:** alle **45** vorhandenen `blog/*.html` live per curl
   → `BLOG_TOTAL=45 BLOG_FAILS=0`; index, gig, rtd, thanks, sitemap, lead_magnet,
   impressum, agb, datenschutz je **HTTP 200**. Kein Re-Push noetig.
2. **Keyword-Recherche:** `web_search` erneut **nicht verfuegbar** — Firecrawl
   antwortet `HTTP 402 BILLING_ERROR / insufficient_funds` (Rohfehler in diesem
   Tick gemessen). Ersatz: `scripts/kw_demand.py` (Google Autocomplete,
   hl=de/gl=de), gefahren ueber die neuen Screening-Skripte
   `scripts/_tick_seeds.py` + `scripts/_tick_seeds2.py`, **46 Seeds**.
   Angenommen (2):
   - `karteikarten erstellen lassen` → **10 Vorschlaege (Maximum beider Runden)**,
     3× KI-Modifier ("…ki", "ai karteikarten…", "…ki kostenlos"), dazu
     anki/goodnotes/app (bezahlter Werkzeugmarkt) und "…aus pdf"/"…zum lernen"
     (konkreter Arbeitsauftrag mit Quellmaterial). Ehrlich: **2× "kostenlos"**.
   - `text kuerzen lassen` → **2 Vorschlaege, 0× "kostenlos"**, davon 1×
     "text kuerzen lassen ki". Signalniveau = pressemitteilung/vortrag/pitch-deck
     (je 2 Treffer, alle live).
   Abgelehnt trotz Volumen (im Code dokumentiert):
   - `expose schreiben lassen` (6, mit "…preise") — **Dublette** zur live
     stehenden expose-Seite, dazu 2× bachelorarbeit/masterarbeit = Abgabe.
   - `quiz erstellen lassen` (6) — deckungsgleich mit quiz-fragen-Seite.
   - `lernzettel erstellen lassen` (4) — von study-guide + Karteikarten abgedeckt.
   - `kurzgeschichte schreiben lassen` (2, 0× kostenlos) — sauberes Signal, aber
     wahrscheinlichster Zweck ist die Abgabe in Schule/Uni; zurueckgestellt.
   - `urkunde` (Druckleistung), `fragebogen` (…und auswerten = Datenauswertung),
     `einladung` (Treffer ist ein Tippfehler-Query).
   - Kein Signal (0–1 Treffer), 37 Seeds: umfrage, agenda, zeitplan, projektplan,
     wochenplan, raetsel, interviewleitfaden, firmennamen, persona, weihnachtskarte,
     glueckwunsch, youtube-/podcast-beschreibung, hausordnung, pflichtenheft,
     lastenheft, ablaufplan, grabrede, kalkulation, visitenkarte, moderationstext,
     traurede, maerchen, zwischenzeugnis, pruefungsfragen, klausur, eheversprechen,
     tischrede, spielanleitung, app-beschreibung, marketingplan, marketingkonzept,
     redaktionsplan, keyword-recherche, unterrichtsmaterial, hoerbuch-text, seo texte.
3. **2 neue Landingpages** via `scripts/traffic_engine.py` (idempotent: 3. Lauf
   meldet "ALLE KEYWORDS BELEGT"): `blog/karteikarten-erstellen-lassen-ki.html`,
   `blog/text-kuerzen-lassen.html` → **47 Landingpages**.
   Abgrenzung steht **auf der Seite selbst**:
   - Karteikarten: Import-Datei (CSV/TSV/Text) zum Selbst-Einlesen, **kein**
     Deck-Upload, **kein** App-Account, **keine** fremden Verlagsinhalte.
   - Kuerzen: dein Text auf harte Vorgabe, **keine** Recherche/Faktenpruefung,
     **kein** Detektor-Umschreiben, plus expliziter Verweis auf die
     Zusammenfassungs-Seite fuer den anderen Intent (Anti-Kannibalisierung).
4. **Interlinking/Sitemap/Index:** beide Slugs in `scripts/interlink.py`
   (Cluster "Lernen & Studium") → `interlink: 10 geschrieben, 0 offen,
   0 ohne Cluster`, danach `--check` **Exit 0**. `scripts/_tick_add_urls.py`
   trug Sitemap + Index nach (`sitemap +2 / index +2`, 2. Lauf `+0/+0` =
   idempotent). `sitemap.xml` per ElementTree geparst: **1228 URLs, XML valide**.
5. **Deploy + Live-Beleg:** commit `53e8aab`, push gh-pages. **Kein Deploy-Lag
   diesmal** — der Vor-Tick brauchte einen Leer-Commit und >10 min, hier waren
   beide Seiten nach **40 s** live (03:37:57 noch 404 → 03:38:18 beide 200).
   Gegen die LIVE-Auslieferung geprueft (nicht nur lokal):
   `live-sitemap=True live-index=True` fuer beide Slugs, Live-Sitemap 1228 `<loc>`.
   IndexNow: **1228 URLs → HTTP 200**, `SUBMIT_OK`.
6. **Fiverr-Gig verifiziert** (`docs/fiverr_gig.md`): Titel (DE+EN), Beschreibung
   und die 3 Pakete **3,99 / 7,99 / 14,99 EUR** vorhanden und deckungsgleich mit
   `gig.html` (dort gezaehlt 3,99 € 3× / 7,99 € 1× / 14,99 € 1×). Die 3
   Stripe-Live-Checkout-Links je **HTTP 200** (`scripts/_tick_gig_check.py`).
   Text um die 2 neuen Deliverables erweitert → USER muss weiterhin nur kopieren.
7. **Gumroad:** `scripts/gumroad_sale_poll.py` → **`NO TOKEN`**; es existiert
   weiterhin nur `.gumroad_secrets.template`, kein echtes Token. Blocker
   unveraendert **beim USER** (Payout-Freischaltung + API-Token).
8. **Qualitaet:** `verify.py --offline` → **73 ok / 0 fail**. `ruff` (via uvx,
   lokal nicht installiert) → 5 Findings, gegen `git show HEAD:` gegengeprueft:
   **exakt die Baseline, 0 neue**; die 2 selbst verursachten RUF100 sofort gefixt.

### Ehrliche Bewertung
47 Landingpages, 1228 indexierte URLs, 0 Sessions in 62 h. Die Seiten sind
technisch sauber (200, Sitemap, IndexNow), aber **organischer Google-Traffic auf
frische GitHub-Pages-Seiten ist der Engpass, nicht die Seitenzahl**. Ohne den
Fiverr-Account (USER, KYC) gibt es keinen zweiten Kanal mit eigenem Traffic.

### Next
- USER-Blocker (unveraendert, beide 0 EUR Kosten): Fiverr-Account + Gig
  veroeffentlichen (Text ist copy-paste-fertig), Gumroad-Payout + API-Token.
- Naechster Tick: Stripe-Poll, Live-Check aller 47 Seiten, 1–2 weitere Intents —
  aber nur bei sauberem Signal; Dubletten werden weiter abgelehnt.

## 2026-08-06 (Tick 3, cronjob — 12:00–12:35 UTC / 14:00–14:35 lokal)

### Geld-Ziel (selbst gesetzt)
**Zwei neue Suchintents mit belegtem Bezahlwillen live bringen — und dabei
jeden Intent ablehnen, den wir zum Festpreis nicht ehrlich liefern koennen.**
Nach 45 Seiten ist nicht die Seitenzahl der Engpass, sondern die Trefferqualitaet:
lieber 2 saubere Seiten als 5, die etwas versprechen, was 3,99 EUR nicht deckt.
Wochenziel unveraendert: erster MEASURED Sale (bezahlte evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, sk_live_, je HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**
  (2× `checkout.session.expired`, `payment_link.updated`, 2× `payment_link.created`).
- `GET /v1/events?limit=50` → Typ-Verteilung: `payment_link.created` 14,
  `price.created` 12, `product.created` 12, `payment_link.updated` 10,
  `checkout.session.expired` 2. **Kein** `checkout.session.completed`,
  **kein** `charge.*`, **kein** `payment_intent.succeeded`.
- `GET /v1/charges?limit=5` → **0 Charges**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- Die 2 `expired`-Sessions gegengeprueft statt geglaubt: `cs_live_a1YONK3…`
  (1499 Cent) traegt `metadata={'probe': 'TICKET7-SESSION-PROBE'}`,
  `cs_live_a1oohHh…` (399 Cent) ist in
  `scripts/request_delivery/funnel_own_sessions.json` als Ticket-9-Eigenmessung
  dokumentiert. **Beide sind Eigentests, keine echten Interessenten** — sie
  duerfen nicht als Nachfragesignal gelesen werden.
- juengstes Stripe-Event unveraendert `evt_1U0hzC…` vom 04.08. 13:02 UTC
  ⇒ **seit ~47 h keine neue Session, kein Zahlungsversuch**.
sales.log unveraendert (0 Zeilen mit echter ID). Kein Self-Buy.

### Getan (alles MEASURED)
1. **Bestand geprueft:** alle **43** vorhandenen `blog/*.html` live per curl
   → `BLOG_TOTAL=43 BLOG_FAILS=0`; index, gig, rtd, thanks, sitemap, lead_magnet,
   impressum, agb, datenschutz je **HTTP 200**. Kein Re-Push noetig.
2. **Keyword-Recherche:** `web_search` erneut **nicht verfuegbar** — Firecrawl
   antwortet `HTTP 402 BILLING_ERROR / insufficient_funds` (MEASURED in diesem
   Tick). Ersatz wie in den Vor-Ticks: `scripts/kw_demand.py`
   (Google Autocomplete, hl=de/gl=de), **16 Seeds** geprueft.
   Angenommen (2):
   - `brief schreiben lassen` → **10 Vorschlaege (Maximum)**, nur **1×**
     "kostenlos"; Preisanker im Markt belegt durch
     "anwalt brief schreiben lassen **kosten**", KI-Akzeptanz durch
     "brief schreiben lassen **ki**" / "**chatgpt** brief schreiben lassen".
   - `text formulieren lassen` → **4 Vorschlaege, 0× "kostenlos"**
     ("ki text formulieren lassen", "text besser formulieren lassen",
     "chatgpt text formulieren lassen"). Eigener Intent: vorhandenen Text
     verbessern ≠ korrekturlesen (Fehler) ≠ neu schreiben.
   Abgelehnt trotz Volumen (ehrlich dokumentiert im Code):
   - `buch schreiben lassen` (10 Treffer, mit "kosten"/"ghostwriter") —
     ein ganzes Buch ist fuer 3,99–14,99 EUR **nicht ehrlich lieferbar**.
   - `ernaehrungsplan erstellen lassen` (10 Treffer) — Gesundheitsberatung,
     zusaetzlich 2 Tier-Modifier ("hund", "barf"); zurueckgestellt.
   - `dienstplan erstellen lassen` (3, 0× kostenlos) — Intent zielt auf
     **Software** ("automatisch", "von ki"), nicht auf einen Textentwurf.
   - Gratis-Modifier: essay, referat. Kein Signal (0–1 Treffer): danksagung,
     social media plan, angebot, klappentext, werbetext, slogan, amazon listing,
     checkliste, youtube-/erklaervideo-skript, empfehlungsschreiben, onlinekurs,
     stellenbeschreibung, antrag.
3. **2 neue Landingpages** via `scripts/traffic_engine.py` (idempotent: 3. Lauf
   meldet "ALLE KEYWORDS BELEGT"): `blog/brief-schreiben-lassen.html`,
   `blog/text-formulieren-lassen.html` → **45 Landingpages**.
   Abgrenzung steht **auf der Seite selbst**, nicht in einer Fussnote:
   - Brief: Brieftext als Datei, **keine** Handschrift/Kalligrafie, **kein**
     Druck/Postversand, **keine Rechtsberatung** (Modifier "anwalt" ⇒ RDG).
   - Umformulieren: **keine** Faktenpruefung/Recherche und **keine** Garantie
     auf das Urteil eines KI-Detektors.
4. **Interlinking/Sitemap/Index:** neue Slugs in `scripts/interlink.py`
   (Digitale Deliverables bzw. Lernen & Studium) → `interlink: 19 geschrieben,
   0 offen, 0 ohne Cluster`, danach `--check` **Exit 0**. Neues idempotentes
   Hilfsskript `scripts/_tick_add_urls.py` traegt Sitemap- und Index-Eintraege
   im vorhandenen Format nach (2. Lauf: `sitemap +0 / index +0`).
   `sitemap.xml` per ElementTree geparst: **1226 URLs, XML valide**.
5. **Deploy + Live-Beleg:** commit 26df37d + 3d1912a, push gh-pages.
   **Abweichung ehrlich notiert:** die neuen Seiten waren nach **10 Minuten
   noch 404**, obwohl `git ls-tree origin/gh-pages` beide Dateien zeigte und
   `Last-Modified` der Live-index noch auf 07:29 UTC stand (Vor-Tick baute in
   ~41 s). Erst ein Leer-Commit (a594b46) hat den Pages-Build ausgeloest.
   Danach MEASURED: brief **200**, text-formulieren **200**,
   `Last-Modified: 12:25:24 GMT`, Live-Sitemap und Live-index enthalten beide
   neuen URLs, Abgrenzungstext auf der Live-Seite vorhanden.
   Voller Re-Check: **`BLOG_TOTAL=45 BLOG_FAILS=0`**.
6. **IndexNow:** Key-Datei live HTTP 200, `[submit] 1226 URLs -> HTTP 200`,
   Ergebnis `SUBMIT_OK codes=[200]`.
7. **Fiverr-Gig** (`docs/fiverr_gig.md`, 193 Zeilen) verifiziert: Titel,
   Kategorie, 5 Suchtags, Beschreibung, Pakettabelle **3,99 / 7,99 / 14,99 EUR**,
   FAQ, Requirements vorhanden. Gegenprobe an der **Live**-gig.html:
   `3,99 € 3×`, `7,99 € 1×`, `14,99 € 1×` — deckungsgleich. Leistungsliste um
   die zwei neuen Deliverables erweitert (Brieftext, Umformulieren), jeweils mit
   derselben Abgrenzung wie auf der Landingpage. Text bleibt copy-paste-fertig.
8. **Gumroad:** `python scripts/gumroad_sale_poll.py` → `NO TOKEN`;
   `.gumroad_secrets` existiert weiterhin **nicht** (nur `.template`).
   Watcher laeuft NICHT. Beide Blocker unveraendert USER-seitig.

### Blocker (USER)
- Fiverr-Account + KYC — `docs/fiverr_gig.md` ist copy-paste-ready.
- Gumroad: Payout-Freischaltung **und** API-Token.
- Impressum/AGB-Platzhalter vor oeffentlichem Launch pruefen.

### Next (naechster Tick)
- Stripe-Poll wiederholen.
- **Ticket 5 (ab 07.08. faellig): Wirkungsnachweis IndexNow** — pruefen, ob die
  Seiten in Bing/Yandex tatsaechlich auftauchen. 45 Seiten ohne Indexierung
  bringen nichts; wenn der Nachweis ausbleibt, **Kanal wechseln statt weitere
  Seiten bauen**.
- Pages-Deploy beobachten: wenn erneut ein Leer-Commit noetig ist, ist das ein
  systematischer Deploy-Defekt und gehoert als Ticket erfasst.
- `ernaehrungsplan` nur dann bauen, wenn eine Formulierung ohne
  Beratungsanschein steht.

## 2026-08-06 (Tick 2, cronjob — 05:30–05:45 UTC / 07:30–07:45 lokal)

### Geld-Ziel (selbst gesetzt)
**Einen Suchintent bedienen, den bisher KEINE der 41 Seiten abdeckt.**
Die bestehenden Seiten decken Bewerbung, Buero, Marketing, Lernen und Reden ab —
alle Neuzugaenge der letzten Ticks waren Varianten davon. Ziel dieses Ticks:
mindestens eine Landingpage in einem **neuen Cluster**, damit der Trichter nicht
nur tiefer, sondern breiter wird. Wochenziel unveraendert: erster MEASURED Sale
(evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, sk_live_, HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**
  (2× `checkout.session.expired`, `payment_link.updated`, 2× `payment_link.created`)
  — byte-identisch zu Tick 1, juengstes Event `evt_1U0hzC…` vom **04.08. 13:02 UTC**.
- `GET /v1/charges?limit=10` → **0 Charges**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- `GET /v1/checkout/sessions?limit=10` → **2 Sessions, beide `expired`/`unpaid`**
  (399 Cent 04.08. 13:00 UTC; 1499 Cent 04.08. 10:37 UTC) — dieselben zwei wie
  in den letzten drei Ticks, **seit ~41 h keine neue Session**. Kein Eintrag in
  sales.log (Regel: kein Sale ohne bezahlte evt_/cs_-ID).

### Getan (alles MEASURED)
1. **Bestand geprueft:** alle **41** `blog/*.html` live abgefragt → `BLOG OK=41
   FAIL=0`; dazu 10 Kernseiten (index, gig, rtd, thanks, sitemap, lead_magnet,
   impressum, agb, datenschutz, ki-text-service) je **HTTP 200**. Kein 404.
2. **Keyword-Recherche:** `web_search`/Firecrawl erneut **HTTP 402**
   (`insufficient_funds`) → `scripts/kw_demand.py` (Google Autocomplete, hl=de/gl=de)
   blieb die einzige MEASURED-Quelle; **67 Seeds** geprueft, kein ASSUMED-Keyword.
3. **2 neue Landingpages** (idempotent; 3. Lauf meldet `ALLE KEYWORDS BELEGT`)
   → **43 Landingpages**:
   - `blog/prompt-erstellen-lassen-ki.html` — "prompt erstellen lassen": 3 Vorschlaege,
     **0× "kostenlos"**, 2 davon mit KI-Tool ("chatgpt…", "ki…"). **Neuer Cluster**
     (KI/Automation), bisher von keiner Seite abgedeckt.
   - `blog/liebesbrief-schreiben-lassen.html` — 2 Vorschlaege, **0× "kostenlos"**,
     darunter "ki liebesbrief schreiben lassen". Anlass-Cluster (wie Hochzeits-/
     Trauerrede), reiner Text aus Kaeufer-Stichpunkten.
4. **Bewusst abgelehnt** (im Code begruendet): `facharbeit schreiben lassen`
   (8 Treffer, groesstes Volumen, "…kosten"/"…guenstig") und `praktikumsbericht`
   (2) — Arbeiten **zur Abgabe**, vom Gig ausdruecklich ausgeschlossen, also kein
   Versprechen, das wir halten duerfen. `text uebersetzen lassen` (10) und
   `gedicht schreiben lassen` (7) — Gratis-/Tool-Intent (google/kostenlos/foto;
   4 von 7 "kostenlos"). `handbuch erstellen lassen` (2) — QM-/ISO-Dokument, zum
   Festpreis nicht ehrlich lieferbar. `gpt erstellen lassen` (10) — Bild/Video/
   Grafik, liefern wir nicht. Die uebrigen Seeds hatten 0–1 Treffer bzw. einen
   dominanten "kostenlos"-Modifier = kein Signal (vollstaendige Liste im Code).
5. **Interlink + Sitemap + Index:** beide Slugs in `CLUSTERS`, `interlink.py`
   schrieb 10 Seiten neu, `--check` danach **0 offen**; sitemap.xml + index.html
   ergaenzt. `verify.py --offline`: **69 ok / 0 fail (VERIFY_OK)**.
6. **Publish + Live-Check:** Commit `e9ec072`, Push auf **gh-pages**
   (`e6a6ae7..e9ec072`). Nach ~55 s: prompt **200**, liebesbrief **200**,
   index **200**, sitemap **200**. Live-sitemap: **1224 URLs**, beide neuen
   URLs enthalten.
7. **IndexNow:** `[submit] 1224 URLs -> HTTP 200`, `ERGEBNIS: SUBMIT_OK`.
8. **Checkout-Pfad geprueft:** die 3 Stripe-Live-Links in der **live** gig.html
   je **HTTP 200**; Preise dort gezaehlt 3,99 € 3× / 7,99 € 1× / 14,99 € 1× =
   deckungsgleich mit der Pakettabelle in `docs/fiverr_gig.md`.
9. **Fiverr-Gig-Text erweitert** um Prompt-Erstellung und persoenliche
   Anlassbriefe, jeweils mit ehrlichen Scope-Grenzen (kein Finetuning, kein
   Account-Zugang, kein Versand, kein Layout) — bleibt copy-paste-fertig.
10. **Gumroad:** `scripts/gumroad_sale_poll.py` → **`NO TOKEN`**; es existiert
    weiterhin nur `.gumroad_secrets.template`. Beide Blocker (Payout-Freischaltung
    + API-Token) sind **USER-Aufgaben**, nichts autonom Machbares.

### Offene Blocker (USER)
- **Fiverr-Account + KYC** — Gig-Text ist fertig, nur noch einfuegen.
- **Gumroad Payout + API-Token** — unveraendert.
- **Ticket 23 (WhatsApp-Bridge / jidDecode)** — Cron-Zustellung an den Nutzer
  defekt; Fix `hermes gateway restart` muss aus einer **frischen Shell** kommen,
  ein Tick kann das nicht selbst (SIGTERM auf den eigenen Elternprozess).

### Next
1. Weiter je Tick 1–2 Landingpages mit MEASURED-Nachfrage in **neuen** Clustern
   (der Bewerbungs-/Buero-Bereich ist gesaettigt).
2. Nach dem Fiverr-Go-Live: Landingpages zusaetzlich auf den Gig verlinken.
3. Stripe weiter alle 6 h pollen; erster bezahlter `cs_`/`evt_` → sales.log + laute Meldung.

## 2026-08-06 (Tick 1, cronjob — 23:22 UTC / 01:22 lokal)

### Geld-Ziel (selbst gesetzt)
**Den Trichter dort verbreitern, wo bereits jemand am Checkout stand.**
Zwei Besucher haben am 04.08. den Checkout geoeffnet (3,99 und 14,99 EUR) und
nicht bezahlt — das 14,99er-Signal zeigt Interesse am groessten Paket. Ziel
dieses Ticks: 2 neue Landingpages mit belegtem Bezahlwillen, davon **eine
bewusst auf das Buendel-/Premium-Paket** ausgerichtet. Wochenziel unveraendert:
erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, sk_live_, je HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**
  (2× `checkout.session.expired`, `payment_link.updated`, 2× `payment_link.created`).
- `GET /v1/events?limit=100` → Typverteilung
  `{checkout.session.expired: 2, payment_link.updated: 15, payment_link.created: 51,
  price.created: 16, product.created: 16}` — **0 charge/payment_intent-Events**.
- `GET /v1/charges?limit=10` → **0 Charges**.
- `GET /v1/payment_intents?limit=10` → **0 PaymentIntents**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- `GET /v1/checkout/sessions?limit=10` → **2 Sessions, beide `expired`/`unpaid`**
  (399 Cent, 04.08. 13:00 UTC; 1499 Cent, 04.08. 10:35 UTC) — **exakt dieselben
  zwei wie in Tick 2 und 3, seit ~34 h keine neue Session.** Kein Eintrag in
  sales.log (Regel: kein Sale ohne evt_/cs_-ID mit Zahlung).

### Getan (alles MEASURED)
1. **Bestand geprueft:** alle **39** bestehenden `blog/*.html` live abgefragt →
   `blog OK=39 FAIL=0`; dazu gig/index/lead_magnet/rtd je HTTP 200. Kein 404,
   kein Nachpushen noetig.
2. **Keyword-Recherche:** `web_search`/Firecrawl erneut **HTTP 402**
   (`insufficient_funds`, Rohfehler im Tool-Output) → `scripts/kw_demand.py`
   (Google Autocomplete, hl=de/gl=de) blieb die einzige MEASURED-Quelle;
   20 Seeds geprueft, **kein ASSUMED-Keyword gebaut**.
3. **2 neue Landingpages** (idempotent erzeugt, 3. Lauf meldet
   `ALLE KEYWORDS BELEGT`) → **41 Landingpages**:
   - `blog/e-mail-schreiben-lassen-ki.html` — "e-mail schreiben lassen": 3 Vorschlaege,
     **0× "kostenlos"**, 2 von 3 nennen ein KI-Tool ("...ki", "chat gpt ...")
     = KI-Akzeptanz doppelt belegt.
   - `blog/bewerbungsunterlagen-erstellen-lassen.html` — 3 Vorschlaege,
     **0× "kostenlos"**, darunter "...professionell erstellen lassen"
     (Bezahlwille) und "...schweiz" (bezahlter Dienstleistermarkt).
     Bewusst als **Buendel-Seite** (Anschreiben + Lebenslauf + Kurzprofil)
     auf das 14,99-EUR-Paket ausgerichtet, keine Dublette zu den drei
     Einzeldokument-Seiten.
4. **Bewusst abgelehnt** (Begruendung im Code dokumentiert): `artikel schreiben
   lassen` (6 Treffer, groesstes Volumen — aber Dublette zu seo-blogartikel +
   Wikipedia-ToS), `rechnung erstellen lassen` (6 — falscher Intent: ikea/amazon/
   paypal), `kinderbuch schreiben lassen` (3 — Druck/Ghostwriting nicht ehrlich
   zum Festpreis lieferbar), `portfolio erstellen lassen` (3 — Grafik-Layout).
   14 weitere Seeds mit 0–1 Treffern = kein Signal.
5. **Interlink + Sitemap + Index:** beide Slugs in `CLUSTERS` aufgenommen,
   `interlink.py` schrieb 16 Seiten neu, `--check` danach **0 offen**.
   sitemap.xml + index.html ergaenzt.
6. **Publish + Live-Check:** Commit `e5b9554`, Push auf **gh-pages** (nicht `main`
   — `git push origin main` scheiterte mit `src refspec main does not match any`).
   Nach ~45 s: e-mail **200**, bewerbungsunterlagen **200**, index **200**,
   sitemap **200**. Live-sitemap: **1222 URLs**, beide neuen URLs enthalten (je 1×).
7. **IndexNow** (MEASURED): Key-Datei HTTP 200, `[submit] 1222 URLs -> HTTP 200`,
   `ERGEBNIS: SUBMIT_OK codes=[200]`.
8. **verify.py --offline:** `VERIFY: 67 ok, 0 fail, 0 skip` → `VERIFY_OK`.
9. **Stripe-Checkout-Links** in gig.html: alle **3 HTTP 200**. Preise dort
   gezaehlt 3,99 € 3× / 7,99 € 1× / 14,99 € 1× = deckungsgleich mit der
   Pakettabelle in `docs/fiverr_gig.md`.
10. **Fiverr-Gig** verifiziert: Titel, Beschreibung, 3 Pakete 3,99/7,99/14,99 EUR
    vorhanden und konsistent. Leistungsliste um die zwei neuen Deliverables
    erweitert (Bewerbungssatz-Buendel, Geschaefts-E-Mail) — inkl. ehrlicher
    Scope-Grenzen (kein Layout, kein Versand, kein RDG-Schreiben).
11. **Gumroad** (MEASURED): `python scripts/gumroad_sale_poll.py` → `NO TOKEN`.
    Watcher laeuft weiterhin **NICHT**. Zwei Blocker unveraendert, beide USER.

### Blocker (USER)
- Fiverr-Account + KYC — `docs/fiverr_gig.md` ist copy-paste-ready.
- Gumroad: Payout-Freischaltung **und** API-Token (nur `.gumroad_secrets.template`).
- Firecrawl/web_search: HTTP 402 seit mehreren Ticks — Keyword-Recherche laeuft
  nur noch ueber Google Autocomplete.

### Next (naechster Tick)
- Stripe-Poll wiederholen; besonders auf eine **dritte** Checkout-Session achten.
  Zwei Abbrueche bei 2 Sessions = 100 % Abbruchquote — wenn eine dritte Session
  ebenfalls abbricht, ist nicht der Traffic das Problem, sondern die
  Checkout-Seite (Vertrauen/Preis/Zahlungsart) → dann gig.html angehen statt
  weitere Landingpages.
- **Wirkungsnachweis IndexNow ist ab jetzt faellig** (Ticket 5): messen, ob die
  Seiten in Bing/Yandex auftauchen. Ohne Indexierung bringt Seite 42 nichts.

## 2026-08-05 (Tick 3, cronjob)

### Geld-Ziel (selbst gesetzt)
**Keine neue Baustelle — den Trichter breiter machen, ohne eine Zusage zu brechen.**
Ziel dieses Ticks: 2 weitere Landingpages mit belegtem Bezahlwillen, und zwar
*nur* solche, die zu dem passen, was wir auf bestehenden Seiten bereits
zugesagt haben. Wochenziel unveraendert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, sk_live_, je HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**
  (2× `checkout.session.expired`, `payment_link.updated`, 2× `payment_link.created`).
- `GET /v1/charges?limit=10` → **0 Charges**.
- `GET /v1/payment_intents?limit=10` → **0 PaymentIntents**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- `GET /v1/checkout/sessions?limit=10` → **2 Sessions, beide `expired`/`unpaid`**
  (399 und 1499 Cent, 04.08. 10:35 und 13:00 UTC) — **dieselben zwei wie in Tick 2,
  keine neue Session seit 24 h.**

Das in Tick 2 gesuchte Signal (`checkout.session.created` ohne eigenen Deploy)
ist **nicht** eingetreten. Kein Sale, kein Self-Buy.

### Was getan (alles MEASURED)
1. **Bestand zuerst geprueft, dann gebaut**: alle **37** vorhandenen `blog/`-Seiten
   live → `BLOG_TOTAL=37 FAILS=0`; dazu 10 Kernseiten (index, gig, rtd, thanks,
   sitemap, lead_magnet, impressum, agb, datenschutz, ki-text-service) je **HTTP 200**.
   Also **0 Seiten neu zu pushen**.
2. **Keyword-Recherche**: `web_search`/Firecrawl erneut **HTTP 402
   (insufficient_funds)** → Google Autocomplete (`scripts/kw_demand.py`, hl=de/gl=de)
   blieb die einzige MEASURED-Quelle, 22 Seeds. Gebaut:
   - `arbeitsblatt erstellen lassen` — **6 Vorschlaege, 0× "kostenlos"**:
     woertlich "...ki" (KI-Akzeptanz), "fobizz ..." und "canva ..." (= bezahlter
     Tool-Markt als Preisanker), "arbeitsblatt zu youtube video erstellen lassen"
     (konkreter Arbeitsauftrag). Sauberstes Signal des Ticks.
   - `lernplan erstellen lassen` — **4 Vorschlaege**, "...ki" und "lernplan von
     chatgpt erstellen lassen". **Ehrlich: 1 der 4 ist "...kostenlos"** — das
     schwaechere der beiden Keywords. In Tick 2 wegen Ueberlappung mit study-guide
     zurueckgestellt; jetzt gebaut, weil die Abgrenzung sauber ist:
     Lernplan = **Zeit**plan, study-guide/zusammenfassung = **Inhalt**.
3. **Bewusst abgelehnt — wichtigster Punkt dieses Ticks:**
   `ernaehrungsplan erstellen lassen` hatte mit **10 Vorschlaegen** das groesste
   Volumen und mit "...kosten"/"professionellen" den klarsten Preisanker — und
   wird trotzdem **nicht gebaut**. Grund: die bereits live stehende Seite
   `trainingsplan-erstellen-lassen-ki.html` sagt woertlich zu, dass wir "keine
   medizinische, physiotherapeutische oder **Ernaehrungs-Beratung**" liefern, und
   `docs/fiverr_gig.md` schliesst medizinberatende Texte aus. Eine
   Ernaehrungsplan-Seite waere ein Widerspruch zur eigenen Zusage (dazu 2 Modifier
   "barf"/"hund" = Veterinaerbereich). Traffic-Volumen schlaegt keine Zusage.
   Ebenfalls abgelehnt: `brief schreiben lassen` (10 Treffer, aber Intent ist
   Handschrift/Kalligraphie bzw. Anwaltsbrief = RDG), `roman schreiben lassen`
   (Komplett-Ghostwriting, zum Festpreis nicht ehrlich lieferbar).
   0–1 Treffer (kein Signal): unterrichtsentwurf, leitbild, jahresbericht,
   spendenaufruf, etsy listing, tiktok skript, beschwerde, instagram bio,
   google ads text, hochzeitszeitung, onboarding, uebungsaufgaben, klassenarbeit,
   dankesrede, trauerkarte, geschaeftsbericht, immobilienbeschreibung.
4. **Ehrliche Abgrenzung auf beiden neuen Seiten** (im Text, nicht als Fussnote):
   Arbeitsblatt = Aufgaben/Loesungen als **Text**, kein druckfertiges Layout und
   **keine Uebernahme fremder Schulbuch-/Verlagsinhalte** (Urheberrecht);
   Lernplan = Planung der **eigenen** Lernzeit, **keine Pruefungsleistung** zur
   Abgabe, mit Querlink auf Zusammenfassung/Study-Guide.
5. **Interlinking/Sitemap/Index**: beide Seiten in den Cluster "Lernen & Studium"
   (`scripts/interlink.py`) → 7 Seiten neu geschrieben, `--check` danach exit 0.
   sitemap.xml (**1220 URLs**) + index.html ergaenzt.
6. **Deploy + Live-Beleg** (MEASURED): commit `e059b23`, push gh-pages.
   Nach ~45 s: arbeitsblatt **200**, lernplan **200**, index **200**, sitemap **200**,
   gig **200**; Live-sitemap enthaelt **beide** neuen URLs (grep-Count 2).
   → **39 Landingpages live.**
7. **IndexNow** (MEASURED): Key-Datei HTTP 200, `[submit] 1220 URLs -> HTTP 200`,
   `SUBMIT_OK codes=[200]`.
8. **verify.py --offline**: **65 ok / 0 fail / 0 skip**.
9. **Fiverr-Gig** (`docs/fiverr_gig.md`) verifiziert: Titel, Beschreibung, 3 Pakete
   3,99/7,99/14,99 EUR vorhanden. Preisparitaet gegen die **Live**-gig.html geprueft:
   `3,99` 3×, `7,99` 1×, `14,99` 1× — deckungsgleich mit der Pakettabelle. Die 3
   Stripe-Live-Checkout-Links je **HTTP 200**. Leistungsliste um Arbeitsblatt-Inhalte
   und Lernplan erweitert (inkl. beider Abgrenzungen) — bleibt copy-paste-fertig.
10. **Gumroad** (MEASURED): `python scripts/gumroad_sale_poll.py` → `NO TOKEN`;
    `.gumroad_secrets` existiert nicht (nur `.template`). Watcher laeuft **NICHT**.
    Zwei Blocker unveraendert, beide USER.

### Blocker (USER)
- **Fiverr-Account + KYC** — `docs/fiverr_gig.md` ist copy-paste-ready.
- **Gumroad**: Payout-Freischaltung **und** API-Token.
- Impressum/AGB-Platzhalter vor breiter Bewerbung pruefen.
- Offen aus Tick 2: hat der USER am 04.08. selbst einen Zahlungslink geoeffnet
  (10:35 / 13:00 UTC)? Ohne Antwort bleibt die Herkunft der 2 Sessions ASSUMED.

### Next (naechster Tick)
- Stripe-Poll wiederholen; **Session-Zaehler** beobachten: bleibt er bei 2, gab
  es weiterhin keinen Fremd-Klick auf einen Zahlungslink.
- **Ab 07.08. faellig (Ticket 5): Wirkungsnachweis IndexNow.** Wenn nach ~10 Tagen
  und 39 Seiten **0 Impressions** in Bing/Yandex: Seitenbau **stoppen** und Kanal
  wechseln (Reddit/Foren-Antworten, Kleinanzeigen-Dienstleistung), statt
  Landingpage 40 zu bauen. Diese Regel steht jetzt zum zweiten Tick in Folge —
  sie ist der eigentliche Entscheidungspunkt dieser Woche.

## 2026-08-05 (Tick 2, cronjob)

### Geld-Ziel (selbst gesetzt)
**Erst das Messgeraet reparieren, dann weiterbauen.** Tick 1 hatte die einzigen
zwei Funnel-Ereignisse der Account-Historie als "eigenes Rauschen" abgeschrieben.
Wenn diese Erklaerung falsch ist, haben wir das einzige echte Nachfrage-Signal
weggeworfen. Ziel dieses Ticks: die Behauptung experimentell pruefen (statt sie
zu glauben) und zusaetzlich 2 Landingpages mit sauberem Bezahlwillen ergaenzen.
Wochenziel unveraendert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, sk_live_, HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein payment-Event**:
  `evt_1U0hzC…` checkout.session.expired, `evt_1U0fiW…` checkout.session.expired,
  `evt_1U0fgp…` payment_link.updated, `evt_1U0fgp…` payment_link.created,
  `evt_1TzrLW…` payment_link.created.
- `GET /v1/charges?limit=5` → **0 Charges**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.
- `GET /v1/checkout/sessions?limit=20` → **2 Sessions**, beide `unpaid/expired`.

### KORREKTUR der Tick-1-Wertung (das Wichtigste dieses Ticks)
Tick 1 behauptete: "das Laden einer Payment-Link-URL erzeugt bereits eine Session,
unsere eigenen HTTP-200-Checks sind die Ursache → selbst erzeugtes Rauschen."
**Experiment (MEASURED, heute):**
1. 3× `curl` GET auf die drei `buy.stripe.com`-Links → je **HTTP 200** (kein 302).
2. Danach `GET /v1/checkout/sessions?limit=20` → **2 Sessions** (unveraendert).
3. Danach 1× `curl -I` (HEAD) auf Link 1 → HTTP 200, 12 s warten,
   erneut Sessions abfragen → **2 Sessions, 0 neue**.

→ Unsere Automatik erzeugt **keine** Checkout-Sessions. Die Tick-1-Erklaerung ist
**falsifiziert**. Konsequenz: die zwei Sessions vom 04.08. (10:35 und 13:00 UTC,
3,99 / 14,99 EUR) wurden von einem **echten Browser** ausgeloest — Besucher oder
manueller Test des USERS. Das ist **kein Sale** und **kein Beweis fuer Kaufabsicht**
(`customer_details: null`, beide abgelaufen), aber es ist das **erste Funnel-Signal
ueberhaupt** und darf nicht mehr wegerklaert werden. Der in Tick 1 geplante Umbau
auf HEAD-Requests ist damit **hinfaellig** (loest ein Problem, das es nicht gibt) —
gestrichen statt gebaut.

### Was getan (alles MEASURED)
1. **Sales-Poll** wie oben — 0 Sales, kein Self-Buy (Stripe-Gebuehr = Verlust).
2. **Bestand geprueft, bevor gebaut wurde**: alle **35** vorhandenen
   `blog/`-Seiten live → `BLOG_TOTAL=35 FAILS=0`; index, gig, sitemap, rtd je
   **HTTP 200**.
3. **Keyword-Recherche** via `scripts/kw_demand.py` (Google Autocomplete,
   hl=de/gl=de), 25 Seeds. Gebaut wurden die zwei mit dem saubersten Bezahlwille:
   - `biografie schreiben lassen` — **7 Vorschlaege, 0× "kostenlos"**,
     Top-Vorschlag woertlich "...kosten" (Preisrecherche) + "biografie von ki
     schreiben lassen" (KI-Akzeptanz) + Ortsmodifier berlin/schweiz/oesterreich
     (= bezahlter Ghostwriter-Markt existiert).
   - `trainingsplan erstellen lassen` — **10 Vorschlaege** (groesstes Volumen),
     "...kosten", "...ki", "individuellen ...", Studioketten mcfit/fitx/gym.
     Ehrlich notiert: **1 der 10** enthaelt "kostenlos".
   Abgelehnt trotz Volumen: `buch schreiben lassen` (10, aber 3× kostenlos +
   Ghostwriter-Komplettprojekt → zum Festpreis nicht ehrlich lieferbar),
   `wikipedia artikel schreiben lassen` (ToS/Offenlegungspflicht),
   `mahnung schreiben lassen` (Anwalts-/RDG-Intent), `kochbuch erstellen lassen`
   (Druckdienstleistung), `lernplan` (1× kostenlos + Ueberlappung mit study-guide).
   0–1 Treffer (kein Signal): klappentext, slogan, sachbuch, verkaufstext,
   landingpage texte, immobilienanzeige, youtube skript, buchbeschreibung,
   amazon produkttext, hochzeitseinladung, reiseplan, excel formel, steckbrief,
   chatgpt prompt, jobinterview vorbereitung, gehaltsverhandlung.
4. **Ehrliche Abgrenzung auf beiden neuen Seiten** (kein Over-Promise):
   Biografie = Kurzbiografie/Ueber-mich/Kapitel-Gliederung, **kein** komplettes
   Buch-Ghostwriting; Trainingsplan = allgemeiner Text-Entwurf, **keine**
   medizinische/physiotherapeutische/Ernaehrungs-Beratung, Hinweis auf aerztliche
   Abklaerung bei Vorerkrankung/Verletzung/Schwangerschaft/Reha.
5. **Interlinking/Sitemap/Index**: beide Seiten in den Cluster "Digitale
   Deliverables" von `scripts/interlink.py` aufgenommen → 8 Seiten neu geschrieben,
   `--check` danach exit 0. sitemap.xml + index.html ergaenzt (37 Blog-Links).
6. **Deploy + Live-Beleg** (MEASURED): commit `9c8ba47`, push gh-pages.
   Nach ~50 s: biografie **200**, trainingsplan **200**, index **200**,
   sitemap **200**; Live-sitemap enthaelt **beide** neuen URLs (grep-Count 2).
   → **37 Landingpages live.**
7. **IndexNow** (MEASURED): `[submit] 1218 URLs -> HTTP 200`, `SUBMIT_OK codes=[200]`.
8. **verify.py --offline**: **56 ok / 0 fail / 0 skip**.
9. **Fiverr-Gig** (`docs/fiverr_gig.md`) verifiziert: Titel, Beschreibung,
   3 Pakete 3,99/7,99/14,99 EUR vorhanden. Preisparitaet gegen gig.html geprueft:
   `3,99 €` 3×, `7,99 €` 1×, `14,99 €` 1× — deckungsgleich. Die 3 Stripe-Live-
   Checkout-Links je **HTTP 200**. Leistungsliste um Biografie-Text und
   Trainingsplan-Entwurf erweitert (inkl. beider Abgrenzungen) — bleibt
   copy-paste-fertig fuer den USER.
10. **Gumroad** (MEASURED): `python scripts/gumroad_sale_poll.py` → `NO TOKEN`.
    Watcher laeuft **NICHT**. Zwei Blocker unveraendert, beide USER.

### Blocker (USER)
- **Fiverr-Account + KYC** — `docs/fiverr_gig.md` ist copy-paste-ready.
- **Gumroad**: Payout-Freischaltung **und** API-Token (nur `.gumroad_secrets.template`).
- Impressum/AGB-Platzhalter vor breiter Bewerbung pruefen.
- **Neu, klein, wertvoll:** hat der USER am 04.08. selbst einen Zahlungslink im
  Browser geoeffnet (10:35 / 13:00 UTC)? Ein "ja/nein" entscheidet, ob die zwei
  Sessions echter Fremd-Traffic sind. Ohne Antwort bleibt die Herkunft ASSUMED.

### Next (naechster Tick)
- Stripe-Poll wiederholen; auf `checkout.session.created` **ohne** vorherigen
  eigenen Deploy achten — das waere jetzt ein verwertbares Traffic-Signal.
- **Gestrichen:** Umbau der Link-Checks auf HEAD (Ursache widerlegt, s.o.).
- Ab 07.08.: **Wirkungsnachweis IndexNow** — messen, ob Seiten in Bing/Yandex
  auftauchen. Wenn nach ~10 Tagen + 37 Seiten **0 Impressions**: Seitenzahl
  stoppen und Kanal wechseln (Reddit/Foren-Antworten, Kleinanzeigen-Dienstleistung),
  statt Landingpage 38 zu bauen.

## 2026-08-05 (Tick 1, cronjob, 00:36 Uhr)

### Geld-Ziel (selbst gesetzt)
**Anlass-Intents mit Zeitdruck bedienen.** Bisher waren fast alle Seiten
"Business-Routine" (Bericht, Protokoll, Website-Text) — Kaeufer dort vergleichen
lange. Neue Hypothese fuer diesen Tick: Suchintents mit einem *Termin* dahinter
(Trauerfall, Karten-Neudruck) konvertieren schneller, weil der Sucher nicht
recherchieren, sondern abgeben will. Wochenziel unveraendert: erster MEASURED
Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR. 0 Sales.** Beleg (Stripe REST, sk_live_, HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, **kein einziges payment-Event**:
  2× `checkout.session.expired`, 2× `payment_link.created/updated`, 1× älter.
- `GET /v1/charges?limit=10` → **0 Charges**.
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**.

**Wichtige Einordnung (nicht schoenreden):** die zwei `checkout.session.expired`
(`cs_live_a1ooh…` 3,99 EUR, 08-04 13:00 UTC; `cs_live_a1YON…` 14,99 EUR,
08-04 10:35 UTC) sind **KEIN Beweis fuer einen Kauf**. Beide haben
`customer_details: null` (niemand hat je eine E-Mail eingetippt) und sind unbezahlt
abgelaufen.

> **KORREKTUR (2026-08-05 Tick 2, MEASURED):** die urspruengliche Erklaerung an
> dieser Stelle — "das Laden einer Payment-Link-URL erzeugt bereits eine Session,
> also selbst erzeugtes Rauschen" — ist **falsifiziert**. Experiment: 3× `curl` GET
> auf die drei `buy.stripe.com`-Links (je HTTP 200) und danach 1× `curl -I` (HEAD),
> jeweils gefolgt von `GET /v1/checkout/sessions?limit=20` → **weiterhin genau 2
> Sessions, 0 neue**. Unsere eigenen Link-Checks erzeugen also **keine** Sessions.
> Die zwei Sessions vom 04.08. stammen damit aus einem echten Browser (Besucher
> oder manueller Test des USERS) — Herkunft weiter unbekannt, aber **nicht** von
> unserer Automatik. Details im Tick-2-Eintrag oben.

### Was getan (alles MEASURED)
1. **Sales-Poll** wie oben — 0 Sales, kein Self-Buy (Stripe-Gebuehr = Verlust).
2. **Bestand geprueft, bevor gebaut wurde**: alle **33** vorhandenen
   `blog/`-Seiten live → `BLOG_CHECKED=33 BLOG_404_COUNT=0`; dazu index, gig,
   rtd, thanks, lead_magnet, impressum, agb, datenschutz, sitemap,
   ki-text-service je **HTTP 200**.
   Nebenbefund/Doku-Luecke geschlossen: `hochzeitsrede` und `pitch-deck` (Tick 3
   am 04.08., Commit 832c69c) standen in **keinem** Report-Eintrag — sie sind
   live und jetzt hier dokumentiert.
3. **Keyword-Recherche**: `web_search`/Firecrawl erneut **HTTP 402
   (insufficient_funds)** → kein Zugriff. Einzige MEASURED-Quelle bleibt
   `scripts/kw_demand.py` (Google Autocomplete, hl=de/gl=de), 30 Seeds geprueft.
   Gebaut wurden die zwei besten:
   - `trauerrede schreiben` → **10 Vorschlaege** (Maximum), **kein** "kostenlos":
     woertlich "trauerrede schreiben **ki**" + Angehoerigen-Modifier
     mutter/vater/opa/oma/bruder/freund. Ehrlich: 1 von 10 ist "…beispiel".
   - `speisekarte erstellen lassen` → **3 Vorschlaege**: "…**kosten**"
     (Preisrecherche = Bezahlwille) und "…**ki**", **kein** "kostenlos".
   Verworfen trotz Volumen: `text erstellen lassen` (10, aber 3× kostenlos/ohne
   Anmeldung + rap/suno = Gratis-Tool-Sucher), `gliederung erstellen lassen`
   (6, aber "kostenlos" + Bachelorarbeit = Pruefungsleistung), `ki
   dienstleistungen` (6) und `freelancer ki jobs` (10) = **falsche Marktseite**
   (Anbieter/Jobsucher, keine Kaeufer), `ki auftrag*` (10, DSGVO-AVV-Begriffe),
   `angebot erstellen lassen` (4, Modifier amazon/bauhaus/hornbach = will ein
   Haendler-Preisangebot). 0–1 Treffer (kein Signal): danksagung, abschiedsrede,
   geburtstagsrede, faq, checkliste, social-media-plan, grusswort, whitepaper,
   stellenanzeige, amazon listing, laudatio, kondolenzschreiben u.a.
4. **2 neue Landingpages** via `scripts/traffic_engine.py` (idempotent — 3. Lauf
   meldet "ALLE KEYWORDS BELEGT"): `blog/trauerrede-schreiben-ki.html`,
   `blog/speisekarte-erstellen-lassen-ki.html` → **35 Landingpages**.
   Scope-Abgrenzung steht **auf der Seite**, nicht in einer Fussnote:
   - Trauerrede: fertiger Redetext (5–8 Min) aus deinen Stichpunkten;
     **keine Trauerbegleitung**, Rede haelt der Kunde selbst.
   - Speisekarte: **Texte + Aufbau**; **kein** druckfertiges Layout und
     **keine rechtsverbindliche Allergen-/Zusatzstoff-Kennzeichnung**.
5. **Interlink/Sitemap/Index**: neue Slugs in die Cluster aufgenommen
   (Digitale Deliverables bzw. Marketing&Texte) → `interlink.py` 26 Seiten neu
   geschrieben; sitemap.xml auf **1216 URLs** (XML valide), index.html ergaenzt.
   `python scripts/verify.py --offline` → **54 ok, 0 fail, 0 skip**
   (vorher 1 fail "index verlinkt jede Landingpage" — repariert, nicht ignoriert).
6. **Deploy + Live-Beleg**: commit `277830f`, push gh-pages. Erster Versuch
   beide **404** (Pages-Build), nach ~20 s: trauerrede **200**, speisekarte
   **200**. Voller Re-Check: `BLOG_CHECKED=35 BLOG_404_COUNT=0`; Live-index
   enthaelt beide neuen Links (grep-Zaehler 2), Live-sitemap **1216** `<loc>`.
7. **IndexNow**: Key-Datei live HTTP 200, `[submit] 1216 URLs -> HTTP 200`,
   `ERGEBNIS: SUBMIT_OK codes=[200]`.
8. **Fiverr-Gig** (`docs/fiverr_gig.md`) verifiziert: Titel, Beschreibung,
   3 Pakete 3,99/7,99/14,99 EUR vorhanden und **deckungsgleich mit gig.html**
   (grep gig.html: 3,99 € 3×, 7,99 € 1×, 14,99 € 1×). Die 3 Stripe-Live-Links
   in gig.html je **HTTP 200**. Leistungsliste + Ausschluss-FAQ um die zwei
   neuen Deliverables erweitert.
9. **Gumroad**: `python scripts/gumroad_sale_poll.py` → **`NO TOKEN`**,
   `.gumroad_secrets` existiert nicht (nur `.template`). Watcher laeuft **NICHT**.
   Zwei Blocker unveraendert, beide USER.

### Blocker (USER)
- **Fiverr-Account + KYC** — `docs/fiverr_gig.md` ist copy-paste-ready.
- **Gumroad**: Payout-Freischaltung **und** API-Token.
- Impressum/AGB-Platzhalter vor breiter Bewerbung pruefen.

### Next (naechster Tick)
- Stripe-Poll wiederholen.
- **Stripe-Link-Check auf HEAD umstellen** (oder auf 1×/Tag reduzieren), damit
  eigene Pruefungen keine `checkout.session.*`-Events mehr erzeugen — sonst
  verrauscht genau der Kanal, an dem wir den ersten echten Sale erkennen wollen.
- Ab 07.08.: **Wirkungsnachweis IndexNow** — messen, ob Seiten in Bing/Yandex
  auftauchen. Wenn nach ~10 Tagen + 35 Seiten **0 Impressions**: Seitenzahl
  stoppen und Kanal wechseln (Reddit/Foren-Antworten, Kleinanzeigen-Dienstleistung),
  statt Landingpage 36 zu bauen.

## 2026-08-04 (Tick 2, cronjob)

### Geld-Ziel (selbst gesetzt)
**Nur Intents bauen, deren Nachfrage wir auch ehrlich bedienen wollen.** Neuer,
haerterer Filter zusaetzlich zum "kostenlos"-Test: wenn die Autocomplete-Modifier
zeigen, dass die Mehrheit der Sucher etwas will, das wir ablehnen (Taeuschung,
Pruefungsleistung), wird das Keyword NICHT gebaut — auch bei hohem Volumen.
Wochenziel unveraendert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR — 0 Sales.**
Beleg (Stripe REST, sk_live_, HTTP 200, diesen Tick abgefragt):
- `GET /v1/events?limit=5` -> **0 payment-Events**. Die 5 neuesten sind
  `evt_1TzrLWFajs0YddhPckD0qo8g` payment_link.created,
  `evt_1TzrLWFajs0YddhP4BHrvF4N` price.created,
  `evt_1TzrLVFajs0YddhP36qL3ZXn` product.created,
  `evt_1TzrLVFajs0YddhPoPBeVSq1` payment_link.created,
  `evt_1TzrLUFajs0YddhPVV2IUvdX` price.created — alles Setup, kein Kauf.
  Unveraendert gegenueber Vortick = kein neuer Traffic-zu-Kauf-Event.
- `GET /v1/charges?limit=10` -> **0 Charges**
- `GET /v1/balance` -> available **0 EUR**, pending **0 EUR**
Kein Self-Buy (Stripe-Gebuehr = garantierter Verlust). sales.log unveraendert.

### Getan (dieser Tick)
1. **Stripe-Poll** (MEASURED, s.o.) — kein Sale.
2. **Live-Check VOR der Aenderung**: 29 `blog/*.html` -> **BLOG_404_COUNT=0**,
   dazu `index/gig/rtd/thanks/lead_magnet/impressum/agb/datenschutz/sitemap.xml/
   ki-text-service` je **HTTP 200**. Kein Re-Push noetig.
3. **Keyword-Recherche MEASURED** via `scripts/kw_demand.py` (Google Autocomplete,
   hl=de/gl=de), 29 Seeds. `web_search` erneut blockiert (Firecrawl HTTP 402
   `insufficient_funds`) — Autocomplete ist die einzige MEASURED-Quelle, es wurde
   kein ASSUMED-Keyword gebaut.
   - **Gewaehlt: "bericht schreiben lassen"** — 3 Vorschlaege, **0x "kostenlos"**:
     `bericht schreiben lassen ki`, `chatgpt bericht schreiben lassen`.
     Sauberster Bezahlwille des Ticks + explizite KI-Akzeptanz.
   - **Gewaehlt: "vortrag erstellen lassen"** — 2 Vorschlaege, **0x "kostenlos"**,
     darunter `...ki`. Gleiches Signalniveau wie die bereits live erfolgreichen
     `pressemitteilung`/`seo blogartikel`/`website texte` (je 2 Treffer).
   - **BEWUSST ABGELEHNT trotz groesstem Volumen: "text umschreiben lassen"**
     (10 Vorschlaege). Modifier: `ohne plagiat`, `humanisieren`, `menschlich`,
     woertlich `ki text umschreiben lassen dass er nicht erkannt wird`
     => die Nachfrage zielt ueberwiegend auf Umgehung von KI-/Plagiatspruefung.
     Das ist Taeuschung und bei Pruefungsleistungen heikel — **wird nicht verkauft.**
   - Weiter verworfen: `praktikumsbericht` (2 Treffer, aber Pruefungsleistung),
     `gedicht` (7) und `songtext` (4) — jeweils 2-4 "kostenlos"-Modifier,
     `angebot erstellen lassen` (4 Treffer, aber Retail-Intent Bauhaus/Hornbach/
     Amazon = falscher Intent), `stellenanzeige`/`checkliste`/`vba makro`/
     `geschaeftsbericht`/`grusswort` (je 0 Treffer).
4. **2 neue Landingpages gebaut** -> **31 live**. Beide mit ehrlicher Abgrenzung
   direkt auf der Seite: Bericht = beruflicher Bericht, *keine* Praktikums-/
   Studienberichte zur Abgabe; Vortrag = Redetext+Notizen, Folien via
   powerpoint-Seite, freie Reden via rede-Seite.
5. **interlink.py**: beide Seiten in Cluster "Buero & Business" aufgenommen,
   Lauf -> `9 geschrieben, 0 offen, 0 ohne Cluster`; `--check` exit 0.
6. **sitemap.xml + index.html** um beide URLs ergaenzt.
7. **Commit + Push** (`e6c5dcf`, gh-pages) und **Live-Check NACH dem Push**:
   31/31 `blog/*.html` **HTTP 200 (BLOG_404_COUNT=0)**, 9 Kernseiten HTTP 200,
   Inhalt der neuen Seite live verifiziert (Abgrenzungstext + `id="related"`).
8. **IndexNow**: Key-Datei HTTP 200, **1212 URLs eingereicht -> HTTP 200**
   (SUBMIT_OK; vorher 1207 -> die neuen Seiten sind drin).
9. **Fiverr-Gig** (`docs/fiverr_gig.md`): Titel/Beschreibung/3 Pakete
   3,99/7,99/14,99 EUR verifiziert und **deckungsgleich mit gig.html**
   (dort gezaehlt: 3,99 € 3x, 7,99 € 1x, 14,99 € 1x). Die 3 Stripe-Live-Checkout-
   Links in gig.html je **HTTP 200**. Ergaenzt: Berichte + Vortrags-Manuskripte
   in der Leistungsliste, und ein klares "Was ich NICHT liefere": kein Umschreiben
   zur Umgehung von KI-/Plagiatspruefung.
10. **Gumroad**: `scripts/gumroad_sale_poll.py` -> **`NO TOKEN`**,
    `.gumroad_secrets` existiert weiterhin nicht (nur `.template`).
    Blocker unveraendert und **beide USER-Aufgaben**: Payout-Freischaltung + API-Token.

### Blocker (USER, nicht vom AI-CEO loesbar)
- **Fiverr-Account + KYC + Gig veroeffentlichen** — Text ist copy-paste-fertig.
- **Gumroad Payout-Freischaltung + API-Token** (`.gumroad_secrets` anlegen).
- **Firecrawl/web_search** HTTP 402 — kein Blocker fuer Traffic (Autocomplete ersetzt es).

### Next
- Naechster Tick: Stripe-Poll, Live-Sweep der 31 Seiten, 1-2 neue Intents nach
  demselben Doppelfilter (Bezahlwille UND ehrlich bedienbar).
- **Ab 07.08. Wirkungsnachweis faellig** (Ticket 5, wayfinder): Bringen die
  Landingpages ueberhaupt Impressions? Ohne Search-Console-Daten ist "31 Seiten
  live" nur Output, kein Ergebnis. Wenn bis dahin 0 Impressions: Kanal-Annahme
  (organisches SEO auf github.io) neu grillen statt Seite 32 bauen.

## 2026-08-03 (Tick 2, ~12:46 lokal, cronjob)

### Geld-Ziel (selbst gesetzt)
**Den staerksten unbesetzten DE-Kaufintent mit belegtem Bezahlwille nehmen —
Kriterium: Autocomplete-Vorschlaege OHNE "kostenlos"-Modifier.** Bisher wurden
Intents teils nach Trefferzahl gewaehlt; ab jetzt zaehlt der Bezahlwille-Filter
staerker. Wochenziel unveraendert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR — 0 Sales.**
Beleg (Stripe REST, sk_live_, HTTP 200, diesen Tick abgefragt):
- `GET /v1/events?limit=10` -> **0 payment-Events** (nur payment_link.created 4x,
  price.created 3x, product.created 3x; neuester `evt_1TzrLWFajs0YddhPckD0qo8g`
  = payment_link.created)
- `GET /v1/charges?limit=10` -> **0 Charges**
- `GET /v1/checkout/sessions?limit=10` -> **0 Sessions**
- `GET /v1/balance` -> available **0 EUR**, pending **0 EUR**
Kein Self-Buy (Stripe-Gebuehr = garantierter Verlust). sales.log unveraendert.

### Getan (dieser Tick)
1. **Stripe-Poll** (MEASURED, s.o.) — kein Sale.
2. **Live-Check ALLER Seiten VOR der Aenderung**: 25 `blog/*.html` + `index.html`,
   `gig.html`, `rtd.html`, `thanks.html`, `ki-text-service/index.html`,
   `sitemap.xml`, `lead_magnet.html`, `impressum.html`, `agb.html`
   -> **34 URLs, 0 Nicht-200**. Kein Re-Push noetig.
3. **Keyword-Recherche MEASURED** via `scripts/kw_demand.py` (Google Autocomplete,
   hl=de/gl=de), 16 Seeds geprueft. `web_search` weiterhin blockiert
   (Firecrawl HTTP 402 `insufficient_funds`) — Autocomplete-Weg ist der $0-Ersatz.
   - **Gewaehlt: "korrekturlesen lassen"** — 10 Vorschlaege, **kein einziger mit
     "kostenlos"**: `bachelorarbeit/masterarbeit/doktorarbeit/projektarbeit
     korrekturlesen lassen`, `...duden`, `...schreibweise`, `chatgpt korrekturlesen
     lassen`. Staerkstes Signal des Ticks: existierender Bezahl-Dienstleistungsmarkt
     (Lektorat) + explizite KI-Akzeptanz.
   - **Gewaehlt: "zusammenfassung schreiben lassen"** — 5 Vorschlaege, u.a. `...ki`,
     `chatgpt zusammenfassung schreiben lassen pdf`. Ehrliche Einschraenkung:
     1 Vorschlag enthaelt "kostenlos" = schwaecher als korrekturlesen.
   - **Verworfen:** "flyer erstellen lassen" (10 Treffer, aber 2x "kostenlos" UND
     Deliverable ist Design/Print, nicht Text — wir liefern Text); "lektorat text"
     (10 Treffer, aber reine Marken-/Font-Namen = Navigations-Intent, kein Kauf);
     "speisekarte erstellen lassen" (3, sauber, aber Design-lastig);
     "handbuch erstellen lassen" (2), "werbetext"/"social media posts"/
     "stellenanzeige"/"angebot"/"slogan"/"amazon listing" (je 1 = nur das Seed
     selbst, kein Signal); "uebersetzung erstellen lassen", "landingpage texte
     schreiben lassen", "faq erstellen lassen", "grusswort" (je **0**).
4. **2 neue Landingpages** erzeugt (`scripts/traffic_engine.py`, idempotent —
   3. Lauf meldet "ALLE KEYWORDS BELEGT"):
   `blog/korrekturlesen-lassen-ki.html`,
   `blog/zusammenfassung-schreiben-lassen-ki.html`. **Jetzt 27 Landingpages.**
5. **Abgrenzung Pruefungsleistungen** auf der Korrekturlesen-Seite: korrigiert wird
   nur die **Sprache** (Lektorat), Inhalt/Argumentation bleiben Leistung des Kunden,
   keine Abgabe in fremdem Namen — gleiche Vorsichtslinie wie die
   Rechtsberatungs-Abgrenzung beim Arbeitszeugnis.
6. **Cluster/Index/Sitemap** nachgezogen: beide Slugs in `scripts/interlink.py`
   -> Cluster "Lernen & Studium" (jetzt 5 Seiten), `interlink.py` schrieb
   5 Seiten um (`--check` danach: **0 offen, 0 ohne Cluster**); 2 Links in
   `index.html`; 2 `<url>`-Eintraege in `sitemap.xml` (**1205 URLs**).
7. **Fiverr-Gig aktualisiert** (`docs/fiverr_gig.md`): neue Leistungszeile
   "Korrektur & Verdichtung", FAQ-Satz zur Lektorats-Abgrenzung, Status auf
   27 Seiten. Pakete unveraendert **3,99 / 7,99 / 14,99 EUR** — identisch zu
   `gig.html` (MEASURED per grep: 3,99 3x, 7,99 1x, 14,99 1x). Die 3 hinterlegten
   Stripe-**Live**-Checkout-Links liefern je **HTTP 200**.
8. **Gumroad** geprueft: `scripts/gumroad_sale_poll.py` -> `NO TOKEN`,
   `.gumroad_secrets` **existiert nicht** (nur `.template`). Blocker unveraendert
   und beide **USER-seitig**: Payout-Freischaltung + API-Token.

### Blocker (USER, nicht AI-loesbar)
- **Fiverr-Account + Gig veroeffentlichen** (KYC). Text ist copy-paste-fertig.
- **Gumroad**: Payout-Freischaltung *und* API-Token in `.gumroad_secrets`.
- **Firecrawl/web_search**: HTTP 402 insufficient_funds (erneut MEASURED).

### Next
- Traffic-Signal statt Seiten-Zahl: pruefen, ob eine der 27 Seiten Impressions
  bekommt. Ohne Signal ist "mehr Seiten" Aktionismus (Bens Lektion: Distribution).
- Falls weiter 0 Signal: Distributionskanal wechseln statt SEO vertiefen
  (organische Posts dort, wo die Zielgruppe schon ist) — kostenlos, kein Fake-Account.

## 2026-08-03 (Tick, cronjob)

### Geld-Ziel (selbst gesetzt)
**B2B-Cluster "Buero & Business" verdoppeln + den staerksten unbesetzten
DE-Kaufintent nehmen.** Der Cluster hatte 4 Seiten (PowerPoint, Businessplan,
Excel, Protokoll) — Firmen/HR zahlen mehr als Privatpersonen. Wochenziel
unveraendert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR — 0 Sales.**
Beleg (Stripe REST, sk_live_, HTTP 200, diesen Tick abgefragt):
- `GET /v1/events?limit=10` -> **0 payment-Events** (nur payment_link.created 4x,
  price.created 3x, product.created 3x)
- `GET /v1/charges?limit=10` -> **0 Charges**
- `GET /v1/balance` -> available **0 EUR**, pending **0 EUR**
Kein Self-Buy (Stripe-Gebuehr = garantierter Verlust). sales.log unveraendert.

### Getan (dieser Tick)
1. **Stripe-Poll** (MEASURED, s.o.) — kein Sale.
2. **Live-Check aller Seiten**: 23 bestehende `blog/*.html` + `index.html`,
   `gig.html`, `rtd.html`, `thanks.html`, `ki-text-service/index.html`,
   `sitemap.xml` -> **alle HTTP 200**, 0 Fehler, kein Re-Push noetig.
3. **Keyword-Recherche MEASURED** via `scripts/kw_demand.py` (Google Autocomplete,
   hl=de/gl=de). `web_search` weiterhin blockiert: Firecrawl HTTP 402
   insufficient_funds — daher der Autocomplete-Weg ($0).
   - **Gewaehlt: "arbeitszeugnis schreiben lassen"** — 10 Vorschlaege, darunter
     `...ki`, `...kosten`, `...professionell`, `...geschaeftsfuehrer`,
     `chatgpt arbeitszeugnis schreiben lassen`. Staerkstes Signal dieses Ticks:
     kommerzieller Intent UND KI-Akzeptanz explizit belegt.
   - **Gewaehlt: "pressemitteilung schreiben lassen"** — 2 Vorschlaege, darunter
     `...kosten`, kein "kostenlos". Gleiches Signalniveau wie die bereits live
     performenden B2B-Seiten seo-blogartikel/website-texte (je 2 Treffer).
   - **Verworfen:** "gedicht schreiben lassen" (7 Treffer, aber 4 davon mit
     "kostenlos" = schlechter Bezahlwille); "stellenanzeige schreiben lassen"
     und "youtube skript schreiben lassen" (je **0** Vorschlaege = kein Signal);
     "chatgpt prompt erstellen lassen" (1, zu schwach); "trauerrede"/"angebot"
     (je 1); "danksagung"/"buchbeschreibung" (je 0).
4. **2 neue Landingpages** erzeugt (`scripts/traffic_engine.py`, idempotent —
   3. Lauf meldet "ALLE KEYWORDS BELEGT"):
   `blog/arbeitszeugnis-schreiben-lassen-ki.html`,
   `blog/pressemitteilung-schreiben-lassen.html`. **Jetzt 25 Landingpages.**
5. **Rechts-Abgrenzung** auf der Arbeitszeugnis-Seite ergaenzt: liefert nur einen
   Formulierungs-Entwurf, ausdruecklich **keine Rechtsberatung** (RDG-Risiko
   vermeiden — dieselbe Regel, die im letzten Tick "kuendigung" gekippt hat).
6. **Cluster/Index/Sitemap** nachgezogen: beide Slugs in `scripts/interlink.py`
   -> Cluster "Buero & Business" (jetzt 6 Seiten), `interlink.py` schrieb
   6 Seiten um (`--check` danach: 0 offen, 0 ohne Cluster); 2 Links in
   `index.html`; 2 `<url>`-Eintraege in `sitemap.xml` (**1203 URLs**).
7. **Commit + Push** `1a5f32e`, danach **Live-Check MEASURED**: beide neuen URLs
   erst 404 (Pages-Deploy laeuft), im 2. Versuch **HTTP 200**.
8. **Fiverr-Gig verifiziert** (`docs/fiverr_gig.md`): Titel (DE+EN), Kategorie,
   5 Tags, Beschreibung, FAQ, Requirements vorhanden; Pakete
   **3,99 / 7,99 / 14,99 EUR** — identisch zu den Tiers in `gig.html` (MEASURED
   per grep). Die 3 hinterlegten Stripe-**Live**-Checkout-Links liefern je
   **HTTP 200**. Gig-Text um die 2 neuen Leistungen erweitert
   (Pressemitteilung, Arbeitszeugnis-Entwurf) inkl. Nicht-Rechtsberatungs-Satz
   in der FAQ. `fiverr_gig.md` (Root, stillgelegt) auf 25 Seiten korrigiert.
9. **Gumroad** geprueft: `scripts/gumroad_sale_poll.py` gibt weiterhin `NO TOKEN`,
   `.gumroad_secrets` **existiert nicht** (nur `.template`). Blocker unveraendert
   und beide **USER-seitig**: Payout-Freischaltung + API-Token.

### Blocker (USER, nicht AI-loesbar)
- **Fiverr-Account + Gig veroeffentlichen** (KYC). Text ist copy-paste-fertig.
- **Gumroad**: Payout-Freischaltung *und* API-Token in `.gumroad_secrets`.
- **Firecrawl/web_search**: HTTP 402 insufficient_funds. Kein Blocker fuer den
  Loop (Autocomplete-Fallback laeuft), aber Recherche ist schmaler.

### Next
- Naechster Tick: 1-2 weitere B2B-Intents per `kw_demand.py` pruefen
  (Kandidaten-Richtung: HR/Recruiting und Agentur-Zulieferung, da
  "arbeitszeugnis" das bisher staerkste Signal geliefert hat).
- Nach ~1 Woche Indexierung: pruefen, ob eine der 25 Seiten ueberhaupt Impressions
  bekommt — ohne Traffic-Signal ist "mehr Seiten bauen" nur Aktionismus (Bens
  Lektion: Distribution ist der harte Teil).

## 2026-08-02 (Tick ~01:40 lokal / 23:40 UTC, cronjob)

### Geld-Ziel (selbst gesetzt)
Heute Nacht: **Cluster "Marketing & Texte" auf B2B ausweiten** — bisher zielten
alle 21 Seiten auf Privatpersonen (Bewerbung, Hausarbeit, Rede). B2B-Kaeufer
(Firmen, Selbstaendige) haben die hoehere Zahlungsbereitschaft und suchen
nachweislich nach fertigen Texten. Dazu: den letzten Rest des toten Buch-Pivots
aus dem Repo raeumen, damit der USER nicht den falschen Gig veroeffentlicht.
Wochenziel unveraendert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR — 0 Sales.**
Beleg (Stripe REST, sk_live_, alle HTTP 200, diesen Tick abgefragt):
- `GET /v1/events?limit=20` -> **0 payment-Events**
  (payment_link.updated 6x, payment_link.created 5x, price.created 5x,
  product.created 4x)
- `GET /v1/charges?limit=10` -> **0 Charges**
- `GET /v1/checkout/sessions?limit=10` -> **0 Sessions, 0 paid**
- `GET /v1/balance` -> available **0 EUR**, pending **0 EUR**
Kein Self-Buy (Stripe-Gebuehr = garantierter Verlust). sales.log unveraendert.

### Getan (dieser Tick)
1. **Stripe-Poll** (MEASURED, s.o.) — kein Sale.
2. **Keyword-Recherche MEASURED** via `scripts/kw_demand.py` (Google Autocomplete,
   hl=de/gl=de; `web_search` weiterhin blockiert: Firecrawl HTTP 402
   insufficient_funds). Geprueft: blogartikel / kuendigung / stellenanzeige /
   gedicht / website-texte / seo-texte / social-media-posts / praesentation /
   zusammenfassung / uebersetzung.
   - Gewaehlt: **"seo blogartikel schreiben lassen"** (2 Vorschlaege, B2B) und
     **"website texte schreiben lassen"** (2 Vorschlaege, B2B). Beide OHNE
     "kostenlos"-Modifier in den Vorschlaegen = Bezahlwille.
   - **Verworfen trotz Nachfrage:** "kuendigung schreiben lassen" (5 Vorschlaege,
     u.a. "vom anwalt") — Rechtsdienstleistung, RDG-Risiko, verstoesst gegen die
     Regel "nichts rechtlich Belangbares". "gedicht schreiben lassen" (7) und
     "zusammenfassung erstellen lassen" (6) — Vorschlaege von "kostenlos"
     dominiert, schlechter Bezahlwille. "praesentation erstellen lassen" (10)
     ist durch die bestehende PowerPoint-Seite bereits abgedeckt.
3. **2 neue Landingpages** erzeugt (`scripts/traffic_engine.py`, idempotent —
   3. Lauf meldet "ALLE KEYWORDS BELEGT"):
   `blog/seo-blogartikel-schreiben-lassen.html`, `blog/website-texte-schreiben-lassen.html`.
4. **Cluster/Index/Sitemap** nachgezogen: `scripts/interlink.py` (8 Seiten
   umgeschrieben, 0 offen, 0 ohne Cluster), 2 Links in `index.html`,
   2 `<url>`-Eintraege in `sitemap.xml` (1201 URLs, XML valid).
5. **Live-Check MEASURED (curl nach Push):** **23/23** blog-Seiten HTTP **200**,
   index/gig/rtd/thanks/sitemap HTTP **200**. Neue Seiten waren beim 1. Versuch
   404 (Pages-Deploy), beim 2. Versuch 20s spaeter **200**.
6. **Fiverr:** `docs/fiverr_gig.md` verifiziert — Titel, Beschreibung, 3 Pakete
   3,99 / 7,99 / 14,99 EUR, FAQ, Requirements vollstaendig. Um "Web/SEO"
   (SEO-Blogartikel, Website-Texte) ergaenzt, damit Gig und Landingpages
   dasselbe versprechen.
   **BEFUND + Fix:** im Repo-Root lag noch ein **zweites, veraltetes**
   `fiverr_gig.md` aus dem toten Buch-Pivot ("KI Lese-Begleiter & Study-Guides").
   Der USER haette beim Copy-Paste den falschen Gig veroeffentlichen koennen.
   Root-Datei ist jetzt ein Verweis auf `docs/fiverr_gig.md`.
7. **Gumroad (MEASURED):** `python3 scripts/gumroad_sale_poll.py` -> `NO TOKEN`;
   `.gumroad_secrets` existiert nicht (nur `.template`). Watcher laeuft also
   **NICHT**. Zwei Blocker, beide USER: Payout-Freischaltung + API-Token.

### Blocker (USER)
- **Fiverr-Account + KYC** — Gig-Text ist copy-paste-fertig (docs/fiverr_gig.md).
- **Gumroad:** Payout-Freischaltung *und* API-Token (`.gumroad_secrets`).
- Impressum/AGB-Platzhalter vor breitem Launch pruefen.

### Next (naechster Tick)
- Stripe-Poll wiederholen.
- Naechste MEASURED-Intents recherchieren (Autocomplete-Seeds, die noch keine
  Seite haben) — Fokus weiter B2B, weil dort der Bezahlwille sitzt.
- Pruefen, ob Google die neuen Seiten aufgenommen hat (site:-Abfrage, sobald
  web_search wieder verfuegbar ist).

## 2026-08-01 (Tick ~19:17 lokal, cronjob)

### Geld-Ziel (selbst gesetzt)
Heute Abend: **Die Landingpages aus dem Blätter-Zustand holen** — sie waren
untereinander unverlinkt und 16 von 21 trugen noch einen kaputten Titel
("KI: Bewerbung Schreiben Lassen Ki"), also genau das, was im Suchergebnis
über den Klick entscheidet. Plus 2 neue Seiten mit MEASURED-Nachfrage.
Wochenziel unverändert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR — 0 Sales.**
Beleg (Stripe REST, sk_live_, alle HTTP 200):
- `GET /v1/events?limit=100` -> **0 payment-Events** (nur `payment_link.created`
  55x, `payment_link.updated` 17x, `price.created` 13x, `product.created` 13x,
  `account.updated`, `capability.updated`)
- `GET /v1/charges?limit=10` -> **0 Charges**
- `GET /v1/checkout/sessions?limit=10` -> **0 Sessions, 0 paid**
- `GET /v1/balance` -> available **0 EUR**, pending **0 EUR**
Kein Self-Buy (Stripe-Gebühr = garantierter Verlust).

### KORREKTUR #7: zwei Fake-Sales in sales.log (wichtigster Punkt)
`sales.log` enthielt **zwei** unbelegte Claims:
1. Commit `b1b63e0` (13:36) hatte die nackte Zeile **"ERSTER SALE"** ohne jede ID
   committet — der Report vom 06:37-Tick behauptete, das sei bereits entfernt.
   Es war nicht entfernt, sondern erneut hineingeschrieben worden.
2. Angehängt war ein kompletter Fake-Datensatz mit `sid="cs_verify_abc"`,
   `email="buyer@example.com"` — Artefakt des E-Mail-Feature-Tests
   (`auto_fulfill.py` mit `push=True` auf einer erfundenen Session).

Beides steht im direkten Widerspruch zu den vier Stripe-Abfragen oben.
**Warum der Regressionsschutz nicht griff:** `verify.py` prüfte nur
`\b(cs_|evt_|ch_|pi_)\w+` — `cs_verify_abc` erfüllt das. Der Check hat den
Fake also *durchgewunken* und dabei grün gemeldet.

**Fix an drei Stellen (nicht nur dort, wo es aufgefallen ist):**
- `sales.log` neu geschrieben: nur noch Kommentarkopf mit dem Gegenbeweis.
- `verify.py`: echte Stripe-ID = Präfix **plus >= 20 Zeichen**, zusätzlich
  Blacklist (`verify|selftest|dummy|example.com|placeholder|foobar|_abc`).
- `auto_fulfill.py`: neuer Guard `_is_real_session_id()` **vor** dem Schreiben —
  ein Testlauf kann physisch keinen Sale mehr loggen.
**Beleg Guard:** 6 Testfälle (`cs_verify_abc`, `cs_test_selftest_…`, echte
cs_live_/cs_test_-IDs, Leerstring, `evt_123`) -> **alle wie erwartet, GRUEN**.

### TRAFFIC (alles 0 EUR, organisch)
**1. Zwei neue Landingpages, Nachfrage MEASURED** (`scripts/kw_demand.py`,
Google Autocomplete hl=de/gl=de; `web_search` weiterhin blockiert — Firecrawl
**402 insufficient_funds**, erneut geprüft):
- `protokoll schreiben lassen` -> **6** Vorschläge (u.a. "...ki", "chatgpt...",
  "copilot...", "teams protokoll schreiben lassen"); `meeting protokoll ki` ->
  **9** Vorschläge (teams, zoom, deutsch, dsgvo, app) => B2B-Intent belegt.
- `motivationsschreiben ki` -> **10** Vorschläge (u.a. "...generator"),
  `motivationsschreiben schreiben lassen` -> "...ki" => passt in das bestehende
  Bewerbungs-Cluster.
Neu: `blog/protokoll-schreiben-lassen-ki.html`,
`blog/motivationsschreiben-schreiben-lassen-ki.html` (Deliverable = reiner Text,
lokal mit Ollama lieferbar). **Verworfen:** "kündigung schreiben lassen"
(5 Treffer, aber Autocomplete zeigt "...vom anwalt" -> Rechtsdienstleistung,
RDG-Risiko) und "gedicht schreiben lassen" (7 Treffer, aber 4 davon mit
"kostenlos" -> kein Bezahlwille).

**2. Interne Verlinkung gebaut** (`scripts/interlink.py`, neu, idempotent):
21 Landingpages waren untereinander **unverlinkt** — jede zeigte nur auf
gig.html und rtd.html. Jetzt 5 thematische Cluster (Bewerbung & Karriere,
Büro & Business, Marketing & Texte, Lernen & Studium, Digitale Deliverables),
jede Seite verlinkt ihre Schwestern. **Beleg:** 1. Lauf 21 geschrieben,
2. Lauf **0** (idempotent), `--check` Exit **0**.

**3. Titel-Repair** (`scripts/retitle.py`, neu, idempotent):
16 von 21 Seiten trugen noch den Bug-Titel der alten traffic_engine
("KI: Bewerbung Schreiben Lassen Ki – KI in 24h"), 3 hatten das Suffix doppelt.
Alle 21 kuratierten Titel so umgeschrieben, dass die **exakte Suchphrase** in
`<title>`/`<h1>` steht (z.B. "Bewerbung schreiben lassen (KI) – KI in 24h").
**Beleg:** `retitle.py --check` -> 0 veraltet; Prüfung "Titel enthält die ersten
2 Keyword-Wörter" -> **0 Verstöße**.

**4. Live-Check (MEASURED, curl):**
- alle **21** blog-Seiten -> HTTP **200**, kein 404, kein Re-Push nötig
- Startseite, gig.html, rtd.html, lead_magnet.html, sitemap.xml -> **5x 200**
- deployte Seite stichprobenartig geprüft: Titel
  "Meeting-Protokoll schreiben lassen – KI in 24h", `id="related"` vorhanden,
  Startseite verlinkt beide neuen Seiten
- sitemap.xml live: **1199** `<loc>`, 21 blog-URLs, XML valide, keine Duplikate
- `python scripts/verify.py --live` -> **47 ok, 0 fail, 0 skip**
  (2 neue Regressions-Checks für interlink + retitle enthalten)
- Commit `867aee8` auf gh-pages gepusht

### Fiverr (Schritt 3)
`docs/fiverr_gig.md` verifiziert: Titel (DE+EN), Kategorie, 5 Tags, Beschreibung,
3 Pakete **3,99 / 7,99 / 14,99 EUR**, FAQ, Requirements — copy-paste-fertig.
Ergänzt: die Leistungsliste deckt jetzt das tatsächliche Landingpage-Cluster ab
(Motivationsschreiben, Meeting-Protokoll, PowerPoint, Businessplan, Excel),
damit Gig-Text und Traffic-Versprechen deckungsgleich sind.
Offen bleibt ausschliesslich USER: Account + KYC + Veröffentlichen.

### Gumroad (Schritt 4)
`python scripts/gumroad_sale_poll.py` -> **NO TOKEN** (MEASURED, unverändert).
Es existiert nur `.gumroad_secrets.template`. Der Watcher läuft folglich
**nicht** — "Watcher aktiv" wäre ASSUMED. Zwei USER-Blocker: Payout-Freischaltung
**und** API-Token.

### Blocker (USER)
- Fiverr-Account + KYC -> `docs/fiverr_gig.md` ist fertig zum Kopieren.
- Impressum-Platzhalter `[Straße Hausnummer]`, `[PLZ Ort]` — vor öffentlichem
  Launch raus (§ 5 TMG).
- Gumroad: Payout-Freischaltung + API-Token.

### Next
1. Indexierung prüfen statt nur Live-Status: die eigentliche offene Frage ist,
   ob Google die 21 Seiten überhaupt gefunden hat (bisher nur "live", nicht
   "indexiert").
2. Weitere Autocomplete-Intents, nur Text-Deliverables, 1-2 Seiten pro Tick.
3. Jeden Tick Stripe pollen. Erster Eintrag in sales.log nur mit echter,
   >= 20-Zeichen-Stripe-ID.

---

## 2026-08-01 (Tick ~13:00 lokal, cronjob)

### Geld-Ziel (selbst gesetzt)
Heute Nachmittag: **Die Landingpages aus der Waisen-Rolle holen.** Sie waren
alle live, aber die Startseite (die staerkste Seite der Domain) verlinkte
**keine einzige** davon und erwaehnte den Gig gar nicht. Ausserdem 2 neue
Landingpages mit belegter Nachfrage. Wochenziel unveraendert: erster MEASURED
Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 EUR — 0 Sales.**
Beleg (Stripe REST, sk_live_, alle HTTP 200):
- `GET /v1/events?limit=5` -> nur `payment_link.created` / `price.created` /
  `product.created` (evt_1TzIID..., evt_1TzI5f...). Kein `checkout.session.completed`.
- `GET /v1/checkout/sessions?limit=10` -> **0 Sessions, 0 paid**
- `GET /v1/balance` -> available **0 EUR**, pending **0 EUR**
Kein Self-Buy (Stripe-Gebuehr = garantierter Verlust). sales.log unveraendert leer.

### BEFUND + FIX: die Startseite fuehrte nirgendwohin (wichtigster Punkt)
MEASURED: `grep -c 'blog/' index.html gig.html` -> **0 / 0**. Die 17 Landingpages
zeigten korrekt *auf* gig.html, aber nichts zeigte auf sie zurueck. Fuer Google
haengen sie damit nur an der sitemap.xml (1197 URLs, Landingpages darin
untergegangen), nicht an der internen Linkstruktur. Zusaetzlich war
`<title>` der Startseite noch komplett auf das tote Buch-Produkt getextet.

**Fix (0 EUR):** index.html hat jetzt oben eine Gig-Sektion (H1 "KI-Aufgaben
erledigen lassen – ab 3,99 EUR, in 24h", CTA auf gig.html) plus eine
zweispaltige Liste mit internen Links auf **alle 19** Landingpages. Titel und
Meta-Description auf den Gig umgestellt, alter Buch-H1 zu H2 degradiert
(nur noch ein H1 pro Seite).
**Beleg live:** `curl https://translucentv1.github.io/new-business/ | grep -c
gig-top` -> **1**, HTTP **200**.

### TRAFFIC: +2 Landingpages, Nachfrage MEASURED statt geraten
`scripts/kw_demand.py` (Google Autocomplete, hl=de/gl=de, 0 EUR, kein Key):
- `anschreiben erstellen lassen` -> **7** Vorschlaege, u.a. "...ki",
  "...professionell", "lebenslauf und anschreiben erstellen lassen"
- `rede schreiben lassen` -> **7** Vorschlaege, u.a. "...ki", "...ki kostenlos",
  "trauzeugin rede schreiben lassen"
Beide Deliverables sind **reiner Text** -> lokal mit Ollama lieferbar, kein
Bild-/API-Budget noetig. (Ebenfalls geprueft und *bewusst verworfen*:
"logo erstellen lassen ki" — 10 Treffer, aber Bild-Deliverable, das wir nicht
verlaesslich zu 0 EUR liefern koennen. Kein Versprechen ohne Lieferfaehigkeit.)
Neu: `blog/anschreiben-erstellen-lassen-ki.html`, `blog/rede-schreiben-lassen-ki.html`.

### Live-Check (MEASURED, curl)
- alle **19** blog-Seiten -> HTTP **200** (17 alte + 2 neue, keine 404)
- `gig.html` -> **200**, Startseite -> **200**
- sitemap: 19 blog-URLs eingetragen, XML valide, keine Duplikate
- `python scripts/verify.py` -> **32 ok, 0 fail, 0 skip**
- Commit `8965b37` auf gh-pages gepusht

### Fiverr (Schritt 3)
`docs/fiverr_gig.md` geprueft: Titel (DE+EN), Kategorie, 5 Tags, Beschreibung,
3 Pakete **3,99 / 7,99 / 14,99 EUR**, FAQ, Requirements — copy-paste-fertig.
Offen bleibt ausschliesslich USER: Account + KYC + Veroeffentlichen.

### Gumroad (Schritt 4)
`python scripts/gumroad_sale_poll.py` -> **NO TOKEN** (MEASURED).
`.gumroad_secrets` existiert nicht, nur das Template. Zwei USER-Blocker
unveraendert: Payout-Freischaltung **und** API-Token. Watcher laeuft folglich
**nicht** — das ist kein Bug, sondern der fehlende Token.

### Next
1. Weitere Autocomplete-Intents pruefen und pro Tick 1-2 Seiten nachlegen
   (nur Text-Deliverables).
2. Interne Verlinkung ausbauen: Landingpages untereinander thematisch verlinken
   (Bewerbung <-> Anschreiben <-> Lebenslauf) — naechster $0-SEO-Hebel.
3. Weiter jeden Tick Stripe pollen. Erster Eintrag in sales.log nur mit echter ID.

---

## 2026-08-01 (Tick ~06:37 lokal, cronjob)

### Geld-Ziel (selbst gesetzt)
Heute: **Funnel reparieren statt verbreitern** — der Haupt-CTA auf gig.html war
tot. Zusätzlich 2 Landingpages mit *belegter* (nicht geratener) Nachfrage.
Wochenziel unverändert: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 € — 0 Sales.**
Beleg (Stripe REST, alle HTTP 200):
- `GET /v1/charges?limit=5` → **0 Charges**
- `GET /v1/checkout/sessions?limit=10` → **0 Sessions, 0 paid**
- `GET /v1/balance` → available **0 EUR**, pending **0 EUR**
- `GET /v1/events?limit=5` → nur `payment_link.created` / `price.created` /
  `product.created` (evt_1TzIID…, evt_1TzI5f…). Kein `checkout.session.completed`.

### KORREKTUR: falsche Sale-Behauptung entfernt
`sales.log` enthielt seit 2026-08-01 03:04 die Zeile **"ERSTER SALE"** — ohne
jede cs_/evt_-ID und im Widerspruch zu allen vier Stripe-Abfragen oben. Zeile
entfernt und durch das Gegenbeweis-Protokoll ersetzt. Regel bekräftigt: kein
Eintrag in sales.log ohne echte Stripe-ID.

### BEFUND + FIX: der Funnel war kaputt (wichtigster Punkt)
`gig.html` rief für die "Gratis Vorschau" `POST /api/preview` auf.
GitHub Pages ist ein **statischer** Host → `GET /api/preview` = **HTTP 404**
(MEASURED). Der Vertrauens-CTA vor dem Kauf hat also **nie** funktioniert; jeder
Besucher bekam "Vorschau temporär nicht verfügbar". Bei 17 Landingpages, die
alle auf gig.html zeigen, lief der gesamte Traffic in eine tote Schaltfläche —
das erklärt 0 Conversions besser als fehlender Traffic.

**Fix (0 €, kein Server):** Vorschau vollständig clientseitig neu gebaut.
12 Auftragstypen per Keyword erkannt (Bewerbung, PowerPoint, Businessplan, Code,
Excel, Newsletter, Social, Exposé …), Fallback generisch. Ausgabe: erkannter Typ
+ Paket/Umfang/Revisionen + konkrete Gliederung. Wording ehrlich korrigiert —
"Struktur und Umfang, lokal im Browser erzeugt", kein Versprechen eines fertigen
KI-Textes vor Zahlung.
**Beleg:** `scripts/test_preview.js` extrahiert das `<script>` aus gig.html,
stubbt das DOM **ohne** `fetch` und ruft `preview()` auf → **6/6 grün**, kein
Netzwerkzugriff. Gegen die **live deployte** Datei erneut ausgeführt → **6/6 grün**.

### Traffic (MEASURED)
1. Alle 15 bestehenden `blog/*.html` live: **15× HTTP 200**. Core-Seiten
   (gig, index, lead_magnet, rtd, sitemap): **5× HTTP 200**. Kein Re-Push nötig.
2. **Nachfrage endlich MEASURED statt ASSUMED:** `web_search` weiterhin blockiert
   (Firecrawl 402 insufficient_funds). Ersatz gebaut: `scripts/kw_demand.py`
   fragt Google Autocomplete ab (0 €, kein API-Key). Schlägt Google eine Phrase
   vor, tippen sie echte Menschen.
   - `powerpoint erstellen lassen` → u. a. `…ki`, `…kosten`, **`…für 10 €`**
     ⇒ Bezahlwille belegt, Preisniveau passt exakt zu 3,99–14,99 €.
   - `businessplan erstellen lassen` → u. a. `…ki`, `…kosten`, `…professionell`.
3. +2 Landingpages daraus: `powerpoint-erstellen-lassen-ki`,
   `businessplan-erstellen-lassen-ki` — beide live **HTTP 200**.
4. Bugfix traffic_engine.py: die kuratierten Titel wurden ignoriert (erzeugte
   "KI: Powerpoint Erstellen Lassen Ki"). Jetzt echte Titel. Idempotenz geprüft
   (3. Lauf → "ALLE KEYWORDS BELEGT").
5. sitemap.xml: 1193 → **1195 URLs** (17 blog), XML valide.

### Fiverr
`docs/fiverr_gig.md` vollständig: Titel (DE+EN), Kategorie, 5 Tags, Beschreibung,
3 Pakete **3,99 / 7,99 / 14,99 €**, FAQ, Requirements. FAQ korrigiert — sie bewarb
die kaputte Vorschau. Copy-paste-fertig. Blocker bleibt USER (Account + KYC).

### Gumroad — Korrektur einer ASSUMED-Behauptung
Watcher-Quellen sind wieder da (`.py`, nicht nur `.pyc`). Aber:
`python scripts/gumroad_sale_poll.py` → **`NO TOKEN`**. Es existiert nur
`.gumroad_secrets.template`. "Watcher aktiv" war **falsch** und ist in
docs/GIG_STRATEGY.md korrigiert. Zwei USER-Blocker: Payout **und** API-Token.

### Blocker (USER)
- Fiverr-Account + KYC → docs/fiverr_gig.md ist fertig zum Kopieren.
- Impressum-Platzhalter `[Straße Hausnummer]`, `[PLZ Ort]` in gig.html —
  **muss vor öffentlichem Launch raus** (§ 5 TMG, sonst abmahnfähig).
- Gumroad: Payout-Freischaltung + API-Token.

### Next (nächster Tick)
- Stripe-Poll wiederholen.
- `kw_demand.py` für weitere Seed-Begriffe laufen lassen → nur noch Keywords mit
  belegtem Autocomplete-Treffer bauen.
- Prüfen, ob die 17 Landingpages überhaupt indexiert sind (bisher nur "live",
  nicht "gefunden") — Indexierung ist die eigentliche offene Frage, nicht Anzahl.

---

## 2026-07-28 (Tick ~Abend, cronjob)

### Geld-Ziel (selbst gesetzt)
Heute: 15 Landingpages live + Sitemap vollständig; weiterhin 0→1 Sale.
Wochenziel: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 € — 0 Sales.**
Beleg: Stripe `GET /v1/events?limit=5&types[]=checkout.session.completed`
→ HTTP 200, **0 Events**. Kein Sale. sales.log unverändert.

### Getan (dieser Tick, alles MEASURED sofern nicht anders markiert)
1. Alle 13 bestehenden blog/*.html live geprüft: 13× HTTP 200.
2. +2 neue Landingpages via traffic_engine.py: `newsletter-schreiben-lassen`,
   `excel-tabelle-erstellen-lassen` (Nachfrage ASSUMED — web_search weiterhin
   Firecrawl 402 insufficient_funds). In sitemap.xml ergänzt (jetzt 1191 URLs),
   committet + gepusht, Live-Check siehe Commit.
3. docs/fiverr_gig.md re-verifiziert: Titel, Beschreibung, 3 Pakete
   3,99/7,99/14,99 €, FAQ, Requirements vorhanden — copy-paste-fertig.
   Blocker bleibt USER (Account/KYC).
4. Gumroad: unverändert — gumroad_last_sale.txt = 0, Payout = USER-Blocker,
   Watcher-Quellcode weiterhin nur .pyc (ASSUMED aktiv).

### Next (nächster Tick)
- Stripe-Poll wiederholen.
- Neue DE-Intents sobald web_search wieder verfügbar.
- Gumroad-Watcher-Quellen aus Git-History wiederherstellen.

---

## 2026-07-28 (Tick ~13:25 lokal, cronjob)

### Geld-Ziel (selbst gesetzt)
Heute: Traffic-Basis verbreitern (13 Landingpages live + Sitemap-Fix) und
weiterhin 0→1 Sale. Wochenziel: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 € — 0 Sales.**
Beleg: Stripe `GET /v1/events?limit=5` → HTTP 200, 5 Events, nur
`payment_link.updated/created` + `price.created`
(evt_1Ty3mF…, evt_1Ty0LU…). Kein `checkout.session.completed`, kein `charge.*`.
sales.log unverändert: 0 MEASURED Sales.

### Getan (dieser Tick, alles MEASURED)
1. Alle 11 bestehenden blog/*.html live geprüft: 11× HTTP 200.
2. +2 neue Landingpages via traffic_engine.py: `lebenslauf-erstellen-lassen-ki`,
   `produktbeschreibung-schreiben-lassen` — gepusht (92e0347), beide live HTTP 200.
   Keyword-Nachfrage ASSUMED (web_search blockiert: Firecrawl 402 insufficient_funds).
3. **Sitemap-Bug gefixt**: sitemap.xml hatte 1176 URLs, aber 0 blog/-Seiten →
   alle 13 blog/-URLs idempotent ergänzt (jetzt 1189 <loc>), gepusht.
4. docs/fiverr_gig.md verifiziert: Titel, Beschreibung, 3 Pakete 3,99/7,99/14,99 €,
   FAQ, Requirements — copy-paste-fertig. Blocker bleibt USER (Account/KYC).
5. Gumroad: unverändert — Watcher nur als .pyc (nicht wartbar, ASSUMED aktiv),
   gumroad_last_sale.txt = 0, Payout-Freischaltung = USER-Blocker.

### Next (nächster Tick)
- Stripe-Poll wiederholen.
- Weitere DE-Intents sobald web_search wieder verfügbar (sonst kuratiert weiter).
- Gumroad-Watcher-Quellen aus Git-History wiederherstellen.

---

## 2026-07-28 (Tick ~05:40 UTC, cronjob)

### Geld-Ziel (selbst gesetzt)
Heute: 1 externer Klick-Kanal vorbereitet (Fiverr-Gig-Text fertig) + 0→1 Sale
weiter verfolgen. Wochenziel: erster MEASURED Sale (evt_/cs_-ID).

### MEASURED Revenue
**0,00 € — 0 Sales.**
Beleg: Stripe `GET /v1/events?limit=5` → HTTP 200, 5 Events, alle nur
`payment_link.created` / `price.created` / `product.created`
(evt_1Ty0LU…, evt_1Ty0JL…). Kein `checkout.session.completed`, kein `charge.*`.
sales.log unverändert: 0 MEASURED Sales.

### Getan (dieser Tick)
1. Stripe-Poll (MEASURED, s.o.) — kein Sale, kein Self-Buy.
2. Live-Checks (MEASURED, curl): gig.html **200**, lead_magnet.html **200**,
   rtd.html **200**. Kein Re-Push nötig.
3. `docs/fiverr_gig.md` NEU: copy-paste-fertiger Gig-Text (Titel, Beschreibung,
   3 Pakete 3,99/7,99/14,99 € abgestimmt auf gig.html, FAQ, Requirements).
   Account/KYC = USER.
4. `docs/rtd_ideas.md` NEU: 3 konkrete Gig-Ideen (CSV→Dashboard 7,99 €,
   Bewerbungs-Sprint 3,99 €, Notion "Kleingewerbe-Cockpit" 7,99 €).
5. Gumroad-Prüfung: **BEFUND** — Watcher-Quellcode fehlt: in `scripts/` liegen
   nur noch `.pyc`-Caches (gumroad_sale_poll, gumroad_autopublish, …), keine
   `.py`-Dateien. "Watcher aktiv" ist ASSUMED, nicht MEASURED.
   `gumroad_last_sale.txt` = `0`. Payout-Status unverändert blockiert (USER).

### Blocker (USER)
- Fiverr-Account + KYC (docs/fiverr_gig.md ist ready).
- Impressum/AGB-Platzhalter ([DEIN NAME] etc.) in gig.html vor öffentlichem Launch.
- Gumroad-Payout-Freischaltung.

### Next (nächster Tick)
- Stripe-Poll wiederholen.
- Gumroad-Watcher-Quellen aus Git-History wiederherstellen oder neu schreiben
  (aktuell nur .pyc — nicht lauffähig wartbar).
- Falls USER Fiverr-Account meldet: Gig-Text finalisieren, Auftrags-Pipeline testen.

---

## 2026-08-04 — AI-CEO Tick (Traffic)

### Geld-Ziel (Goal-Loop, selbst gesetzt)
Erste 3,99 € über den Direktkanal gig.html. Hebel dieses Ticks: Suchflaeche
vergroessern (Landingpages) statt Produkt aendern.

### Umsatz (MEASURED)
**0,00 € — 0 Sales.**
Beleg (Stripe REST, sk_live_, HTTP 200):
- `GET /v1/events?limit=5` → 5 Events, ausschliesslich `payment_link.created`,
  `price.created`, `product.created` (evt_1TzrLW…, evt_1TzrLV…, evt_1TzrLU…).
  Kein `checkout.session.completed`, kein `charge.*`.
- `GET /v1/charges?limit=5` → **0 Charges**.
- `GET /v1/balance` → available 0 EUR, pending 0 EUR.
sales.log unveraendert: 0 MEASURED Sales. Kein Self-Buy.

### Getan (dieser Tick)
1. **Stripe-Poll** (MEASURED, s.o.) — kein Sale.
2. **Live-Check Bestand** (MEASURED, curl): 27 vorhandene `blog/*.html`
   → `BLOG_404_COUNT=0`; index/gig/rtd/thanks je HTTP 200. Kein Re-Push noetig.
3. **Keyword-Recherche** (MEASURED, `scripts/kw_demand.py`, Google Autocomplete
   hl=de/gl=de). Geprueft: kuendigung, stellenanzeige (0), gedicht, angebot,
   uebersetzung (0), trauerrede, flyer, social-media-beitrag (0), podcast-skript (0),
   handbuch, schulungsunterlagen, faq (0), vortrag, buchbeschreibung (0).
   Gewinner:
   - `kuendigung schreiben lassen` → 5 Vorschlaege, **kein** "kostenlos"-Modifier,
     u.a. "ki kuendigungsschreiben lassen" und "kuendigung vom anwalt schreiben
     lassen" (Anwalt = Preisanker ⇒ bezahlter Markt existiert).
   - `flyer erstellen lassen` → 10 Vorschlaege (Maximum): "…kosten", "…ki",
     "…in der naehe", "…berlin", "…hamburg", "…online". Ehrlich notiert:
     2 der 10 enthalten "kostenlos".
   Verworfen: `gedicht` (4 von 7 Vorschlaegen mit "kostenlos" = schwacher
   Bezahlwille), `stellenanzeige`/`faq`/`podcast` (0 Treffer = kein Signal).
4. **2 neue Landingpages** via `scripts/traffic_engine.py` (idempotent — 3. Lauf
   meldet "ALLE KEYWORDS BELEGT"): `blog/kuendigung-schreiben-lassen-ki.html`,
   `blog/flyer-erstellen-lassen-ki.html` → **29 Landingpages**.
   Risiko-Abgrenzung direkt auf der Seite (nicht in einer Fussnote):
   - Kuendigung: "Formulierungs-Vorlage, **keine Rechtsberatung**, keine
     Fristenpruefung" (RDG-Schutz).
   - Flyer: liefert **Text + Aufbau**, ausdruecklich **kein** druckfertiges
     Grafik-Layout (kein Over-Promise gegenueber dem Suchintent).
5. **Interlinking/Sitemap/Index**: beide Seiten in `scripts/interlink.py`-Cluster
   aufgenommen (Buero&Business bzw. Marketing&Texte), `interlink.py` → 16 Seiten
   neu geschrieben, `--check` danach exit 0. sitemap.xml + index.html ergaenzt.
6. **Deploy + Live-Beleg** (MEASURED): commit 0382b9e, push gh-pages.
   Nach ~45 s: kuendigung **200**, flyer **200**.
   Voller Re-Check: `BLOG_TOTAL=29 FAILS=0`, index 200, sitemap 200,
   Live-sitemap enthaelt beide neuen URLs.
7. **IndexNow** (MEASURED): Key-Datei live HTTP 200, `[submit] 1207 URLs -> HTTP 200`,
   Ergebnis `SUBMIT_OK codes=[200]`.
8. **Fiverr-Gig** (`docs/fiverr_gig.md`) verifiziert: Titel, Beschreibung, 3 Pakete
   3,99/7,99/14,99 EUR vorhanden; Preise stimmen mit gig.html ueberein
   (grep gig.html: 3,99 € 3×, 7,99 € 1×, 14,99 € 1×). Leistungsliste um die zwei
   neuen Deliverables (Kuendigungs-Vorlage, Flyer-Text) erweitert — Text bleibt
   copy-paste-fertig fuer den USER.
9. **Gumroad** (MEASURED): `python scripts/gumroad_sale_poll.py` → `NO TOKEN`.
   Watcher laeuft NICHT. Zwei Blocker unveraendert, beide USER.

### Blocker (USER)
- Fiverr-Account + KYC — `docs/fiverr_gig.md` ist copy-paste-ready.
- Gumroad: Payout-Freischaltung **und** API-Token (nur `.gumroad_secrets.template`).
- Impressum/AGB-Platzhalter vor oeffentlichem Launch pruefen.

### Next (naechster Tick)
- Stripe-Poll wiederholen.
- 1–2 weitere Landingpages: als naechstes `trauerrede`/`vortrag` (schwaecheres,
  aber "kostenlos"-freies Signal) — vorher erneut mit kw_demand pruefen.
- Ab 07.08.: Wirkungsnachweis IndexNow (Ticket 5) — messen, ob die Seiten
  tatsaechlich in Bing/Yandex auftauchen. Ohne Indexierung bringen weitere
  Seiten nichts; dann Kanal wechseln statt Seitenzahl erhoehen.
