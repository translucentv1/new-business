# ADR-0014: create_link-Redirect auf Deliverable + erstes neues PD-Buch

**Status:** Angenommen · **Datum:** 2026-07-18 · **Autor:** Hermes (autonomer Cron-Lauf)
**Bezug:** ADR-0013 (Download-Gate), ADR-0013-Nachtrag (autonomer Push erlaubt)

## GRILL (selbst, vor neuer Initiative)
- *Bringt das messbar einen Sale naeher?* JA. Mehr indexierte Landingpages =
  mehr Long-Tail-SEO-Oberflaeche (die dokumentierte Traffic-Strategie der Charta).
  Buch 98 ("A Tale of Two Cities") ist hochnachgefragt (Klassiker, Dickens).
- *Beleg (MEASURED)?* Nein direkter Sale-Beleg moeglich, aber Mechanik = etablierte
  Strategie; Lieferbarkeit + Redirect wurden live verifiziert (s.u.).
- *Ehrliches Loch?* Risiko: falsch gemappte Gutenberg-ID -> korruptes Bundle
  (siehe TB-13/25913). Mitigation: ID VOR Build per Text-Head verifiziert
  (Titel-Match True) + QA (`is_corrupt`) + Kapitelzahl-Check.
- *Hard Stop?* NEIN (kein Account/Key neu/Geld/Social/OAuth). Stripe-Link wird
  mit vorhandenem Key erstellt (ADR-0012 Design).

## Entscheidung
1. **Neues Buch:** "A Tale of Two Cities" (Gutenberg 98, C. Dickens) end-to-end
   aufnehmen (scan -> pd_processor -> deliverable_gen -> landingpage_gen ->
   Stripe-Link -> publish). 91 Kapitel erkannt, kein PG-Ref, Preview = TOC+Kap.1
   (Landing 5.6KB vs Deliverable 783KB -> Gate intakt, kein Volltext-Leak).
2. **Bugfix create_link:** `scripts/stripe_uploader.create_link` leitete
   `after_completion` auf die *Landingpage* (`/{id}/`), nicht auf das Deliverable.
   Die 7 bestehenden Live-Links waren korrekt via `stripe_redirect_gate.py`
   gesetzt, aber JEDES neue Buch ueber `create_link` haette eine *kaputte
   Erfuellung* bekommen (Kaeufer zahlt -> sieht nur Preview, nicht das Buch).
   Fix: Redirect -> `deliverable_url(book_id)` (verstecktes `/dl/<hash>/<slug>.html`).

## Belege (MEASURED 2026-07-18)
- `python3 scripts/test_pd_processor.py` -> 4/4 PASS.
- `python3 scripts/test_download_gate.py` -> 7 tests OK; 9 Preview-Seiten,
  8 Deliverables (25913 skipped), Stripe-Links fuer alle 9 (98 neu, keine Luecken).
- Stripe API `GET /v1/payment_links` fuer 98:
  `after_completion.redirect.url` = `.../dl/d821d3bec70bad4d/a-tale-of-two-cities.html`
  == `deliverable_url("98")` -> **MATCH True**.
- Live: `curl /98/` -> HTTP 200, `buy.stripe.com`-Button vorhanden (count 1);
  `curl /dl/d821d3bec70bad4d/a-tale-of-two-cities.html` -> HTTP 200;
  `curl /345/` -> 200 (keine Regression).
- `gh-pages` gepusht (Commit `54287bf`); `git ls-tree origin/gh-pages 98/` zeigt
  die Datei.

## Konsequenzen
- Positiv: Inventar 7 -> 8 verkaufbare Produkte; neuer Link hat korrekte Erfuellung.
- Bekanntes Loch (ehrlich): Deliverable-Hash haengt an lokalem `.dl_salt`
  (gitignored). Solange dieselbe Maschine/Salt fuer Rebuilds genutzt wird, bleibt
  der Live-Redirect gueltig. Salt-Aenderung wuerde Live-Links entwerten (spaeteres
  TB, nicht diese Nacht).
- `master` ist 13 Commits vor `origin/master` (nur `gh-pages` ist gepusht/live).
  Push von `master` war NICHT im ADR-0013-Nachtrag autorisiert (nur gh-pages) ->
  bewusst nicht gepusht; User pusht `master` morgens oder gibt frei.
- TB-13 (25913 korruptes Bundle) bleibt `todo` -> USER-Entscheidung
  (Refetch anderes Werk / Drop), autonom NICHT gebaut.
