# ADR-0022 — Strategie-Klärung: Kanal über Traffic, nicht mehr Produkt [ENTWURF zur USER-Entscheidung]

- **Status:** EMPFEHLUNG / wartet auf USER-Entscheidung (nicht bauen vor Wahl)
- **Datum:** 2026-07-19
- **Autor:** Hermes (antwortet auf Handoff-2026-07-19 §3 + ADR-0021)
- **Belegregel:** MEASURED = in dieser Sitzung per Stripe-API / HTTP geprüft. ASSUMED = Schätzung ohne Primärquelle.

## 1. Ehrliche Bilanz der bisherigen Versuche (2–3 Sätze)

Wir haben eine voll funktionsfähige Autonomie-Engine gebaut (Stripe-Uploader, Landingpages,
Download-Gate, Sale-Poll) und 13 kaufbare Produkte live geschaltet — **aber 0 Sales bei ~0 Traffic**
(MEASURED: `poll ok, 0 new sale(s)`; Stripe-Konto `charges_enabled=True`, 13/13 Links `active=True`).
Die erkannte Lektion aus ADR-0018 trifft weiter zu: **ein Produkt ohne Distributionskanal erzeugt
keinen Umsatz** — und ADR-0021 hat bestätigt, dass "noch mehr Produkte" diesen Engpass nicht löst
(SEO ist der einzige erlaubte Hebel und langsam). Der Store ist also nicht kaputt; die **Sichtbarkeit**
ist der einzige verbleibende Blocker.

## 2. Diagnose der Handoff-Warnung "10/10 drafts (0 pub)" (MEASURED, 2026-07-19)

- Die Warnung stammt aus `scripts/publish_all.py` — das ist **Gumroad**-Vokabular
  (`/v2/products/{id}/enable`). Gumroad ist laut ADR-0010/0011 nur **Backup-Rail**.
- Die Live-Site (`docs/index.html` + Produktseiten) verlinkt **nicht** auf Gumroad, sondern auf
  Stripe `buy.stripe.com/...`-Links.
- Stripe-Status (MEASURED via API):
  - Account `acct_1TuRDH…`: `charges_enabled=True`, `payouts_enabled=True`, `country=DE`.
  - 13/13 Links aus `stripe_links.json` sind `active=True` + haben ein gültiges aktives Produkt
    (je 3,99 €). Beispiel-Link HTTP 200.
- **Fazit:** Die "drafts (0 pub)"-Meldung ist irreführend für den Sale-Pfad. Der Stripe-Kanal kann
  heute einen Sale annehmen. Der echte Engpass ist ausschließlich **Traffic**.

## 3. Kandidaten-Strategien (Kriterien aus Handoff §1: 0 Investment · Max Autonomie · schneller
   erster Umsatz-Beweis · skalierbar zum echten Business)

### K1 — SEO-Long-Tail vertiefen (Status quo, "geduldige" Variante)
- **Weg zu ersten Cents:** Mehr indexierte Produkt-/Themen-Landingpages (Long-Tail-Keywords wie
  "A Tale of Two Cities Zusammenfassung Kapitel 3"), in der Hoffnung auf organische Google-Treffer.
- **Nutzer-Aktionen:** keine (läuft passiv); nur bei Bedarf neuer LLM-Key für Study-Guide-Inhalt.
- **Autonomie:** hoch (Cron kann Seiten erzeugen), aber **Ergebnis hängt an Google-Indexierung**.
- **Skalierungspfad:** mehr Seiten → mehr Long-Tail-Abdeckung; prinzipiell unbegrenzt.
- **Größtes Risiko:** Google-Ranking für neue Domains dauert Monate; bisher 0 organischer Traffic
  nach Tagen (MEASURED). "Geduld" liefert den *Beweis* möglicherweise zu spät für das Velocity-Ziel.

### K2 — Marketplace mit eingebauter Discovery (Etsy / eBay / Amazon KDP)
- **Weg zu ersten Cents:** Produkt (Study-Guide / kuratierter PD-Begleiter) auf einen Marktplatz
  stellen, dessen Suche eigenen Traffic bringt — nicht erst auf externen SEO warten.
- **Nutzer-Aktionen:** **HARD STOP** — Account anlegen + Verkäufer-Verifizierung + Steuer/AGB
  (Etsy/EBay/Amazon) sind reine USER-Schritte. Agent bereitet Listings vor, stellt sie nicht live.
- **Autonomie:** niedrig bis Start (Account = USER), danach mittel (Listing-Text autonom).
- **Skalierungspfad:** mehrere Listings, Cross-Promos, eigene Shop-Struktur — echtes Business.
- **Größtes Risiko:** Konto-Freigabe dauert (Tage–Wochen), und PD/Public-Domain auf manchen
  Marktplätzen regelgebunden (KDP z.B. lehnt oft reinen PD-Text ab). First-Sale verzögert sich durch
  den USER-Account-Engpass.

### K3 — Eigen-Traffic durch kostenlosen Lead-Magneten (Quid-pro-Quo statt SEO warten)
- **Weg zu ersten Cents:** Eine **kostenlose**, wertvolle Ressource (z.B. "Kostenlose
  Cliffnotes-PDF zu 5 Klassikern") wird auf Plattformen geparkt, die Leser bringen OHNE dass der
  Agent öffentlich postet (z.B. in bestehende thematische Foren/Communities nur durch den USER,
  oder via E-Mail-Capture auf der eigenen Site). Der kostenlose Download fängt Leads; ein
  Upsell-Link auf die 3,99 €-Begleiter wandelt einen Bruchteil.
- **Nutzer-Aktionen:** Falls Promotion in Communities erfolgen soll = HARD STOP (öffentliches Posten
  ist freigabepflichtig, laut Charta NICHT erlaubt). Rein site-interner Lead-Magnet = autonom.
- **Autonomie:** hoch (Magnet + Landingpage + Upsell autonom), aber **Conversion braucht Besucher** —
  ohne externen Push ebenfalls Traffic-abhängig.
- **Skalierungspfad:** Magnet wird geteilt → E-Mail-Liste → wiederkehrender Kanal; Basis für echtes
  Marketing-Business.
- **Größtes Risiko:** Ohne erlaubtes externes Posten kommt niemand auf den Magnet → gleiches
  Traffic-Loch wie K1.

### K4 — "Schlüsselfertiges" Micro-Produkt auf Nachfrage (Concierge / Manuell-Validierung)
- **Weg zu ersten Cents:** Statt zu warten, wird das *Format* an einer einzigen, realen Anfrage
  validiert: ein fertiger Begleiter wird auf einer Plattform mit Sofort-Kauf (z.B. bereits live:
  Stripe-Link) beworben, wo auch ohne SEO Käufer entstehen können (z.B. Kleinanzeigen/Nischenforum
  durch USER, oder ein bereits bestehender Kanal des USER).
- **Nutzer-Aktionen:** **HARD STOP** — das "Ausspielen" in einen Kanal ist USER (öffentliches Posten).
- **Autonomie:** niedrig (jeder Sale braucht einen USER-Push) — verletzt Kriterium "Max Autonomie"
  fürs laufende Geschäft, taugt aber als **schnellster Einmal-Beweis**.
- **Skalierungspfad:** schlecht (jeder Sale = manuell) → kein Business-Pfad, nur Validierungs-Trick.
- **Größtes Risiko:** bleibt Einmal-Aktion, skaliert nicht; widerspricht Kriterium 4.

### K5 — Inhalts-Syndication mit eingebautem Monetarisierungs-Link (z.B. GitHub/Readme-Ökosystem)
- **Weg zu ersten Cents:** Die wertvollen Begleiter (Zusammenfassungen) werden als **kostenlose**
  Markdown-/HTML-Ressourcen breit verfügbar gemacht, JEDES mit einem dezenten "Vollversion + 30-Tage-
  Plan für 3,99 € (Stripe)"-Link. Wo immer sie gefunden werden, entsteht ein Kaufpfad — ohne dass der
  Agent aktiv postet, sofern der USER die Ressource einmal in einen passenden Ort stellt.
- **Nutzer-Aktionen:** das eine Mal "stellen" = HARD STOP; danach autonom pflegbar.
- **Autonomie:** mittel (Engine erzeugt die Begleiter; Reichweite braucht einmaligen USER-Seed).
- **Skalierungspfad:** je mehr kostenlose Begleiter existieren, desto mehr Embed-Potenzial → echtes
  Content-Marketing-Business.
- **Größtes Risiko:** Reichweite startet bei 0 bis der USER den ersten Seed setzt.

## 4. GRILL jeder Kandidatin (schriftlich)

- **K1:** Bringt sie den *ersten* Sale näher? — Nur indirekt (ranking braucht Zeit). Besteht GRILL?
  **NEIN** für das Velocity-Ziel "heute/bald", JA als passiver Dauerhebel.
- **K2:** Bringt sie den ersten Sale näher? — JA, Marktplatz-Suche = eingebauter Traffic. Besteht
  GRILL? **BEDINGT** — blockiert durch USER-Account-Hard-Stop (Tage–Wochen).
- **K3:** Bringt sie den ersten Sale näher? — Nur mit Besuchern. Besteht GRILL? **NEIN** ohne
  erlaubten externen Push (Charta sperrt autonomes Posten).
- **K4:** Bringt sie den ersten Sale näher? — JA, als schnellster Einmal-Beweis. Besteht GRILL?
  **NEIN** fürs Kriterium "Max Autonomie" + "skalierbar" (Einmal-Trick).
- **K5:** Bringt sie den ersten Sale näher? — JA, sobald ein kostenloser Begleiter gefunden wird.
  Besteht GRILL? **BEDINGT** — braucht einmaligen USER-Seed, danach autonom skalierbar.

## 5. Begründete EMPFEHLUNG

**Empfehlung: K1 als permanenten Dauerhebel BEIBEHALTEN (passiv, 0 Kosten) + K2 als
Haupt-Pivot für den ersten Umsatz-Beweis.** Begründung:

1. K1 erfüllt alle 4 Kriterien außer "schnell" — es ist der einzige *rein autonome* Hebel und muss
   nicht ausgeschaltet werden (Kosten = 0).
2. K2 ist die einzige Strategie, die **eingebauten Traffic** (Marktplatz-Suche) liefert statt auf
   externes SEO zu warten — und erfüllt Kriterium 3 (schneller Beweis) am besten, sobald der USER den
   Account-Hard-Stop bedient. Das ist der einzige echte Flaschenhals, und er liegt bewusst beim USER.
3. K4/K5 sind zu abhängig von manuellem USER-Push, um als *laufendes* Business zu taugen; K3 scheitert
   an der Charta (kein autonomes Posten).

**Honest caveat:** Der "schnelle erste Sale" hängt bei der Empfehlung an einem USER-Schritt
(Marktplatz-Account). Das ist kein Agent-Blocker, sondern die im Handoff §1(2) explizit erlaubte
"Engpass-Liste". Alles andere (Listings, Preise, Study-Guides, Fulfillment) kann der Agent autonom
vorbereiten, sobald der Account steht.

## 6. USER-Entscheidungsvorlage

Bitte eine Wahl treffen (keine weitere Arbeit ohne Entscheid — Handoff §3(4)):

1. **Empfehlung annehmen** — K1 passiv weiterlaufen + ich bereite K2 (Marketplace-Listings:
   Etsy/eBay) vollautonom vor, du legst nur den Verkäufer-Account an und gibst Frei. Schnellster
   realistischer Sale-Pfad.
2. **Alternative wählen** — du pickst K3/K4/K5 (oder mischst), ich baue die autonomen Teile.
3. **Ablehnen / eigenen Vorschlag** — du nennst die Richtung, ich grill sie erneut.

**Nicht bauen vor der Wahl.** Offene Blocker (WA-Bridge, 2h-Report-cfg) bleiben eigenständig zu fixen.
