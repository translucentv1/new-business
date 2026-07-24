# ADR-0017: Neues PD-Buch "Wuthering Heights" (Gutenberg 768) ins Korpus+Live

- **Status:** Akzeptiert · **Datum:** 2026-07-18 · **Autor:** Hermes (Nachtschicht, autonom)
- **Kontext:** Alle TB-8..12,14..16 done; einzig offen TB-13 (USER-Entscheidung,
  nicht autonom). Zeit 13:xx (vor 16:00) → produktive Arbeit erlaubt.

## GRILL (selbst, schriftlich)
- **Bringt das einen Sale naeher?** Mehr SEO-Landingpages = mehr Long-Tail-
  Traffic-Oberflaeche = hoehere Sale-Wahrscheinlichkeit. Gleiches bewaehrte
  Muster wie TB-14/15/16 heute Nacht (Korpus 8→11 Buecher). JA.
- **MEASURED-Beleg:** Korpus wuchs 8→11 Buecher heute Nacht (git log TB-14/15/16);
  Pipeline (pd_processor→landingpage_gen→stripe_uploader) ist gruen + live.
- **Ehrliches Loch:** Erster Sale haengt v.a. am Traffic-Volumen; ein Buch ist
  marginal, aber kumulativ. Kein Garantie-Beleg fuer einen Sale.
- **Hard Stop beruehrt?** NEIN. Kein Account/Key neu, kein Geld, kein Social,
  kein OAuth. Stripe-Rail + .stripe_secrets bereits vorhanden (ADR-0010/0013).
- **Entscheidung:** BAUEN (ein Buch, vollstaendiger Schritt).

## Spezifikation (Kurzform)
- Buch: "Wuthering Heights", Emily Brontë, 1847 (EU-PD, Leben+70), Gutenberg 768.
- Warum dieser Roman: hat "CHAPTER I.."-Struktur → Preview zeigt nur Kap. 1
  (kein Volltext-Leak; Charta-Verbot). Kurzgeschichten-Sammlungen (z.B. Sherlock)
  waeren ungeeignet (ein "Gesamt"-Block → Leak).
- Pipeline: text.txt+meta.json → pd_processor.build_product →
  landingpage_gen.build (Preview+Deliverable) → Stripe-Link in stripe_links.json
  → publish_site.py → Live-Check 200.

## MEASURED-Ergebnis (nach Bau)
- QA-Gate: Titel "# Wuthering Heights", TOC ja, keine [Illustration]/PG-Reste,
  35 Kapitel → PASS.
- Tests: test_pd_processor = ALL TESTS PASS; test_download_gate = OK (7 tests).
- Artefakte: docs/768/index.html (Preview, 3713 B, Kaufbutton verdrahtet),
  docs/dl/270c74d0863825b9/wuthering-heights.html (Deliverable, 678920 B,
  voller Text). ratio Preview/Deliverable = 0.006 → kein Leak.
- Push: gh-pages c351471, PUSHED. Live: HTTP 200 auf /768/ und /dl/.../..html.
- Stripe-Link: buy.stripe.com/aFa7sL7RD6iT4oO20P6c00b (Redirect auf Deliverable).

## Out of Scope
- TB-13 (25913-Bundle korrupt / falscher Inhalt) = USER-Entscheidung, unangetastet.
- Kein Business-Pivot, keine neuen Plattformen/Accounts (Nachtschicht-Mandat).
