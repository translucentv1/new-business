# Social-Post-Entwürfe (publish-ready) — ADR-0030 Strategie #1

**Ziel:** Ersten Sale bis So 2026-07-26 (ADR-0030). Flaschenhals = Traffic.
**Hebel:** Buzz/Discovery über DE-Communities (Reddit, LinkedIn, Facebook, X).
**Stand:** 2026-07-21, 00:1x (cron-Durchgang).

## MEASURED — alle verlinkten Landingpages live (curl -L, HTTP 200)
- `https://translucentv1.github.io/new-business/t/finanz-tracker-dach`
- `https://translucentv1.github.io/new-business/t/kleingewerbe-steuer`
- `https://translucentv1.github.io/new-business/t/adhs-wochenplaner`
- `https://translucentv1.github.io/new-business/t/rechnungsvorlage-kleinunternehmer`
- `https://translucentv1.github.io/new-business/t/agent-skills-bundle`
- `https://translucentv1.github.io/new-business/t/nebenkostenabrechnung`

## WICHTIG — ADR-0030 Grenze (b) / Risiko-Hygiene
- **Nur über ECHTE Accounts des Nutzers posten.** Kein Fake-Account (das ist rechtlich belangbar).
- **Wert zuerst, kein Spam.** Jeder Post liefert echten Nutzen, Link ist klar als eigene Empfehlung gekennzeichnet.
- **Plattform-ToS beachten** (manche Subreddits/Gruppen verbieten Produkt-Links im Hauptpost → Link dann als top-Kommentar mit Disclaimer).
- **Hermes postet NICHT** (kein Account-Zugang, headless). Das sind nur Entwürfe zum 1-Klick-Posten durch den Nutzer.
- **Kein Geld ausgeben** (Startbudget 0 €, ADR-0030 Grenze a). Diese Entwürfe kosten nichts.

## Dateien
- `reddit-finanzen-finanz-tracker.md` — r/Finanzen: Budget/Tracker
- `reddit-adhs-wochenplaner.md` — r/ADHS: Wochenplan
- `reddit-steuer-kleingewerbe.md` — r/Steuern: Kleingewerbe EÜR
- `linkedin-kleingewerbe-rechnung.md` — LinkedIn: Rechnung Pflichtangaben
- `facebook-kleingewerbe-rechnungsvorlage.md` — FB-Gruppe Existenzgründung
- `x-dev-agent-skills.md` — X/Twitter: Agent-Skills für Devs

## Nächster Schritt (Nutzer)
Pro Plattform einen Entwurf auswählen, auf dem eigenen Account posten, Disclaimer beibehalten,
ToS-Check (Link erlaubt?). Danach Sale-Check via `python3 scripts/stripe_uploader.py poll`.
