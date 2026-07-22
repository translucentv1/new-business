# ADR-0032: Produkt-QA-Fix (Faktenfehler + Deliverable-Anreicherung) + Outbound-Kit

Datum: 2026-07-22
Status: umgesetzt (Code lokal, gh-pages live gepusht)
Session: autonome Nachtschicht (Hermes), 5h-Fenster

## Kontext
0 Sales, 0 Traffic. Funnel technisch gebaut (8 Templates, 22 Stripe-Links).
Auftrag: autonom am Business arbeiten. Bindende Beschraenkung laut
meta-agent-sale-velocity + Research: **Distribution**, nicht Zahlung/Produkt.

## Entscheidungen + MEASURED-Belege

### 1. Faktenfehler korrigiert: Sparerpauschbetrag 801/1608 -> 1000/2000 EUR
- MEASURED (gesetze-im-internet.de/estg/__20.html, finanzamt.nrw.de, 2026-07-22):
  Sparer-Pauschbetrag = **1.000 EUR** (Ledige) / **2.000 EUR** (Zusammenveranlagte),
  seit 2023 (vorher 801/1602). Produkt `steuerfreibetrag-optimierer` und 56 SEO-Seiten
  trugen den falschen alten Wert -> repo-weit gepurgt (Evidence-Rule 4).
- Quelle des Fehlers: `make_new_templates.py` (audience/keywords/benefits) +
  `seo_scale3.py` Zeile 84 hartkodiert. Beide gefixt, alle Generatoren neu gelaufen.
- Verifiziert LIVE: `curl .../t/steuerfreibetrag-optimierer/` -> `1000/2000`, `801` = 0 Treffer.

### 2. Deliverables angereichert (Refund-Risiko gesenkt)
- Vorher: budget.csv = 5 Zeilen, alle 0; ANLEITUNG.md = 5 Zeilen (89-594 Bytes).
  Ein zahlender Kaeufer haette fuer ~89 Bytes bezahlt -> Refund-/Chargeback-Risiko.
- Nachher: 12-Monats-Grid + automatische Zeilen-Summe (Spalte N) + Gesamt-Summe
  (Zeile GESAMT) mit `=SUM()`-Formeln; ANLEITUNG mit "In 3 Minuten startklar",
  Bereichen, Praxis-Tipps, Haftungshinweis. MEASURED: deliverable-HTML live
  2664->5656 Bytes (finanz), 1601->2566 (adhs) etc.
- Generatoren gefixt: `template_gen.py` (4 Produkte) + `make_new_templates.py` (3).
- `test_template_gen.py` an neues Format angepasst: **4/4 PASS** (MEASURED).

### 3. Funnel live end-to-end verifiziert (nicht nur HTTP 200)
- 4-Hop-Probe je Produkt: LP 200 -> buy.stripe.com 200 -> after_completion redirect
  vorhanden -> deliverable 200 (>1000 Bytes). **8/8 OK** (MEASURED, live nach Deploy).

### 4. Outbound-Kit fuer alle 8 Produkte (scripts/outbound_kit.py)
- Pro Produkt 1 Datei mit Etsy-Listing + Reddit- + FB-Entwurf + Notion-Gallery-Hinweis.
- Preise/Titel/Zielgruppe aus spec.json (single source) -> keine hartkodierten Preise.
- Alte `docs/social/drafts/` hatten MEHRERE Faktenfehler (kleingewerbe 2,99 statt 9,99;
  rechnung 2,99 statt 5,99; "6 agent skills" statt 7) -> geloescht, ersetzt durch
  korrektes generiertes Kit unter `docs/social/outbound/`.

## Research: schnellste Erst-Sale-Hebel (Subagent, MEASURED 2026-07-22)
Reihenfolge nach erwarteter Geschwindigkeit (Details: docs/research/first-sale-levers-DE.md):
1. **Etsy** — eingebauter DE-Kaufintent, VAT von Etsy abgefuehrt (etsy.com/seller-handbook
   /article/22848011323), 0,20 $/Listing. Autonom vorbereitbar (Listing-Text im Kit).
2. **Notion Template Gallery** — staerkstes kostenloses Publikum, ABER braucht Notion-Konto
   des Nutzers + Produkt als teilbare Notion-Seite (Hard Stop: Account).
3. **Facebook-Gruppen** (DE Finanzen/Selbststaendig/ADHS) — Regeln je Gruppe pruefen.
4. **Reddit** — Wert zuerst, Link nur im Kommentar (r/Finanzen verbietet Direktwerbung).
- FALLE bestaetigt: Gumroad Discover gesperrt bis $100 echte Sales (gumroad.com/help/
  article/79) -> als Discovery unbrauchbar fuer 0-Sales.

## Hard Stops (bleiben beim Nutzer)
- Account-Erstellung (Etsy, Notion), Posten auf eigenen Accounts, Zahlung verbinden.
- Der Agent bereitet ALLES vor (Listings, Post-Texte, korrekte Preise/Fakten);
  der eine menschliche Schritt = auf eigenem Account einstellen/posten.

## Naechster Sale-kritischer Schritt (fuer den Nutzer, 1x manuell)
Etsy-Account + 2-3 Listings aus `docs/social/outbound/*.md` einstellen (hoechster
autonom-vorbereiteter Kaufintent). Danach FB/Reddit-Entwuerfe posten.
