# ADR-0006 — Startpreis: $3,99 fest (kein PWYW) [FINAL, autonom 2026-07-18]

- Kontext: Startpreis muss gesetzt werden. Ziel Nutzer: "schnell kleine Einnahmen,
  bei 0 Invest ist jeder Cent Gewinn". Gumroad-Gebühr = 10% + $0,50 FIX pro
  Transaktion (MEASURED gumroad.com/pricing, 2026-07-18). PWYW-Mindestbetrag wenn
  jemand zahlt = $0,99 (MEASURED gumroad.com/help/article/133). Freie Produkte ($0+)
  = 0% Gebühr, aber niemand zahlt freiwillig bei gratis-verfügbarer PD.
- Gebührenmathematik (MEASURED-Rechnung auf Basis 10%+$0,50):
  - $0,99 -> netto ~$0,39 (39%)
  - $1,99 -> netto ~$1,29 (65%)
  - $2,99 -> netto ~$2,19 (73%)
  - $3,99 -> netto ~$3,09 (77%)
  - $9,99 -> netto ~$8,49 (85%)
  Die $0,50-Fixgebühr dominiert unter ~$3. Ab $3,99 bleibt >3/4 hängen.
- Entscheidung (FINAL, autonom): **$3,99 fester Preis**, KEIN PWYW.
  Begründung: (a) Fixgebühr frisst Kleinstpreise; (b) PWYW bei "woanders gratis"
  konvergiert gegen 0 gezahlt; (c) $3,99 ist Impuls-Schwelle und lässt Marge für
  ADR-0005-Reinvestition. Nutzer-Einwand "60ct=10ct Gewinn" ist mathematisch wahr,
  aber 0 Traffic × jeder Preis = 0 -> Preis ist NICHT der bindende Hebel (siehe ADR-0007).
- Konsequenz: `PD_PRICE_CENTS=399` als Default im Uploader. Preis in einer Konstante,
  jederzeit per Env überschreibbar. Reevaluieren nach ersten MEASURED Verkaufsdaten.
- Belegstatus: Gebühren MEASURED. "Welcher Preis maximiert Umsatz für PD-eBooks" ist
  ASSUMED (keine echten Verkaufsdaten dieser Nische in der Hand) -> A/B nach Go-Live.

# ADR-0007 — Distribution: Traffic ist der bindende Engpass, nicht der Preis [FINAL, autonom 2026-07-18]

- Kontext: Beim Preis-Grilling entdeckt: Gumroad Discover (die einzige eingebaute
  Traffic-Quelle) verlangt VOR Listung: Payout-Settings gefüllt + **$100 Guthaben aus
  echten Verkäufen** (keine Selbstkäufe) + Risk-Review ~3 Wochen + Produkt hat mind.
  1 Verkauf (MEASURED gumroad.com/help/article/79-gumroad-discover, 2026-07-18).
  => Henne-Ei: Discover bringt erst Traffic NACHDEM man schon $100 verkauft hat.
  Gumroad ist ein Checkout-/Hosting-Tool, KEIN Marktplatz mit Laufkundschaft.
- Konsequenz-Erkenntnis: Ein hochgeladenes PD-eBook verkauft 0 Stück ohne externen
  Traffic, egal bei welchem Preis. Der autonome Loop hatte bisher eine Lücke:
  "wie kommen Käufer auf den Link". Legal-Check PD-Verkauf: ERLAUBT (MEASURED
  gumroad.com/prohibited — nur #16 copyrighted / #44 PLR verboten, PD ist keins von beiden).
- Entscheidung (FINAL, autonom): Traffic wird als eigener automatisierbarer Loop-Schritt
  behandelt. Priorisierte kostenlose, legale Kanäle (ASSUMED-Wirksamkeit, per Primärquelle
  noch zu härten):
  1. **SEO-Landingpage** je Produkt (statischer HTML-Export, GitHub Pages = gratis Hosting)
     mit Keyword "<Titel> kostenlos lesen / gratis eBook" -> Long-Tail-Suchtraffic.
  2. **Pinterest** Pins je Titel (gratis, SEO-getrieben, keine Follower nötig — ASSUMED
     stark für digitale Produkte laut mehreren 2025-Quellen).
  3. Reddit/Foren NUR regelkonform (kein Spam) — niedrige Prio wegen ToS-Risiko.
- Konsequenz: Neuer Tracer-Bullet nötig (TB-6: Landingpage-Generator). Ohne diesen ist
  der Upload-Loop technisch fertig, aber wirtschaftlich wirkungslos. Preis-Ticket (TB unten)
  bleibt trivial; Traffic-Ticket ist das eigentliche Wertstück.
- Belegstatus: Discover-Regeln + Legal MEASURED. Kanal-Wirksamkeit ASSUMED -> je Kanal
  mit einem Mini-Experiment (1 Produkt, 1 Kanal) MEASURED validieren, bevor skaliert wird.

# ADR-0008 — Korrektur veralteter MEASURED-Annahmen aus ADR-0002/0004 [FINAL, autonom 2026-07-18]

- Kontext: Beim echten Go-Live-Test entdeckt, dass zwei "MEASURED" Annahmen der frühen ADRs
  überholt sind (basierten auf StackOverflow #70257679 von 2021).
- Korrektur 1 — Datei-Upload: `POST /v2/products` akzeptiert KEIN `file`-Feld mehr
  (MEASURED: API-Antwort "'file' is not an accepted parameter", 2026-07-18). Der korrekte
  Flow ist Presign->S3-PUT->Complete->Attach (MEASURED: Gumroad GitHub Issue #4477,
  vom Gumroad-Team beantwortet + end-to-end getestet 2026-07-18, "file PERSISTED = True").
- Korrektur 2 — Sales-Tracking: Webhook-Ping braucht öffentliche URL, die ein lokaler
  Host nicht hat. -> POLLING via `GET /v2/sales` (bereits in sale_poller.py umgesetzt,
  ADR-0004 "Webhook" ist damit überholt).
- Entscheidung (FINAL): gumroad_uploader.py MUSS auf den Presign-Flow umgeschrieben werden
  (der alte Code crasht/blockt am echten Call). Sale-Tracking bleibt Polling.
- Konsequenz: TB-3 (Uploader) wird neu implementiert; ADR-0002-Satz "Sale-Webhook-Ping"
  und ADR-0004-Satz "trackt Sales via Webhook" gelten als korrigiert durch dieses ADR.
