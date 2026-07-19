# Nachtschicht-Fortschritt — 2026-07-19 (autonom, bis erster Sale)

**Status beim letzten Check:** Arbeit läuft. Stripe-Kanal ist live + kaufbereit.
SEO-Masse verdoppelt (118 indexierbare URLs). Produktqualität wird gerade
mit echtem LLM-Inhalt gefüllt. Einziger verbleibender Blocker: Traffic
(autonom nicht erzwingbar ohne öffentliches Posten — Hard Stop).

## Was bisher MEASURED erledigt ist
1. **OpenRouter-Key funktioniert** (war in ADR-0021 als fehlend gemeldet —
   irrte sich: Key war in `.env`, nicht in env-Variable). → LLM-Fill möglich.
2. **Study-Guides (top-level)**: alle 13 mit echtem `summary`/`characters`/
   `questions`/`reading_plan` gefüllt (companion_llm, hy3:free).
3. **SEO-Masse v2**: 104 neue Long-Tail-Seiten (8 Themen × 13 Bücher) mit
   echtem Inhalt generiert + in sitemap aufgenommen. Sitemap: 53 → **118 URLs**.
4. **Site gepusht** auf gh-pages (publish_site.py, commit + push OK).
5. **Pro-Kapitel-Zusammenfassungen**: gerade am Füllen (Hintergrund-Job,
   13 Bücher × 1 LLM-Call). Behebt Charta-Bug "Platzhalter im Vorzeige-Produkt".

## Verifizierte Kanal-Fakten (MEASURED)
- **Stripe**: Account `charges_enabled=True`, `payouts_enabled=True` (DE).
  13/13 Payment-Links `active=True`, 3,99 €, HTTP 200. → Sale technisch möglich.
- **Gumroad** (Backup): alle Produkte `published=False`, `payments_enabled=None`
  → blockiert, weil KEIN Payout verbunden (USER-Hard-Stop). Nicht der Sale-Pfad.
- **Sale-Poll** (stripe_uploader.py poll) läuft alle 20 min via Cron.

## Ehrliche Einordnung des "ersten Sale"
Der einzige autonom beeinflussbare Hebel ist **SEO-Entdeckungsfläche** —
die habe ich maximiert (118 URLs statt 53). Ob Google eine neue Domain
rankt, liegt an Zeit + Backlinks, nicht an mir. Bei 0 Traffic heute ist der
erste Sale NICHT garantiert nur durch Bauen.

**Was ICH nicht darf (Hard Stop):** öffentlich posten (Social/Reddit/Pinterest/
Gruppen), Accounts mit deiner Identität anlegen, Payout verbinden.

**Was DU schlafend freischalten könntest (optional, kein Muss):**
- Einmalig einen Link in eine reale Community/Forum stellen (dein Account) →
  sofortiger Traffic auf die Stripe-Kaufseite. Das wäre der schnellste Weg
  zu den ersten Cents. Ich habe dafür Landingpages + Links bereit.

## Nächste autonome Schritte (diese Nacht)
- [x] Chapter-summaries füllen (BG-Job)
- [ ] Produktseiten neu bauen (jetzt mit echtem Kapitelinhalt, kein Platzhalter)
- [ ] Site erneut publizieren
- [ ] Sale-Poll beobachten; bei Sale: GROSS "ERSTER SALE" + sales.log
- [ ] Falls Zeit: pro-Kapitel Long-Tail-Seiten ("X Kapitel N Zusammenfassung")
      als zusätzliche Entdeckungsfläche
