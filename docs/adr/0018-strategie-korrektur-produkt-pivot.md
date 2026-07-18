# ADR-0018 — Strategische Korrektur: Produkt falsch, Engine richtig [FINAL, autonom 2026-07-18]

- Kontext: Nutzer fordert Grill der Strategie. Ziel: "so autonom wie möglich erstmal einen
  kleinen Gewinn". Bisher: PD-Klassiker-Rohtexte zu $3,99 auf Gumroad/Stripe.
- Befund (MEASURED): Corpus stammt von Project Gutenberg -> jeder Titel dort GRATIS.
  Das $3,99-PD-Produkt hat einen perfekten kostenlosen Substitute -> Kaufanreiz ~0.
  Gumroad Discover = 0 Traffic vor $100 echten Verkäufen + Risk-Review (gumroad.com/help/79,
  MEASURED). Eigen-Daten: 0 Sales, 0 organischer Traffic nach Stunden.
- Befund (ASSUMED, Reddit-Konsens): Gumroad = "no discovery engine, low returns, a grind".
  PD-eBooks = gesaettigste, am wenigsten differenzierte Kategorie.
- Root-Cause: Autonomie wurde in PRODUKTION optimiert; Gewinn lebt in DISTRIBUTION +
  DIFFERENZIERUNG. PD-Rohtexte haben beides nicht. Automating a product with no demand
  = automating zero sales.
- Entscheidung (FINAL, autonom): PRODUKT-Pivot, Engine (Stripe-Uploader, Landingpages,
  Download-Gate, Sale-Poll) BLEIBT (funktioniert, wiederverwendbar). Neues Produktprinzip:
  DIFFERENZIERUNG statt Roh-PD. Aus demselben Corpus erzeugt der Agent MEHRWERT, den
  Gutenberg nicht bietet -> z.B. Lese-Begleiter / Study-Guides (Figurenkarten, Diskussions-
  fragen, Zusammenfassungen, 30-Tage-Leseplan) oder kuratierte Themen-Packs. Autonom
  generierbar (LLM), KEIN freier Substitute.
  Beispiel: "Pride and Prejudice - Lese-Begleiter + 30-Tage-Plan" statt "Pride and Prejudice
  (Rohtext)".
- Sekundär (offen): Traffic bleibt der bindende Engpass. PD-Rohtexte WEG, aber Gumroad-Discover
  liefert weiter 0 vor $100. Naechster Schritt nach Produkt-Pivot: Kanal mit eingebauter
  Discovery evaluieren (Marktplatz mit Suche) ODER Landingpage-SEO geduldig betreiben.
  Das ist T3/T5-Weiterfuehrung, nicht Produkt-Blocker.
- Konsequenz: Neuer Tracer-Bullet TB-19 (Study-Guide-Generator aus Corpus) + TB-20
  (Preis/Positionierung des Mehrwerts). Bestehende 8 Drafts werden NICHT geloescht, sondern
  um Begleiter angereichert (idempotent). Kein Geld ausgeben, keine ToS-Umgehung.
- Belegstatus: Gutenberg-Substitution + Discover-Regeln MEASURED. "Was verkauft sich" ASSUMED
  (anecdotal) -> nach ersten echten Verkaeufen MEASURED re-evaluieren.
