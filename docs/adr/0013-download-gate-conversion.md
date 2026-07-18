# ADR-0013: Download-Gate statt gratis Volltext (Conversion-Hebel)

**Status:** Angenommen · **Datum:** 2026-07-18 · **Autor:** Claude Code
(leitender Kopf) im Auftrag des Nutzers; Ausfuehrung autonom durch Hermes.

## Kontext
ADR-0012 hat als MVP-Fulfillment die **oeffentliche Landingpage mit vollem,
gemeinfreiem Buchtext** festgelegt. Das schliesst zwar die Kasse, ist aber der
staerkste Conversion-Killer: niemand zahlt 3,99 EUR fuer einen Text, der auf
derselben Seite bereits kostenlos und vollstaendig lesbar ist.

- MEASURED 2026-07-18, `scripts/landingpage_gen.py`: `body_text = _esc(content)`
  rendert den kompletten `product/content.md` als sichtbaren Seiteninhalt.
- MEASURED 2026-07-18, `stripe_links.json`: 8 Live-Payment-Links aktiv; ihr
  `after_completion`-Redirect zeigt auf genau diese Volltext-Seite.
- MEASURED 2026-07-18: `py -3.12 -c "import reportlab/weasyprint"` ->
  `ModuleNotFoundError` (keine PDF-Bibliothek installiert). `zipfile`/`html`
  (stdlib) sind vorhanden.

## Entscheidung
1. **Preview-Fulfillment.** Die oeffentliche Produktseite zeigt kuenftig nur
   noch eine **Leseprobe**: Titel, Autor, Inhaltsverzeichnis und das **erste
   Kapitel**, plus Kaufbutton. Der Rest wird angeteasert, nicht ausgeliefert.
2. **Obscure-URL-Download-Gate.** Das vollstaendige eBook wird als Datei unter
   einem **nicht erratbaren, gehashten Pfad** abgelegt
   (`/dl/<sha256(id+salt)>/<slug>.html`). Diese Download-URL wird **nur** ueber
   den Stripe-`after_completion`-Redirect ausgeliefert, nie oeffentlich
   verlinkt und nicht in `sitemap.xml`/`robots.txt` gefuehrt.
3. **Deliverable-Format.** Tier-1 = eine **self-contained, gestylte HTML-Datei**
   (voller Text, offline lesbar, null externe Abhaengigkeit). Tier-2 (spaeter,
   eigenes Ticket) = **EPUB** ueber stdlib `zipfile`. **Kein PDF** (wuerde
   pip-Install neuer Infrastruktur erfordern — verstoesst gegen Velocity-Regel).
4. **Redirect-Umstellung.** `stripe_uploader.py` setzt `after_completion`
   jedes Payment-Links auf die jeweilige Download-URL statt auf die
   Volltext-Landingpage. Umstellung erst, **nachdem** Preview + Download-Datei
   generiert und MEASURED-gruen sind (sonst zeigt ein Live-Link ins Leere).

## Konsequenzen
- Positiv: Der Kaufanreiz entsteht wieder (Wert hinter der Kasse statt davor);
  hoehere erwartbare Conversion, ohne neue Infrastruktur oder Hard-Stop.
- **Bekanntes Loch (ehrlich, MEASURED):** Statisches GitHub-Pages-Hosting kann
  eine Zahlung **nicht serverseitig verifizieren**. Der gehashte Pfad ist
  *Obscurity, keine Kryptographie* — eine geteilte URL umgeht das Gate. Ein
  echtes serverseitig verifiziertes Gate (signierte URL / Serverless-Funktion +
  Stripe-Session-Check) ist ein spaeteres TB und bewusst NICHT Teil dieser
  Nacht (neue Infra + Deploy = Hard-Stop-Naehe).
- Legal unveraendert unkritisch: Werke sind gemeinfrei; das Gate schuetzt die
  *Aufbereitung/Bequemlichkeit*, nicht ein Urheberrecht.

## Belege
- MEASURED 2026-07-18: `landingpage_gen.py` Volltext-Render (Zeile
  `body_text = _esc(content)`), `stripe_links.json` (8 Links), fehlende
  PDF-Libs (ModuleNotFoundError), stdlib `zipfile`/`html` vorhanden.
- docs.stripe.com/payment-links/url-parameters — `after_completion` Redirect
  nach Kauf (bereits in ADR-0012 zitiert, hier nur Zielpfad geaendert).
