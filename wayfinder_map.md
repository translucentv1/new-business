# wayfinder:map — Ersten realen Sale erzielen

## Destination
Mit dem bestehenden Geld-Stack (RTD / POD / Affiliate / KDP) den **ersten realen, bezahlten Sale** erzielen — mit minimalem Aufwand, autonom wo möglich. Stack ist technisch fertig + sale-fähig (Stripe-Key gültig, echte Links live). Einziger verbliebener Blocker: **0 Traffic / 0 Besucher**.

## Notes
- Domain: Business Automation / Sales. Skills: wayfinder, autonomous-execution, autonomous-seo-indexnow.
- MEASURED proof Pflicht (HTTP 200, echte Paid-Session, nicht nur "gebaut").
- Stack-Status: RTD ✅(live), POD ✅(Shirtee-Key fehlt), Affiliate ✅(Amazon-Tag fehlt), KDP ✅(1178 Specs, Upload fehlt).
- Harter Fakt: 0 Visitors auf 1300 Seiten + rtd.html → 0 Sales. Hebel = Traffic.
- Rechtlich sauber bleiben (ADR-0030): kein Fake-Account, kein ToS-Bypass.
- **Kanonische Live-Domain: `translucentv1.github.io/new-business/`** (philippgro.github.io = 404).
- **Branch-Falle:** GitHub Pages liefert **gh-pages-ROOT**. Commits auf `master` oder Dateien unter `docs/` gehen live NICHT online (kostete IndexNow 11 Tage). Vor jedem "ist live"-Claim: `curl` gegen die echte URL.

## Decisions so far
- [Traffic-Hebel](tickets/1-traffic-hebel.md) — bei 0 Budget: Reddit/X-Posts (Nutzer) oder SEO (langsam). Größter Hebel = Nutzer-Posts.
- [Autonomer Traffic](tickets/2-autonomer-traffic.md) — Hermes kann OHNE Nutzer-Account keinen Traffic erzeugen (keine Reddit/X-Creds, SEO dauert Wochen). Fazit: Loop braucht Nutzer-Präsenz für Sale. *(2026-08-04 teilkorrigiert durch Ticket 4: für **Google** gilt das weiterhin, für **Bing/Yandex** nicht — IndexNow braucht keinen Account.)*
- [Fiverr-Hochpotential](tickets/3-fiverr-hochpotential.md) — Fiverr/Upwork hat höchstes 48h-Potential, weil Traffic VOM Marktplatz kommt (nicht von uns). Hermes baut Gig, Nutzer veröffentlicht (2 Min).
- [IndexNow-Indexierung](tickets/4-indexnow-indexierung.md) — es gibt doch **einen** login-freien Indexierungs-Hebel: IndexNow. Dabei Defekt gefunden: Key lag auf `master` unter `docs/` → live 404, seit 24.07. nie funktionsfähig. Fix live (Key HTTP 200), 1205 URLs eingereicht (HTTP 202/200 MEASURED).

## Tickets (Frontier)
- [Fiverr-Hochpotential](tickets/3-fiverr-hochpotential.md) — GIG TEXT READY (fiverr_gig.md), wartet auf Nutzer-Veröffentlichung. **HITL-Blocker (Nutzer-KYC).**
- [Bing-Indexierung verifizieren](tickets/5-bing-indexierung-verifizieren.md) — AFK, aber **zeitgesperrt bis 2026-08-07**: vorher hat ein Lauf keinen Informationswert.

## Not yet specified
- Falls Bing indexiert (Ticket 5 positiv): welche Keywords/Seiten ziehen überhaupt Suchvolumen? Erst grillen, wenn echte Impressionen messbar sind — vorher ist jede Content-Arbeit Blindflug.
- Conversion: rtd.html wurde nie von einem echten Besucher gesehen. Ob 399 € Einstiegspreis / Formularfeld "anfrage" konvertieren, ist unbeantwortbar ohne Traffic. Nicht ticketbar bis Besucher > 0.

## Out of scope
- China-POD (Zoll ab 1.7.2026 frisst Vorteil)
- Echtzeit-Kontroll-Warn-App (illegal, Hard-Stop)
- Plattform-Aufbau mit User-Uploads (Art.17-Haftung, vorerst)
- Google-Indexierung ohne Nutzer-Login — `/ping` ist tot (404), Search Console erzwingt Login. Kein autonomer Weg vorhanden; nur über den Nutzer erreichbar.
