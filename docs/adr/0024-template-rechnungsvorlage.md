# ADR-0024: Template-Erweiterung "Rechnungsvorlage Kleinunternehmer"

**Status:** ACCEPTED (autonom, GRILL überlebt) · **Datum:** 2026-07-19
**Ticket:** TB-27 · **Spec:** `docs/specs/2026-07-19-template-rechnungsvorlage.md`

## GRILL (selbst, ehrlich)
1. **Bringt es messbar einen Sale naeher?**
   Indirekt: mehr indexierte Landingpage auf einer bewiesen-nachgefragten
   DE-Nische (Rechnungen schreiben = Dauerbeduerfnis von Freelancern/Kleinunternehmern).
   Templates sind der aktive Kanal (Charta). Erhoeht SEO-Oberflaeche des aktiven Kanals.
2. **Beleg (MEASURED)?**
   - Site live, HTTP 200 (MEASURED heute: `/t/finanz-tracker-dach/index.html` = 200).
   - 0 Sales (MEASURED heute: `stripe_uploader.py poll` = 0 new).
   - "Nachfrage bewiesen" nur via Handoff-Claim (ASSUMED: 11k+ Notion-Listings,
     2k-3k Etsy-Reviews) — NICHT frisch von mir gemessen.
   - **Ehrliches Loch:** keine Traffic-Analytics vorhanden → unklar, ob ueberhaupt
     Besucher da sind. Neue Seite ohne Besucher = 0 Extra-Sales. SEO braucht Wochen.
3. **Hard Stop?** Nein. Kein Account, kein Key eingeben (Key liegt lokal), kein Geld,
   kein Social, kein OAuth. Reiner Content-Bau + Publish.
4. **Urteil:** Initiative UEBERLEBT den Grill (sale-closer-adjacent, on-strategy,
   kein Hard Stop). Mit ehrlichem Vorbehalt (kein Traffic-Beleg).

## Entscheidung
Eine neue Template-Spec `rechnungsvorlage-kleinunternehmer` (sheets, 5.99 EUR)
zum aktiven Kanal hinzufuegen: spec -> deliverable -> Stripe-Link -> Landingpage
-> push -> Live-Check. `publish_site.py` Template-Loop wird dynamisch (glob),
damit kuenftige Templates nicht mehr hartkodiert werden muessen (Vermeidung
eines Wiederholungs-Bugs).

## Out of Scope
- Homepage-Index verlinkt Templates nicht (Conversion-Leak, eigener Ticket spaeter).
- Keine neuen PD-Buecher (TB-21 blockiert: OPENROUTER_API_KEY fehlt).
- Kein Etsy (TB-26 Hard Stop USER).
