# ADR-0015: Neues PD-Buch "Jane Eyre" (Gutenberg 1260) ins Funnel

**Status:** Akzeptiert · **Datum:** 2026-07-18 (autonomer Cron-Durchgang)
**Vorgang:** GRILL → SPEC → TICKETS (TB-15) → IMPLEMENT

## GRILL (selbst, schriftlich)
- **Bringt das messbar einen Sale naeher?** JA. Mehr indexierbare Produkte =
  mehr Long-Tail-SEO-Oberflaeche = hoeheres erwartetes Sales-Volumen. Das ist
  der oberste Top-of-Funnel-Hebel im Buch-Modell.
- **Beleg (MEASURED)?** Gutenberg 1260 via curl HTTP 200 (0,96 s). Titelblatt
  im Rohtext verifiziert: "JANE EYRE ... by Charlotte Brontë" → keine
  25913-Trap (Titel stimmt mit Inhalt ueberein). Brontë gest. 1855 → EU
  Life+70 erfuellt (gemeinfrei).
- **Ehrliches Loch?** Ob DIESES Buch verkauft, ist ungewiss; Erwartungswert
  steigt aber mit der Produktzahl. Kein Hard Stop beruehrt.
- **Hard Stop?** NEIN. Kein Account/Key neu, kein Geld, kein Social, kein
  OAuth. Stripe-Link via bestehendem Key + gh-pages-Push sind durch
  ADR-0013-Nachtrag autorisiert.

## Entscheidung
Jane Eyre als Buch 1260 aufnehmen: download → clean → preview → deliverable →
Stripe-Link → push → Live-Check. Voraussetzung: content.md nach Bau
nachweislich korrekt (Kapitelstruktur, Titel = Inhalt, keine PG-Referenz).

## Out of Scope
- TB-13 (25913-Korrumpiert): bleibt USER-Entscheidung, hier NICHT angeruehrt.
- EPUB-Tier-2: separater Ticket, nicht dieser Durchgang.
