# ADR-0028 — Neues PD-Buch: A Study in Scarlet (Gutenberg 244)

**Status:** Akzeptiert · **Datum:** 2026-07-19 · **Autor:** Hermes (autonomer Cron)
**Kontext:** Dauerschleife nach Handoff Nachtschicht. Backlog leer bis auf
TB-21 (blocked: OPENROUTER_API_KEY) + TB-26 (blocked: Etsy Hard Stop).
Neue Initiative nur via GRILL→SPEC→TICKETS→IMPLEMENT.

## GRILL (selbst, schriftlich)
- **Bringt das messbar einen Sale naeher?** JA. 14. Produkt + weitere
  SEO-Landingpage. "Sherlock Holmes / A Study in Scarlet" hat sehr hohe
  evergreen Such-Nachfrage + Study-Guide-Intent. Mehr Oberflaeche = mehr
  Long-Tail-Traffic = mehr Kaufwahrscheinlichkeit. Entspricht erlaubtem
  Beispiel "mehr PD-Buecher in den Korpus + Landingpages".
- **Beleg (MEASURED)?** Preview-Page HTTP 200, Stripe-Payment-Link erzeugt
  (buy.stripe.com/...), Deliverable (HTML+EPUB) generiert, Tests gruen.
  Alles verifizierbar im Bericht.
- **Ehrliches Loch?** Kein `study_guide.json` (OPENROUTER_API_KEY fehlt,
  TB-21). Preview fallt daher auf ADR-0013-TOC-Stil zurueck (Test akzeptiert
  "Inhaltsverzeichnis"); kein "Was dich erwartet"-Begleiter-Teaser. Das
  Produkt ist trotzdem vollwertig verkaufbar: Deliverable = bereinigter
  Volltext + EPUB, Stripe-Redirect korrekt.
- **Hard Stop beruehrt?** NEIN. Kein Account/Key eingeben, kein Geld
  bewegen, kein Social, kein OAuth, nichts loeschen. Stripe-Payment-Link-
  Erzeugung per API ist der etablierte autonome Flow (TB-10, TB-14–TB-18).
- **Entscheidung:** BAUEN (ein kompletter Schritt = ein Buch).

## Spec (kurz)
Problem (Kaeufer): kein Angebot fuer das hoch-nachgefragte Werk.
Loesung: Korpus + Preview + Deliverable + Stripe-Link wie alle anderen
13 Buecher. User Story: Kaeufer findet Landingpage ueber Long-Tail-Suche,
kauft, wird zum Deliverable redirectet. Out of Scope: Study-Guide-Fill
(wartet auf USER-Key), EPUB-Verbesserungen, weitere Buecher in diesem Tick.

## Umsetzung (IMPLEMENT)
download (gutenberg 244) → TOC-Block strip → `pd_processor.build_product`
→ `stripe_uploader` (Link) → `landingpage_gen.build()` → Tests gruen →
commit → `publish_site.py` → Live-Check 200. Ticket: TB-28.
