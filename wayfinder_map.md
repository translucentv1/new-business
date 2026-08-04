# wayfinder:map — Ersten realen Sale erzielen

## Destination
Mit dem bestehenden Geld-Stack (RTD / POD / Affiliate / KDP) den **ersten realen, bezahlten Sale** erzielen — mit minimalem Aufwand, autonom wo möglich. Stack ist technisch fertig + sale-fähig (Stripe-Key gültig, echte Links live). Einziger verbliebener Blocker: **0 Traffic / 0 Besucher**.

## Notes
- Domain: Business Automation / Sales. Skills: wayfinder, autonomous-execution, autonomous-seo-indexnow.
- MEASURED proof Pflicht (HTTP 200, echte Paid-Session, nicht nur "gebaut").
- Stack-Status: RTD ✅(live), POD ✅(Shirtee-Key fehlt), Affiliate ✅(Amazon-Tag fehlt), KDP ✅(1178 Specs, Upload fehlt).
- **Besucher-Lage (MEASURED 2026-08-04, Ticket 9):** Am Kaufbutton kommt niemand an — `funnel_check.py` zeigt BESUCHER = 0. Frueher stand hier „Harter Fakt: 0 Visitors"; das war **ASSUMED** (es gab schlicht kein Instrument). Seitenaufrufe auf `rtd.html` sind weiterhin **ungemessen** (→ Ticket 10). Hebel bleibt Traffic, aber jetzt mit falsifizierbarem Zaehler.
- Rechtlich sauber bleiben (ADR-0030): kein Fake-Account, kein ToS-Bypass.
- **Echte Preise: 3,99 / 7,99 / 14,99 EUR** (MEASURED gegen LIVE-Stripe 2026-08-04).
  Frühere Handoffs behaupteten „399/799/1499 EUR" — das war ein 100x-Lesefehler:
  Stripes `price.unit_amount` ist in **Cent**. Das ist ein **Micro-Produkt**, kein
  Premium-Angebot; Umsatzrechnungen früherer Ticks waren um Faktor 100 falsch.
- **Kanonische Live-Domain: `translucentv1.github.io/new-business/`** (philippgro.github.io = 404).
- **Branch-Falle:** GitHub Pages liefert **gh-pages-ROOT**. Commits auf `master` oder Dateien unter `docs/` gehen live NICHT online (kostete IndexNow 11 Tage). Vor jedem "ist live"-Claim: `curl` gegen die echte URL.
- **Cent-Falle:** Stripe-Beträge immer als `unit_amount/100` lesen. `verify_rtd_chain.py` gibt seit 2026-08-04 beides aus ("399 cent = 3.99 EUR").
- **Paragrafen-Falle:** Für digitale Inhalte ohne körperlichen Datenträger gilt **§ 356 Abs. 6 BGB**, nicht Abs. 5 (Abs. 5 = Dienstleistungen). AGB/Ticket 6/Skripte zitierten bis 2026-08-04 falsch. Rechtsnormen immer gegen gesetze-im-internet.de prüfen, nie aus dem Gedächtnis zitieren.
- **Session-Falle:** `auto_fulfill`s `sessions=N` ist **kein** Traffic-Mass — es enthält auch selbst erzeugte Proben. Echte Browser-Aufrufe haben `payment_link="plink_..."`, eigene API-Proben `payment_link=None`. Vor jedem „erster Besucher!"-Claim: `python scripts/request_delivery/funnel_check.py`.
- **Selftest-Falle:** `auto_fulfill --selftest` läuft mit `push=False` und beweist die Publizierung damit **nicht** — „Kette bewiesen" hieß bis 2026-08-04 in Wahrheit „alles außer der letzten Etappe bewiesen". Ein grüner Selftest ist kein Zustellnachweis; dafür `verify_publish_leg.py` (Ticket 11).
- **HEAD-Falle:** `thanks.html` pollt das Deliverable mit `fetch(..., {method:'HEAD'})`. Live-Checks, die nur GET testen, prüfen den Kundenpfad nicht. Beides messen.
- **Pages-Rebuild = ~31 s** (MEASURED 2026-08-04, Aufbau *und* Abbau je 31 s). `wait_live(18×10 s)` in `auto_fulfill.py` hat damit reichlich Reserve.

## Decisions so far
- [Traffic-Hebel](tickets/1-traffic-hebel.md) — bei 0 Budget: Reddit/X-Posts (Nutzer) oder SEO (langsam). Größter Hebel = Nutzer-Posts.
- [Autonomer Traffic](tickets/2-autonomer-traffic.md) — Hermes kann OHNE Nutzer-Account keinen Traffic erzeugen (keine Reddit/X-Creds, SEO dauert Wochen). Fazit: Loop braucht Nutzer-Präsenz für Sale. *(2026-08-04 teilkorrigiert durch Ticket 4: für **Google** gilt das weiterhin, für **Bing/Yandex** nicht — IndexNow braucht keinen Account.)*
- [Fiverr-Hochpotential](tickets/3-fiverr-hochpotential.md) — Fiverr/Upwork hat höchstes 48h-Potential, weil Traffic VOM Marktplatz kommt (nicht von uns). Hermes baut Gig, Nutzer veröffentlicht (2 Min).
- [IndexNow-Indexierung](tickets/4-indexnow-indexierung.md) — es gibt doch **einen** login-freien Indexierungs-Hebel: IndexNow. Dabei Defekt gefunden: Key lag auf `master` unter `docs/` → live 404, seit 24.07. nie funktionsfähig. Fix live (Key HTTP 200), 1205 URLs eingereicht (HTTP 202/200 MEASURED).
- [Rechtsseiten auf dem Kaufpfad](tickets/6-rechtsseiten-kaufpfad.md) — der Kaufpfad ist jetzt zumutbar: `datenschutz.html` gebaut (war 404, jetzt HTTP 200), AGB ent-templatisiert und `noindex` entfernt, Widerrufs-§ ehrlich gefasst statt ein Erlöschen zu behaupten. Adress-Platzhalter stand in **6** Live-Seiten, nicht in 2 — jetzt nur noch in `impressum.html`. Nebenbefund: `scripts/request_delivery/index.html` war eine live erreichbare Altkopie der Verkaufsseite mit Platzhaltern → Redirect. Commit `4b6f598`.
- [Widerrufs-Zustimmung im Checkout](tickets/7-widerruf-zustimmung-checkout.md) — Stripe **kann** die Zustimmung am Payment Link (`consent_collection` ist unterstützt, scheitert nur an einer ToS-URL, die per API am eigenen Account nicht setzbar ist); ein dropdown-Pflichtfeld geht sogar AFK und ist in der Session auslesbar. **Nützt aber heute nichts:** § 356 **Abs. 6** BGB (nicht Abs. 5 — Zitierfehler in AGB/Ticket 6 gegen die Primärquelle korrigiert) verlangt zusätzlich eine Vertragsbestätigung nach § 312f auf dauerhaftem Datenträger = E-Mail = `EMAIL_*`-Blocker. Entscheidung: LIVE-Links **nicht** anfassen, stattdessen die auslesende Seite gebaut (`extract_consent`/`waiver_effective`, in `sales.log`, Selftest grün). Scharfstellen → Ticket 8.
- [Publish-Etappe verifizieren](tickets/11-publish-etappe-verifizieren.md) — die **letzte ungemessene Etappe des Geldpfads** geschlossen: dass ein erzeugtes Deliverable wirklich live landet, war ASSUMED (`dl/rtd/` war lokal *und* im Git-Tree leer; `--selftest` laeuft mit `push=False` und ueberspringt genau diese Etappe). Dieselbe Defektklasse wie die IndexNow-Branch-Falle, nur zwischen „Kunde hat bezahlt" und „Kunde bekommt Ware". Neu: `verify_publish_leg.py` schickt einen Canary durch die **echten** Produktivfunktionen. MEASURED: 404 vor Push → `git_publish` OK → 0 unpushed → Datei im `origin/gh-pages`-Tree → **GET 200 und HEAD 200** nach 31 s → nach Cleanup wieder 404. HEAD zaehlt separat, weil `thanks.html` mit HEAD pollt — ein GET-Test haette den Kundenpfad nicht bewiesen. Ergebnis: **PUBLISH_LEG_OK**, keine ungemessene Etappe mehr im Geldpfad.
- [Besucher-Messung](tickets/9-besucher-messung.md) — der „harte Fakt 0 Visitors" war **ASSUMED**: auf dem Kaufpfad liegt nachweislich **kein** Zähler und keine Fremdressource, „keine Messung" wurde als „kein Besucher" gelesen. Zugleich ein bereits vorhandenes, ungenutztes Instrument gefunden: ein **echter Browser** legt beim Öffnen eines Payment Links sofort eine `checkout.session` an (MEASURED: curl ohne JS → keine Session; Browser → Session mit `payment_link=plink_…`). Daraus `funnel_check.py` gebaut (0 €, kein Account, keine Cookies). Erste echte Zahl: **BESUCHER = 0** — „niemand erreicht den Kaufbutton" ist jetzt belegt statt vermutet. Nebenbefund: der Tick startete mit `sessions=1`, das war die eigene Ticket-7-Probe — ohne das neue Trennmerkmal wäre daraus ein falscher „erster Traffic"-Claim geworden.

## Tickets (Frontier)
- [Fiverr-Hochpotential](tickets/3-fiverr-hochpotential.md) — GIG TEXT READY (fiverr_gig.md), wartet auf Nutzer-Veröffentlichung. **HITL-Blocker (Nutzer-KYC).**
- [Bing-Indexierung verifizieren](tickets/5-bing-indexierung-verifizieren.md) — AFK, aber **zeitgesperrt bis 2026-08-07**: vorher hat ein Lauf keinen Informationswert.
- [Widerrufs-Waiver scharfstellen](tickets/8-widerruf-waiver-scharfstellen.md) — **blockiert durch zwei USER-Blocker** (ToS-URL im Stripe-Dashboard, `EMAIL_*`). Nicht auf der Frontier. Wird auch dann erst umgesetzt, wenn echte Sale-Daten das Widerrufsrisiko beziffern — Checkout-Reibung bei einem 4-€-Produkt kann teurer sein als jeder Widerruf.
- [Seitenaufrufe auf rtd.html messen?](tickets/10-seitenaufrufe-messen.md) — **HITL-Grilling**, ein Cron-Tick darf das nicht selbst entscheiden. Jede Option kostet einen Account und/oder eine DSGVO-Nachziehung auf dem Kaufpfad; „gar nicht messen" ist bei 3,99 € eine ernsthafte Antwort. Informationswert erst, wenn Ticket 5 Indexierung zeigt oder Ticket 3 live ist.

**USER-Blocker (nicht ticketbar, nur der Nutzer kann sie lösen):**
1. Ladungsfähige Postanschrift in `impressum.html` Z. 20–21. Einzige verbliebene Platzhalter-Stelle im Repo; ohne sie ist § 5 DDG nicht erfüllt.
2. `EMAIL_*` in `hermes/.env` — ohne Mailversand keine Vertragsbestätigung auf dauerhaftem Datenträger (§ 312f BGB) und damit kein Widerrufs-Waiver.
3. ToS-URL in den öffentlichen Stripe-Geschäftsangaben (`agb.html`) — per API am eigenen Account nachweislich nicht setzbar, ~2 Min im Dashboard.

## Not yet specified
- Falls Bing indexiert (Ticket 5 positiv): welche Keywords/Seiten ziehen überhaupt Suchvolumen? Erst grillen, wenn echte Impressionen messbar sind — vorher ist jede Content-Arbeit Blindflug.
- Conversion: rtd.html wurde nie von einem echten Besucher gesehen. Ob 3,99 € Einstiegspreis / Formularfeld "anfrage" konvertieren, ist unbeantwortbar ohne Traffic. Nicht ticketbar bis Besucher > 0. *(2026-08-04 präzisiert: „Besucher > 0" ist ab jetzt **falsifizierbar** — `funnel_check.py` meldet BESUCHER > 0, sobald ein echter Browser die Kaufseite öffnet. Der Trigger für dieses Fog-Patch ist damit definiert statt gefühlt.)*
- **Trägt ein Micro-Preis (3,99–14,99 €) dieses Geschäftsmodell überhaupt?** Durch die Preiskorrektur neu aufgeworfen: pro Sale bleiben nach Stripe-Gebühr nur wenige Euro, während Rechts- und Fulfillment-Aufwand identisch zu einem teuren Produkt sind. Ob das ein Preisproblem, ein Mengenproblem oder gar kein Problem ist, lässt sich ohne echte Conversion-Daten nicht entscheiden — erst grillen, wenn Besucher > 0. Nicht blind den Preis anheben.


## Out of scope
- China-POD (Zoll ab 1.7.2026 frisst Vorteil)
- Echtzeit-Kontroll-Warn-App (illegal, Hard-Stop)
- Plattform-Aufbau mit User-Uploads (Art.17-Haftung, vorerst)
- Google-Indexierung ohne Nutzer-Login — `/ping` ist tot (404), Search Console erzwingt Login. Kein autonomer Weg vorhanden; nur über den Nutzer erreichbar.
