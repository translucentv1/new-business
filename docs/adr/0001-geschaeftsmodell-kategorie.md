# ADR-0001 — Geschäftsmodell-Kategorie: Digital/Service statt physischer Ware [FINAL]

- Kontext: arbitrage_bot zeigte Liquiditäts-Lücke (Payment-Holds + Limits) bei physischer
  Arbitrage. Nutzer will max. Autonomie, free-to-build, legal.
- Entscheidung (FINAL, autonom getroffen): Reine Digital-Idee OHNE Warenumschlag,
  OHNE eigenes Capital-at-risk. Physische Arbitrage wird NICHT wiederholt.
- Konsequenz: Kein Lager/Shipping/Payment-Holds. Nachfrage + Differenzierung über Inhalt.

# ADR-0002 — Plattform: Gumroad via API [FINAL]

- Kontext: Free-to-build = "pay only when you earn". Gumroad 10%+$0.50, keine Monatsgebühr
  (MEASURED gumroad.com/pricing). GUMROAD HAT API: Produkte programmatisch anlegen/publish
  + Sale-Webhook-Ping (MEASURED app.gumroad.com/api, StackOverflow #70257679).
- Entscheidung (FINAL): Gumroad primär, via API. EINMALIG Nutzer-Account+API-Key nötig
  (harter Stopp), danach voll autonom (Agent erzeugt/listet/verkauft ohne weiteren Human).
- Konsequenz: Kein Upfront-Geld. Autonomie maximal innerhalb harter Stopps. Etsy sekundär
  (manuell, da keine volle API-Autonomie) -> später.

# ADR-0003 — Produkttyp: Deutsche Public-Domain neu aufbereitet [FINAL]

- Kontext: PD in EU gemeinfrei bei Leben+70J (MEASURED EU-Recht). Sättigung bei PLR-Bundles
  (ASSUMED kundenheld). Differenzierung durch Agent-Qualität nötig.
- Entscheidung (FINAL): DE Public-Domain Sachtexte/Ratgeber (Kochbuch, Haushalt, Technik,
  Natur) vom Agenten neu gegliedert + modernisiert (Rechtschreibung, Struktur, Register)
  + Begleit-PDF. KEIN fremdes urhebergeschütztes Werk ohne Lizenz.
- Konsequenz: Rechtssicher, free-to-build. Agent liefert Mehrwert durch Aufbereitung.

# ADR-0004 — Automatisierung: Autonomous Loop, einmal "go" dann Self-Running [FINAL]

- Kontext: Harte Stopps (kein Account/Upload ohne OK). Nutzer: "Autonom sein".
- Entscheidung (FINAL): Ein einziges Nutzer-OK (Account+Key bereit) -> danach Watchdog-Loop
  (wie WhatsApp): Agent generiert periodisch neue PD-Produkte, lädt via Gumroad-API hoch,
  trackt Sales via Webhook, reinvestiert Gewinn in Scraper/LLM-Tokens. Kein Human-in-Loop.
- Konsequenz: Trennung Entwurf(autonom) vs Ausführung(ein OK). Loop entkoppelt von Risiko.

# ADR-0005 — Reinvestitionsregel [FINAL]

- Kontext: free-to-build verlangt "Gewinn -> Reinvestition".
- Entscheidung (FINAL): Erste 100% des belegten Gewinns -> Scraper-API (z.B. für frische
  PD-Quellen/Metadaten) + LLM-Tokens für Aufbereitung. Erst bei >X€/Monat Payout an Nutzer.
- Konsequenz: System wächst selbsttragend, kein externes Budget.
