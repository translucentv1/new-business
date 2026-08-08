#!/usr/bin/env python3
"""
TRAFFIC ENGINE — autonomer $0-SEO-Traffic fuer gig.html.
GitHub Pages (translucentv1.github.io/new-business) ist bei Google indexiert.
Jede hier erzeugte Landingpage targetiert echte DE-Suchintent und linkt auf gig.html.

Nutzung:
  python3 scripts/traffic_engine.py            # naechstes ungeschriebenes Keyword
  python3 scripts/traffic_engine.py "bewerbung schreiben lassen ki"
"""
import os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "blog")
GIG = "/new-business/gig.html"

# echte DE-Suchintents (kuratiert, MEASURED: diese Phrasen haben Bezahlwillen)
KEYWORDS = [
    ("bewerbung schreiben lassen ki", "Bewerbung schreiben lassen (KI)", "Eine uberzeugende Bewerbung, von KI geschrieben und in 24h geliefert."),
    ("notion template erstellen lassen", "Notion-Template erstellen lassen", "Individuelles Notion-Template, das genau deinen Workflow abbildet."),
    ("text schreiben lassen guenstig", "Text schreiben lassen – guenstig ab 3,99 EUR", "Blog, Produkttext oder E-Mail — fertig ab 3,99 EUR."),
    ("python skript erstellen lassen", "Python-Skript erstellen lassen", "Automatisierung, CSV/JSON, API — kleines Script, feste Preis."),
    ("study guide erstellen lassen", "Study-Guide erstellen lassen", "Zusammenfassung, Charaktere, Verstaendnisfragen zu jedem Buch."),
    ("instagram caption ki", "Instagram-Caption mit KI erstellen lassen", "Instagram/TikTok-Captions, die Klicks bringen."),
    ("hausarbeit schreiben lassen ki", "Hausarbeit schreiben lassen (KI-Entwurf)", "Struktur, Quellen, Gliederung – KI-Entwurf als Lernhilfe."),
    ("ebook cover erstellen lassen", "Ebook-Cover erstellen lassen", "Professionelles Cover fuer Self-Publishing, in 24h."),
    ("linkedin post schreiben lassen", "LinkedIn-Post schreiben lassen", "Posts, die Reichweite bringen – fuer Recruiter sichtbar."),
    ("expose schreiben lassen ki", "Expose schreiben lassen (KI)", "Verkaufsfertiges Expose fuer Vermieter und Makler."),
    ("quiz fragen erstellen lassen", "Quiz-Fragen erstellen lassen", "Für Schulung, Event oder Lead-Gen – fertige Fragen."),
    # 2026-07-28 Tick: Nachfrage ASSUMED (web_search blockiert, Firecrawl 402) — Intents analog zu bewerbung/text
    ("lebenslauf erstellen lassen ki", "Lebenslauf erstellen lassen (KI)", "Moderner, ATS-tauglicher Lebenslauf – von KI erstellt, geprueft, in 24h geliefert."),
    ("produktbeschreibung schreiben lassen", "Produktbeschreibung schreiben lassen", "Verkaufsstarke Produktbeschreibungen fuer Shopify, Etsy oder Amazon – Festpreis ab 3,99 EUR."),
    # 2026-07-28 Tick 2: Nachfrage ASSUMED (web_search weiterhin 402) — Intents analog zu produktbeschreibung/text
    ("newsletter schreiben lassen", "Newsletter schreiben lassen", "E-Mail-Newsletter, der geoeffnet wird – Betreff, Text, CTA, fertig in 24h ab 3,99 EUR."),
    ("excel tabelle erstellen lassen", "Excel-Tabelle erstellen lassen", "Tabelle mit Formeln, Auswertung oder Dashboard – fertig aufgebaut, in 24h geliefert."),
    # 2026-08-01 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, DE).
    # "powerpoint erstellen lassen" -> Vorschlaege u.a. "...ki", "...kosten",
    # "...fuer 10 EUR"  => Bezahlwille belegt, Preisniveau passt zu 3,99-14,99 EUR.
    ("powerpoint erstellen lassen ki", "PowerPoint erstellen lassen (KI)", "Fertige Praesentation mit Struktur, Text und Sprechernotizen – ab 3,99 EUR, in 24h geliefert."),
    # "businessplan erstellen lassen" -> Vorschlaege u.a. "...ki", "...kosten",
    # "...professionell"  => kommerzieller Intent belegt.
    ("businessplan erstellen lassen ki", "Businessplan erstellen lassen (KI)", "Gliederung, Marktanalyse und Finanzteil als Entwurf – guenstiger Festpreis statt Berater-Stundensatz."),
    # 2026-08-01 Tick 2: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, hl=de/gl=de).
    # "anschreiben erstellen lassen" -> 7 Vorschlaege, u.a. "...ki", "...professionell",
    # "...bewerbung"  => kommerzieller Intent + KI-Akzeptanz belegt. Deliverable = reiner Text.
    ("anschreiben erstellen lassen ki", "Anschreiben erstellen lassen (KI)", "Professionelles Bewerbungs-Anschreiben, auf die Stellenanzeige zugeschnitten – ab 3,99 EUR, in 24h."),
    # "rede schreiben lassen" -> 7 Vorschlaege, u.a. "...ki", "...ki kostenlos",
    # "trauzeugin rede schreiben lassen"  => Anlassrede = hohe Zahlungsbereitschaft, Deliverable = reiner Text.
    ("rede schreiben lassen ki", "Rede schreiben lassen (KI)", "Hochzeit, Geburtstag, Firmenfeier oder Trauzeugen-Rede: fertiger Redetext mit Aufbau und Pointen, ab 3,99 EUR."),
    # 2026-08-01 Tick 3: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, hl=de/gl=de).
    # "protokoll schreiben lassen" -> 6 Vorschlaege ("...ki", "chatgpt...", "copilot...",
    # "teams protokoll schreiben lassen"); "meeting protokoll ki" -> 9 Vorschlaege
    # (teams, zoom, deutsch, dsgvo, app)  => B2B-Intent + KI-Akzeptanz belegt.
    # Deliverable = reiner Text (Ollama, 0 EUR).
    ("protokoll schreiben lassen ki", "Meeting-Protokoll schreiben lassen", "Aus deinen Stichpunkten oder dem Transkript ein sauberes Protokoll: Teilnehmer, Beschluesse, To-dos mit Verantwortlichen – ab 3,99 EUR, in 24h."),
    # "motivationsschreiben ki" -> 10 Vorschlaege (u.a. "...generator"),
    # "motivationsschreiben schreiben lassen" -> "...ki"  => Bewerbungs-Intent belegt,
    # passt zum bereits laufenden Cluster Bewerbung/Anschreiben/Lebenslauf.
    ("motivationsschreiben schreiben lassen ki", "Motivationsschreiben schreiben lassen", "Studium, Stipendium oder Job: individuelles Motivationsschreiben auf deine Ausschreibung zugeschnitten – ab 3,99 EUR, in 24h."),
    # 2026-08-02 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, hl=de/gl=de).
    # "blogartikel schreiben lassen" -> 2 Vorschlaege, darunter explizit
    # "seo blogartikel schreiben lassen"  => B2B-Intent (Firmen kaufen SEO-Texte ein),
    # KEIN "kostenlos"-Modifier in den Vorschlaegen = Bezahlwille. Deliverable = reiner Text.
    ("seo blogartikel schreiben lassen", "SEO-Blogartikel schreiben lassen", "Keyword-optimierter Blogartikel mit Struktur, Zwischenueberschriften und Meta-Description – ab 3,99 EUR, in 24h geliefert."),
    # "website texte schreiben lassen" -> 2 Vorschlaege ("...", "texte fuer website schreiben lassen").
    # Ebenfalls B2B / Selbstaendige, kein "kostenlos"-Modifier. Deliverable = reiner Text.
    ("website texte schreiben lassen", "Website-Texte schreiben lassen", "Startseite, Ueber-mich und Leistungen: verkaufsstarke Website-Texte in deiner Tonalitaet – ab 3,99 EUR, in 24h."),
    # 2026-08-03 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, hl=de/gl=de).
    # "arbeitszeugnis schreiben lassen" -> 10 Vorschlaege, u.a. "...ki", "...kosten",
    # "...professionell", "...geschaeftsfuehrer", "chatgpt arbeitszeugnis schreiben lassen"
    # => staerkstes Signal dieses Ticks: kommerzieller Intent (kosten/professionell) UND
    # KI-Akzeptanz explizit in den Vorschlaegen. Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung: Formulierungs-Entwurf, KEINE Rechtsberatung (siehe Seitenhinweis).
    ("arbeitszeugnis schreiben lassen ki", "Arbeitszeugnis schreiben lassen (KI-Entwurf)", "Qualifiziertes Arbeitszeugnis als fertiger Formulierungs-Entwurf – wohlwollend, branchenueblich, ab 3,99 EUR in 24h."),
    # "pressemitteilung schreiben lassen" -> 2 Vorschlaege, darunter explizit
    # "...kosten" (KEIN "kostenlos"-Modifier) => B2B-Bezahlwille belegt, gleiches
    # Signalniveau wie "seo blogartikel"/"website texte" (je 2 Treffer, beide live).
    ("pressemitteilung schreiben lassen", "Pressemitteilung schreiben lassen", "Presse-Text nach Redaktions-Standard: Headline, Lead, Zitat, Boilerplate – ab 3,99 EUR, in 24h geliefert."),
    # 2026-08-03 Tick 2: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, hl=de/gl=de).
    # "korrekturlesen lassen" -> 10 Vorschlaege, KEIN einziger "kostenlos"-Modifier:
    # "bachelorarbeit/masterarbeit/doktorarbeit/projektarbeit korrekturlesen lassen",
    # "...duden", "...schreibweise", "chatgpt korrekturlesen lassen"
    # => staerkstes Signal dieses Ticks: bezahlter Dienstleistungsmarkt (Lektorat)
    # + KI-Akzeptanz. Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung: SPRACHLICHE Korrektur, kein Schreiben von Pruefungsleistungen.
    ("korrekturlesen lassen ki", "Korrekturlesen lassen (KI)", "Rechtschreibung, Grammatik, Zeichensetzung und Stil – dein Text sauber korrigiert, ab 3,99 EUR in 24h."),
    # "zusammenfassung schreiben lassen" -> 5 Vorschlaege, darunter "...ki",
    # "chatgpt zusammenfassung schreiben lassen pdf" => KI-Akzeptanz explizit.
    # Einschraenkung ehrlich notiert: 1 Vorschlag enthaelt "kostenlos" (schwaecherer
    # Bezahlwille als korrekturlesen). Deliverable = reiner Text.
    ("zusammenfassung schreiben lassen ki", "Zusammenfassung schreiben lassen (KI)", "Aus PDF, Buch, Studie oder Meeting-Text eine praezise Zusammenfassung – ab 3,99 EUR, in 24h geliefert."),
    # 2026-08-04 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, hl=de/gl=de).
    # "kuendigung schreiben lassen" -> 5 Vorschlaege, KEIN "kostenlos"-Modifier:
    # "ki kuendigungsschreiben lassen", "kuendigung vom anwalt schreiben lassen",
    # "kuendigung krankschreiben lassen" => es existiert ein BEZAHLTER Markt
    # (Anwalt als Preisanker) UND KI-Akzeptanz. Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung (RDG): nur Formulierungs-Vorlage, KEINE Rechtsberatung, KEINE Fristenpruefung.
    ("kuendigung schreiben lassen ki", "Kuendigung schreiben lassen (KI-Vorlage)", "Kuendigungsschreiben fuer Vertrag, Abo oder Mitgliedschaft als fertige Formulierungs-Vorlage – ab 3,99 EUR, in 24h."),
    # "flyer erstellen lassen" -> 10 Vorschlaege (Maximum dieses Ticks): "...kosten",
    # "...ki", "...in der naehe", "...berlin", "...hamburg", "...noerdlingen", "...online"
    # => lokaler Dienstleistungsmarkt mit Preisrecherche ("kosten") = starker Bezahlwille.
    # Einschraenkung ehrlich notiert: 2 der 10 Vorschlaege enthalten "kostenlos".
    # Deliverable ehrlich abgegrenzt: Flyer-TEXT + Aufbau, kein druckfertiges Grafik-Layout.
    ("flyer erstellen lassen ki", "Flyer erstellen lassen (KI) – Text & Aufbau", "Headline, Nutzenargumente, Call-to-Action und Aufbau fuer deinen Flyer – textfertig ab 3,99 EUR, in 24h."),
    # 2026-08-04 Tick 2: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete, hl=de/gl=de).
    # web_search/Firecrawl war in diesem Tick nicht verfuegbar (HTTP 402, insufficient
    # funds) -> Autocomplete ist die einzige MEASURED-Quelle, kein ASSUMED-Keyword.
    # "bericht schreiben lassen" -> 3 Vorschlaege: "...ki", "chatgpt bericht schreiben
    # lassen". KEIN einziger "kostenlos"-Modifier => sauberster Bezahlwille dieses Ticks
    # UND explizite KI-Akzeptanz. Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung: Geschaefts-/Projekt-/Taetigkeitsberichte. KEINE Praktikums- oder
    # Studienberichte zur Abgabe (Pruefungsleistung) - siehe Seitenhinweis.
    ("bericht schreiben lassen ki", "Bericht schreiben lassen (KI)", "Projektbericht, Taetigkeitsbericht oder Monatsreport: sauber gegliedert aus deinen Stichpunkten – ab 3,99 EUR, in 24h."),
    # "vortrag erstellen lassen" -> 2 Vorschlaege ("...", "...ki"), KEIN "kostenlos"-
    # Modifier. Gleiches Signalniveau wie "pressemitteilung"/"seo blogartikel"/
    # "website texte" (je 2 Treffer, alle live) => Bar erfuellt, KI-Akzeptanz explizit.
    # Abgrenzung zu powerpoint-Seite: hier Redetext + Aufbau, dort Folien.
    ("vortrag erstellen lassen ki", "Vortrag erstellen lassen (KI)", "Vortrag mit rotem Faden: Einstieg, Argumente, Schluss und Sprechernotizen – ab 3,99 EUR, in 24h geliefert."),
    # BEWUSST ABGELEHNT (2026-08-04 Tick 2): "text umschreiben lassen" hatte mit 10
    # Vorschlaegen das groesste Volumen dieses Ticks, wird aber NICHT gebaut. Die
    # Modifier zeigen, dass die Nachfrage ueberwiegend auf etwas zielt, das wir nicht
    # verkaufen: "ohne plagiat", "humanisieren", "menschlich" und woertlich "ki text
    # umschreiben lassen dass er nicht erkannt wird" = Umgehung von KI-/Plagiatspruefung.
    # Das waere Taeuschung (und bei Pruefungsleistungen ToS-/pruefungsrechtlich heikel).
    # Ebenfalls abgelehnt: "praktikumsbericht schreiben lassen" (2 Treffer, aber
    # Pruefungsleistung zur Abgabe) und "gedicht"/"songtext" (4-7 Treffer, aber
    # 2-4 davon "kostenlos" = kein Bezahlwille).
    # 2026-08-04 Tick 3: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete,
    # hl=de/gl=de). web_search/Firecrawl erneut HTTP 402 (insufficient_funds) -> Autocomplete
    # bleibt die einzige MEASURED-Quelle; kein ASSUMED-Keyword gebaut.
    # "hochzeitsrede schreiben lassen" -> 3 Vorschlaege: "...kosten" (Preisrecherche =
    # Bezahlwille) und woertlich "hochzeitsrede von ki schreiben lassen" (KI-Akzeptanz
    # explizit). KEIN "kostenlos"-Modifier. Anlassrede = hoechste Zahlungsbereitschaft
    # im Rede-Cluster. Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung zur generischen rede-Seite: hier nur Hochzeit (Braut/Braeutigam,
    # Trauzeuge, Eltern), dort alle uebrigen Anlaesse.
    ("hochzeitsrede schreiben lassen", "Hochzeitsrede schreiben lassen", "Rede fuer Braut, Braeutigam, Trauzeuge oder Eltern: persoenliche Anekdoten, Aufbau, Pointen und Timing – ab 3,99 EUR, in 24h."),
    # "pitch deck erstellen lassen" -> 2 Vorschlaege, darunter explizit "...kosten",
    # KEIN "kostenlos"-Modifier => B2B/Startup-Bezahlwille belegt, gleiches Signalniveau
    # wie "pressemitteilung"/"vortrag"/"website texte" (je 2 Treffer, alle live).
    # Deliverable EHRLICH abgegrenzt: Slide-TEXTE + Storyline + Sprechernotizen,
    # KEIN Grafik-Design und KEIN Finanzmodell/keine Anlageberatung.
    ("pitch deck erstellen lassen", "Pitch-Deck erstellen lassen – Texte & Storyline", "Storyline und fertige Slide-Texte fuer Problem, Loesung, Markt, Team und Ask – ab 3,99 EUR, in 24h."),
    # BEWUSST ABGELEHNT (2026-08-04 Tick 3):
    # - "text uebersetzen lassen" (10 Vorschlaege = groesstes Volumen des Ticks): Modifier
    #   sind "google", "kostenlos", "foto", "whatsapp", "chatgpt", "pdf" => der Sucher will
    #   ein kostenloses TOOL, keinen bezahlten Dienstleister. Falscher Intent.
    # - "handout erstellen lassen" (8): 2x "kostenlos", zusaetzlich "powerpoint handout"/
    #   "handout aus praesentation" = Ableitung aus vorhandener Datei, deckt die
    #   bestehende powerpoint-Seite bereits ab.
    # - "referat schreiben lassen" (3): 1x "kostenlos" UND Pruefungsleistung zur Abgabe.
    # - "konzept erstellen lassen" (3): Top-Modifier ist "haccp konzept" =
    #   Lebensmittelhygiene-Pflichtdokument; koennen wir nicht verantwortlich liefern.
    # - 0-1 Treffer (kein Signal): elevator pitch, swot analyse, geschaeftsbrief,
    #   anleitung, bedienungsanleitung, marktanalyse, stellenbeschreibung,
    #   unternehmensprofil, werbetext, social media posts, schulungsunterlagen,
    #   interview fragen, email vorlage, podcast skript.
    # 2026-08-05 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete,
    # hl=de/gl=de). web_search/Firecrawl erneut HTTP 402 (insufficient_funds) ->
    # Autocomplete bleibt die einzige MEASURED-Quelle; kein ASSUMED-Keyword gebaut.
    # "trauerrede schreiben" -> 10 Vorschlaege (Maximum dieses Ticks), KEIN "kostenlos":
    # woertlich "trauerrede schreiben ki" (KI-Akzeptanz explizit) plus die
    # Angehoerigen-Modifier mutter/vater/opa/oma/bruder/freund => konkreter Anlass,
    # hoher Zeitdruck, hohe Zahlungsbereitschaft. Deliverable = reiner Text (Ollama, 0 EUR).
    # Ehrlich notiert: 1 der 10 Vorschlaege ist "...beispiel" (Vorlagen-Sucher).
    # Abgrenzung zu rede-/hochzeitsrede-Seite: hier ausschliesslich Trauerfall.
    ("trauerrede schreiben ki", "Trauerrede schreiben lassen (KI)", "Einfuehlsame Trauerrede fuer Mutter, Vater, Grosseltern oder Freund – Aufbau, Anekdoten, Schlussworte, ab 3,99 EUR in 24h."),
    # "speisekarte erstellen lassen" -> 3 Vorschlaege: "...kosten" (Preisrecherche =
    # Bezahlwille) und "...ki" (KI-Akzeptanz), KEIN "kostenlos"-Modifier.
    # Gastro-Markt, gleiches Signalniveau wie "bericht" (3 Treffer, live).
    # Deliverable EHRLICH abgegrenzt: Gerichts-TEXTE und Karten-Aufbau, KEIN
    # druckfertiges Layout und KEINE rechtsverbindliche Allergen-/Zusatzstoff-Kennzeichnung.
    ("speisekarte erstellen lassen ki", "Speisekarte erstellen lassen (KI) – Texte & Aufbau", "Appetitliche Gerichtsbeschreibungen, Kategorien und Karten-Aufbau fuer Restaurant, Cafe oder Foodtruck – ab 3,99 EUR, in 24h."),
    # BEWUSST ABGELEHNT (2026-08-05 Tick):
    # - "text erstellen lassen" (10 Treffer = groesstes Volumen): 3 Modifier sind
    #   "kostenlos"/"ohne anmeldung", dazu "rap"/"suno" (Songtexte) => der Sucher will
    #   ein Gratis-Tool, keinen bezahlten Dienstleister. Deckt zudem die bestehende
    #   Seite text-schreiben-lassen-guenstig ab.
    # - "gliederung erstellen lassen" (6): enthaelt "...kostenlos" UND 2x
    #   Hausarbeit/Bachelorarbeit = Pruefungsleistung zur Abgabe -> gleiche Linie wie
    #   die frueher abgelehnten praktikumsbericht/referat-Keywords.
    # - "ki dienstleistungen" (6) und "freelancer ki jobs" (10): falsche Marktseite —
    #   das sind Leute, die KI-Leistungen ANBIETEN bzw. Jobs suchen, keine Kaeufer.
    # - "ki auftrag*" (10): B2B-Softwarebegriffe (Auftragsverarbeitung/DSGVO-AVV),
    #   kein Text-Kaufintent.
    # - "angebot erstellen lassen" (4): Modifier amazon/bauhaus/hornbach => Nutzer will
    #   ein Preisangebot VON einem Haendler, kein geschriebenes Angebotsdokument.
    # - 0-1 Treffer (kein Signal): trauerrede schreiben lassen, danksagung, abschiedsrede,
    #   geburtstagsrede, faq, checkliste, social media plan, content plan, grusswort,
    #   wohnungsbewerbung, stellenanzeige, whitepaper, landingpage text, amazon listing,
    #   produkttext, elternbrief, einladung text, bewertung antworten, kondolenzschreiben,
    #   laudatio, ausschreibung.
    # 2026-08-05 Tick 2: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete,
    # hl=de/gl=de), Rohausgabe im Report protokolliert.
    # "biografie schreiben lassen" -> 7 Vorschlaege, KEIN "kostenlos"-Modifier:
    # Top-Vorschlag ist woertlich "...kosten" (Preisrecherche = Bezahlwille), dazu
    # "biografie von ki schreiben lassen" (KI-Akzeptanz explizit) und die Ortsmodifier
    # berlin/schweiz/oesterreich (= es existiert ein bezahlter Ghostwriter-Markt).
    # Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung EHRLICH: Kurzbiografie / Ueber-mich-Text / Kapitel-Gliederung,
    # KEIN komplettes Buch-Ghostwriting (das ist zum Festpreis nicht lieferbar).
    ("biografie schreiben lassen", "Biografie schreiben lassen", "Lebensgeschichte als fertiger Text: Kurzbiografie, Ueber-mich-Text oder Kapitel-Gliederung fuer das eigene Buchprojekt – ab 3,99 EUR, in 24h."),
    # "trainingsplan erstellen lassen" -> 10 Vorschlaege (Maximum dieses Ticks):
    # "...kosten" (Preisrecherche), "...ki" (KI-Akzeptanz), "individuellen trainingsplan
    # erstellen lassen" und die Studioketten mcfit/fitx/gym => es existiert ein
    # BEZAHLTER Markt mit klarem Preisanker. Ehrlich notiert: 1 der 10 Vorschlaege
    # ist "...kostenlos". Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung EHRLICH: allgemeiner Trainingsplan-Entwurf, KEINE medizinische,
    # physiotherapeutische oder Ernaehrungs-Beratung (siehe Seitenhinweis).
    ("trainingsplan erstellen lassen ki", "Trainingsplan erstellen lassen (KI)", "Wochenplan mit Uebungen, Saetzen, Wiederholungen und Progression fuer dein Ziel – als Text-Entwurf ab 3,99 EUR, in 24h."),
    # BEWUSST ABGELEHNT (2026-08-05 Tick 2):
    # - "buch schreiben lassen" (10 Treffer = groesstes Volumen): 3 Modifier sind
    #   "kostenlos"/"ki ... kostenlos deutsch", der Rest zielt auf Ghostwriter-
    #   Komplettprojekte (mehrere hundert Seiten) -> zum Festpreis 3,99-14,99 EUR
    #   nicht ehrlich lieferbar. Der bezahlbare Teil davon ist als "biografie"
    #   (Gliederung/Kurztext) abgedeckt.
    # - "wikipedia artikel schreiben lassen" (2, davon "...kosten"): bezahltes
    #   Schreiben ist bei Wikipedia offenlegungspflichtig/ToS-heikel -> Regel (2).
    # - "mahnung schreiben lassen" (2): zweiter Vorschlag ist "anwalt mahnung
    #   schreiben lassen" = Rechtsdienstleistung (RDG), nicht unser Deliverable.
    # - "lernplan erstellen lassen" (4): brauchbares Signal, aber 1x "kostenlos" und
    #   inhaltlich stark ueberlappend mit study-guide/zusammenfassung -> zurueckgestellt.
    # - "kochbuch erstellen lassen" (2): zweiter Vorschlag "...und drucken lassen"
    #   = Druckdienstleistung, koennen wir nicht liefern.
    # - 0-1 Treffer (kein Signal): klappentext, slogan, sachbuch, hoerbuch skript,
    #   verkaufstext, landingpage texte, immobilienanzeige, youtube skript,
    #   buchbeschreibung, amazon produkttext, hochzeitseinladung text, reiseplan,
    #   excel formel, steckbrief, chatgpt prompt, jobinterview vorbereitung ki,
    #   gehaltsverhandlung vorbereiten.
    # 2026-08-05 Tick 3: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete,
    # hl=de/gl=de). web_search/Firecrawl erneut HTTP 402 (insufficient_funds) ->
    # Autocomplete bleibt die einzige MEASURED-Quelle; kein ASSUMED-Keyword gebaut.
    # "arbeitsblatt erstellen lassen" -> 6 Vorschlaege, KEIN "kostenlos"-Modifier:
    # woertlich "...ki" (KI-Akzeptanz explizit), "fobizz ..." und "canva ..."
    # (= es existiert ein BEZAHLTER Tool-Markt, Preisanker) sowie "arbeitsblatt zu
    # video / zu youtube video erstellen lassen" (konkreter Arbeitsauftrag).
    # Zielgruppe Lehrkraefte/Nachhilfe. Deliverable = reiner Text (Ollama, 0 EUR).
    # Abgrenzung EHRLICH: Aufgabentext + Loesungen als Text, KEIN druckfertiges
    # Layout und keine Lizenz an fremden Schulbuch-/Verlagsinhalten.
    ("arbeitsblatt erstellen lassen ki", "Arbeitsblatt erstellen lassen (KI)", "Aufgaben, Loesungen und Arbeitsauftraege zu deinem Thema oder Text – fertig formuliert fuer Unterricht und Nachhilfe, ab 3,99 EUR in 24h."),
    # "lernplan erstellen lassen" -> 4 Vorschlaege: "...ki" und "lernplan von chatgpt
    # erstellen lassen" (KI-Akzeptanz doppelt belegt). Ehrlich notiert: 1 der 4
    # Vorschlaege ist "...kostenlos" (schwaecherer Bezahlwille als arbeitsblatt).
    # Im Tick 2 zurueckgestellt wegen Ueberlappung mit study-guide — Abgrenzung ist
    # jetzt sauber: Lernplan = ZEITplan (Wochenaufteilung, Reihenfolge, Puffer bis
    # zum Pruefungstermin), study-guide/zusammenfassung = INHALT. Keine
    # Pruefungsleistung zur Abgabe -> die eigene Lernzeit zu planen ist keine Taeuschung.
    ("lernplan erstellen lassen ki", "Lernplan erstellen lassen (KI)", "Realistischer Lernplan bis zum Pruefungstermin: Wochenaufteilung, Reihenfolge der Themen, Wiederholungen und Puffer – ab 3,99 EUR, in 24h."),
    # BEWUSST ABGELEHNT (2026-08-05 Tick 3):
    # - "ernaehrungsplan erstellen lassen" (10 Treffer = groesstes Volumen des Ticks,
    #   mit "...kosten"/"professionellen" = klarer Preisanker): WIRD NICHT GEBAUT.
    #   Die bereits live stehende Seite trainingsplan-erstellen-lassen-ki.html sagt
    #   woertlich zu, dass wir "keine medizinische, physiotherapeutische oder
    #   Ernaehrungs-Beratung" liefern, und docs/fiverr_gig.md schliesst
    #   medizinberatende Texte aus. Eine Ernaehrungsplan-Seite wuerde dieser
    #   Zusage widersprechen. Zusaetzlich zielen 2 Modifier ("barf", "hund") auf
    #   Tier-Ernaehrung (Veterinaerbereich).
    # - "brief schreiben lassen" (10 Treffer): falscher Intent. Die Modifier
    #   "handschriftlich", "kalligraphie", "schoen schreiben" verlangen eine
    #   HANDSCHRIFT-Dienstleistung (koennen wir nicht liefern), "anwalt brief
    #   schreiben lassen (kosten)" ist Rechtsdienstleistung (RDG). Dazu 1x "kostenlos".
    # - "roman schreiben lassen" (3): Komplett-Ghostwriting eines Romans ist zum
    #   Festpreis 3,99-14,99 EUR nicht ehrlich lieferbar (gleiche Linie wie das
    #   frueher abgelehnte "buch schreiben lassen").
    # - 0-1 Treffer (kein Signal): unterrichtsentwurf, leitbild, jahresbericht,
    #   spendenaufruf, etsy listing, tiktok skript, beschwerde, instagram bio,
    #   google ads text, hochzeitszeitung, onboarding unterlagen, uebungsaufgaben,
    #   klassenarbeit, dankesrede, trauerkarte text, geschaeftsbericht,
    #   immobilienbeschreibung.
    # 2026-08-06 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete,
    # hl=de/gl=de). web_search/Firecrawl erneut HTTP 402 (insufficient_funds, Rohfehler
    # im Report) -> Autocomplete bleibt die einzige MEASURED-Quelle; kein ASSUMED-Keyword.
    # "e-mail schreiben lassen" -> 3 Vorschlaege, KEIN "kostenlos"-Modifier:
    # "e mail schreiben lassen ki" UND "chat gpt e mail schreiben lassen"
    # => KI-Akzeptanz doppelt belegt (2 von 3 Vorschlaegen nennen ein KI-Tool).
    # Deliverable = reiner Text (Ollama, 0 EUR), keine Ueberlappung mit einer
    # bestehenden Seite (das frueher gepruefte "email vorlage" hatte 0-1 Treffer).
    # Abgrenzung EHRLICH: Geschaefts-/Bewerbungs-/Beschwerde-E-Mail als Formulierung,
    # KEIN Versand, KEIN Rechts- oder Forderungsschreiben (RDG).
    ("e mail schreiben lassen ki", "E-Mail schreiben lassen (KI)", "Geschaefts-, Bewerbungs- oder Beschwerde-E-Mail: hoeflich, klar und im richtigen Ton formuliert – ab 3,99 EUR, in 24h."),
    # "bewerbungsunterlagen erstellen lassen" -> 3 Vorschlaege, KEIN "kostenlos":
    # "...professionell erstellen lassen" (Bezahlwille explizit) und "...schweiz"
    # (Ortsmodifier = es existiert ein bezahlter Dienstleistermarkt).
    # Bewusst als BUENDEL-Seite gebaut, nicht als Dublette: bewerbung/anschreiben/
    # lebenslauf decken je EIN Einzeldokument ab, diese Seite den kompletten Satz
    # (Anschreiben + Lebenslauf + Kurzprofil) und zielt damit auf das 14,99-EUR-Paket.
    # Deliverable = reiner Text (Ollama, 0 EUR). Abgrenzung EHRLICH: Textinhalt,
    # KEIN Grafik-/Deckblatt-Layout und keine Zeugnis-Beschaffung.
    ("bewerbungsunterlagen erstellen lassen", "Bewerbungsunterlagen erstellen lassen", "Kompletter Bewerbungssatz: Anschreiben, Lebenslauf und Kurzprofil aus einem Guss, auf die Stellenanzeige zugeschnitten – ab 3,99 EUR, in 24h."),
    # BEWUSST ABGELEHNT (2026-08-06 Tick):
    # - "artikel schreiben lassen" (6 Treffer = groesstes Volumen des Ticks, mit
    #   "...ki"/"chatgpt..."): der Bezahl-Teil davon ist bereits als
    #   seo-blogartikel-schreiben-lassen live ("blog artikel schreiben lassen" ist
    #   woertlich einer der Vorschlaege) -> Dublette/Kannibalisierung. Der Rest ist
    #   "wikipedia artikel schreiben lassen (kosten)", schon frueher wegen
    #   Offenlegungspflicht/ToS abgelehnt (Regel 2).
    # - "rechnung erstellen lassen" (6): falscher Intent. Modifier ikea/amazon/db/
    #   paypal/e-rechnung => der Sucher will eine Rechnung VON einem Haendler bzw.
    #   ein E-Rechnungs-Tool, kein geschriebenes Dokument (gleiche Linie wie das
    #   frueher abgelehnte "angebot erstellen lassen").
    # - "kinderbuch schreiben lassen" (3): "...und drucken lassen" = Druckleistung,
    #   der Rest ist Komplett-Ghostwriting -> zum Festpreis 3,99-14,99 EUR nicht
    #   ehrlich lieferbar (gleiche Linie wie buch/roman schreiben lassen).
    # - "portfolio erstellen lassen" (3): Top-Modifier "architektur portfolio" =
    #   Grafik-/Layout-Arbeit, die wir ausdruecklich nicht liefern.
    # - 0-1 Treffer (kein Signal): sop, prozessbeschreibung, leitfaden,
    #   schulungsunterlagen, jubilaeumsrede, abschiedsbrief, gute nacht geschichte,
    #   podcast skript, youtube video skript, werbetext ki, linkedin profil
    #   optimieren, onlinekurs, drehbuch, ratgeber.
    # 2026-08-06 Tick 2: Nachfrage MEASURED via scripts/kw_demand.py (Google
    # Autocomplete, hl=de/gl=de). web_search/Firecrawl erneut HTTP 402
    # (insufficient_funds) -> Autocomplete bleibt die einzige MEASURED-Quelle.
    # "prompt erstellen lassen" -> 3 Vorschlaege, **0x "kostenlos"**, davon 2 mit
    # KI-Tool-Modifier ("chatgpt prompt erstellen lassen", "ki prompt erstellen
    # lassen") => Zielgruppe nutzt KI bereits aktiv und sucht trotzdem nach einem
    # Dienstleister. Deliverable = reiner Text (Ollama, 0 EUR), keine Dublette:
    # bisher deckt keine Seite den KI-/Automations-Intent ab.
    # Abgrenzung EHRLICH: fertiger Prompt inkl. Rollen-/Kontextteil, Variablen und
    # Beispiel-Output — KEIN Modell-Finetuning, KEIN Account-Zugang, keine Garantie
    # auf ein bestimmtes Modellergebnis.
    ("prompt erstellen lassen ki", "Prompt erstellen lassen (ChatGPT & Co.)", "Massgeschneiderter Prompt fuer ChatGPT, Claude oder Gemini: Rolle, Kontext, Variablen und Beispiel-Output – ab 3,99 EUR, in 24h."),
    # "liebesbrief schreiben lassen" -> 2 Vorschlaege, **0x "kostenlos"**, darunter
    # "ki liebesbrief schreiben lassen" => KI-Akzeptanz belegt, kein Gratis-Modifier.
    # Passt in den bestehenden Anlass-Cluster (Hochzeitsrede/Trauerrede/Biografie),
    # der dieselbe Zahlungsbereitschaft bedient. Deliverable = reiner Text aus den
    # Stichpunkten des Kaeufers. Abgrenzung EHRLICH: persoenlicher Brieftext,
    # KEIN Versand, keine Handschrift/Kalligrafie, kein Layout.
    ("liebesbrief schreiben lassen", "Liebesbrief schreiben lassen", "Persoenlicher Brief aus deinen Stichpunkten: eigener Ton, echte Details, kein Textbaustein-Kitsch – ab 3,99 EUR, in 24h."),
    # 2026-08-06 Tick 3: Nachfrage MEASURED via scripts/kw_demand.py
    # (Google Autocomplete, hl=de/gl=de). web_search steht NICHT zur Verfuegung
    # (Firecrawl HTTP 402 BILLING_ERROR, MEASURED in diesem Tick) -> Autocomplete
    # bleibt die einzige $0-Nachfragequelle.
    # "brief schreiben lassen" -> 10 Vorschlaege (= Maximum), nur 1 davon mit
    # "kostenlos". Preisanker im Markt belegt: "anwalt brief schreiben lassen
    # kosten". KI-Akzeptanz belegt: "brief schreiben lassen ki", "chatgpt brief
    # schreiben lassen". Abgrenzung EHRLICH direkt auf der Seite: wir liefern den
    # BRIEFTEXT als Datei — KEINE Handschrift/Kalligrafie (Modifier
    # "handschriftlich"/"kalligraphie"), KEIN Versand, KEINE Rechtsberatung
    # (Modifier "anwalt" -> RDG).
    ("brief schreiben lassen", "Brief schreiben lassen", "Privat oder geschaeftlich: fertiger Brieftext aus deinen Stichpunkten – richtiger Ton, klarer Aufbau, ab 3,99 EUR in 24h."),
    # "text formulieren lassen" -> 4 Vorschlaege, **0x "kostenlos"**:
    # "ki text formulieren lassen", "text besser formulieren lassen",
    # "chatgpt text formulieren lassen" => Umformulieren ist ein eigener Intent
    # (vorhandener Text wird verbessert) und damit NICHT deckungsgleich mit
    # "korrekturlesen" (Fehler korrigieren) oder "text schreiben lassen" (neu
    # schreiben). Deliverable = reiner Text, zu 100% lieferbar.
    ("text formulieren lassen", "Text besser formulieren lassen", "Dein Entwurf, professionell umformuliert: klarer, hoeflicher, ueberzeugender – Inhalt bleibt deiner, ab 3,99 EUR in 24h."),
    # BEWUSST ABGELEHNT (2026-08-06 Tick 3):
    # - "buch schreiben lassen" (10 = Maximum, mit "kosten"/"ghostwriter"):
    #   ein ganzes Buch ist zu 3,99-14,99 EUR NICHT ehrlich lieferbar
    #   (Over-Promise) -> abgelehnt trotz groesstem Volumen.
    # - "ernaehrungsplan erstellen lassen" (10, mit "kosten"/"professionellen"):
    #   Gesundheits-/Ernaehrungsberatung, dazu 2 Tier-Modifier ("hund", "barf").
    #   Zurueckgestellt bis geklaert ist, wie ein Text-Entwurf ohne
    #   Beratungsanschein formuliert wird.
    # - "dienstplan erstellen lassen" (3, 0x kostenlos): Suchintent zielt auf
    #   SOFTWARE/Automatik ("automatisch", "von ki"), nicht auf einen Textentwurf.
    # - Gratis-Modifier enthalten: essay (3, 1x), referat (3, 1x).
    # - 0-1 Treffer (kein Signal): danksagung, social media plan, angebot
    #   schreiben, klappentext, werbetext, slogan, amazon listing, checkliste,
    #   youtube skript, erklaervideo skript, empfehlungsschreiben, onlinekurs,
    #   stellenbeschreibung, antrag (nur "psychotherapie antrag").
    # - "handbuch erstellen lassen" (2): bereits im Vor-Tick abgelehnt
    #   (QM/ISO-9001 nicht zum Festpreis lieferbar) — Ablehnung bestaetigt.
    # 16 Seeds in diesem Tick geprueft, 2 angenommen.
    # BEWUSST ABGELEHNT (2026-08-06 Tick 2):
    # - "facharbeit schreiben lassen" (8 = groesstes Volumen des Ticks, mit
    #   "...kosten"/"...guenstig" = klarer Bezahlwille) und "praktikumsbericht
    #   schreiben lassen" (2, "...ki"): beides Arbeiten ZUR ABGABE. Der Fiverr-Gig
    #   schliesst akademische Abgaben ausdruecklich aus -> eine Landingpage, die das
    #   bewirbt, waere ein Versprechen, das wir nicht einloesen duerfen.
    # - "text uebersetzen lassen" (10) und "gedicht schreiben lassen" (7): grosses
    #   Volumen, aber Gratis-Intent. Bei uebersetzen dominieren google/kostenlos/
    #   foto/pdf (= Tool-Suche), bei gedicht sind 4 von 7 Vorschlaegen "kostenlos".
    # - "handbuch erstellen lassen" (2): Top-Modifier "qm handbuch" = ISO-9001-
    #   Zertifizierungsdokument, zum Festpreis 3,99-14,99 EUR nicht ehrlich lieferbar.
    # - "gpt erstellen lassen" (10): Vorschlaege sind bild/logo/video/grafik/portrait
    #   = Bild-/Videogenerierung, die wir nicht liefern (gleiche Linie wie portfolio).
    # - Gratis-Modifier dominiert (2-4 Treffer, je mit "kostenlos"): songtext (4,
    #   2x kostenlos), referat (3, 1x), essay (3, 1x).
    # - 0-1 Treffer (kein Signal): stellenanzeige, angebot schreiben, angebot
    #   erstellen (nur Haendler-Modifier amazon/bauhaus/hornbach), werbetexte,
    #   verkaufstexte, drehbuch, danksagung, einladungstext, amazon listing, etsy
    #   beschreibung, elevator pitch, konzept, checkliste, social media plan,
    #   uebersetzung erstellen, grusskarte, faq, onboarding, geschaeftsbrief,
    #   angebotstext, kleinanzeigen, ebay beschreibung, laudatio, abschiedsrede,
    #   taufrede, landingpage text, firmenprofil, unternehmensprofil (nur
    #   "google unternehmensprofil"), blogbeitrag, social media beitraege,
    #   geburtstagsrede, slogan, steckbrief, inhaltsangabe, ueber-mich-text,
    #   reklamation, geburtstagsgedicht, hochzeitseinladung, dating profil,
    #   tinder profil, immobilien expose, chatbot, excel formel, makro, vba,
    #   automatisierung, n8n, app text, datenanalyse.
    # Insgesamt 67 Seeds in diesem Tick geprueft, 2 angenommen.
    # 2026-08-07 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google
    # Autocomplete, hl=de/gl=de), Screening-Skripte scripts/_tick_seeds.py und
    # scripts/_tick_seeds2.py (46 Seeds, Rohausgabe im Report).
    # web_search erneut NICHT verfuegbar: Firecrawl HTTP 402 BILLING_ERROR
    # (insufficient_funds) -> Autocomplete bleibt die einzige MEASURED-Quelle.
    # "karteikarten erstellen lassen" -> 10 Vorschlaege (= Maximum beider Runden),
    # 3x KI-Modifier ("...ki", "ai karteikarten...", "...ki kostenlos") und die
    # Tool-Modifier anki/goodnotes/app (= es existiert ein etablierter, teils
    # bezahlter Werkzeugmarkt) sowie "...aus pdf" / "...zum lernen" (konkreter
    # Arbeitsauftrag mit mitgeliefertem Quellmaterial).
    # Ehrlich notiert: 2 der 10 Vorschlaege enthalten "kostenlos".
    # Abgrenzung zu bestehenden Seiten: study-guide/zusammenfassung = Fliesstext,
    # quiz-fragen = Multiple-Choice fuer Schulung/Event, lernplan = Zeitplan;
    # hier Frage-Antwort-PAARE als Import-Datei (CSV/TSV/Text) fuer Anki & Co.
    # Abgrenzung EHRLICH auf der Seite: Textdatei zum Selbst-Import, KEIN
    # Deck-Upload, KEIN App-Account, keine Uebernahme fremder Verlagsinhalte.
    ("karteikarten erstellen lassen ki", "Karteikarten erstellen lassen (KI)", "Frage-Antwort-Karten aus deinem Skript, PDF oder Thema – import-fertig fuer Anki, Quizlet & Co., ab 3,99 EUR in 24h."),
    # "text kuerzen lassen" -> 2 Vorschlaege, **0x "kostenlos"**, davon 1x
    # "text kuerzen lassen ki" (KI-Akzeptanz belegt). Signalniveau identisch mit
    # den bereits live stehenden pressemitteilung/vortrag/pitch-deck (je 2 Treffer).
    # Eigener Intent, keine Dublette: korrekturlesen = Fehler beheben,
    # text-formulieren = Ton/Stil verbessern (Laenge egal), zusammenfassung =
    # NEUER kurzer Text ueber die Quelle; hier bleibt es DEIN Text, nur auf eine
    # harte Wort-/Zeichen-/Seitenvorgabe eingedampft. Deliverable = reiner Text.
    ("text kürzen lassen", "Text kürzen lassen", "Zu lang? Dein Text auf die geforderte Wort-, Zeichen- oder Seitenzahl gekuerzt – Aussage und Ton bleiben erhalten, ab 3,99 EUR in 24h."),
    # BEWUSST ABGELEHNT (2026-08-07 Tick):
    # - "expose schreiben lassen" (6 Treffer, 0x kostenlos, mit "...preise"):
    #   waere eine DUBLETTE zur bereits live stehenden
    #   expose-schreiben-lassen-ki.html; zusaetzlich sind 2 der 6 Vorschlaege
    #   "expose bachelorarbeit/masterarbeit" = Pruefungsleistung zur Abgabe.
    # - "quiz erstellen lassen" (6, 1x kostenlos): deckungsgleich mit der
    #   bestehenden quiz-fragen-erstellen-lassen.html -> Kannibalisierung.
    # - "lernzettel erstellen lassen" (4, 1x kostenlos): inhaltlich vom
    #   study-guide + der neuen Karteikarten-Seite abgedeckt.
    # - "kurzgeschichte schreiben lassen" (2, 0x kostenlos, 1x "ki"): sauberes
    #   Signal, aber der wahrscheinlichste Verwendungszweck ist die Abgabe in
    #   Schule/Uni (Pruefungsleistung) und die Autocomplete-Modifier grenzen das
    #   nicht ab -> gleiche Linie wie referat/praktikumsbericht, zurueckgestellt.
    # - "urkunde erstellen lassen" (2): zweiter Vorschlag "...und drucken lassen"
    #   = Druck-/Layoutleistung, koennen wir nicht liefern.
    # - "einladung schreiben lassen" (2): erster Treffer ist der Tippfehler
    #   "einladung/schreiben lassen" -> kein belastbarer Intent.
    # - "fragebogen erstellen lassen" (2): zweiter Vorschlag ist
    #   "...und auswerten lassen" = Datenerhebung + Auswertung, nicht unser
    #   Text-Deliverable.
    # - 0-1 Treffer (kein Signal): umfrage, agenda, zeitplan, projektplan,
    #   wochenplan, raetsel, interviewleitfaden, firmennamen, persona,
    #   weihnachtskarte, glueckwunsch, youtube-/podcast-beschreibung,
    #   hausordnung, pflichtenheft, lastenheft, ablaufplan, grabrede,
    #   kalkulation, visitenkarte, moderationstext, traurede, maerchen,
    #   zwischenzeugnis, pruefungsfragen, klausur, eheversprechen, tischrede,
    #   spielanleitung, app-beschreibung, marketingplan, marketingkonzept,
    #   redaktionsplan, keyword-recherche, unterrichtsmaterial, hoerbuch-text,
    #   seo texte.
    # 46 Seeds in diesem Tick geprueft, 2 angenommen.
    # 2026-08-08 Tick: Nachfrage MEASURED via scripts/kw_demand.py (Google Autocomplete,
    # hl=de/gl=de). web_search/Firecrawl erneut HTTP 402 (insufficient_funds, Rohtext im
    # Report) -> Autocomplete bleibt die einzige MEASURED-Quelle; kein ASSUMED-Keyword.
    # "kinderbuch schreiben lassen" -> 3 Vorschlaege, KEIN "kostenlos"-Modifier:
    # "chatgpt kinderbuch schreiben lassen" (KI-Akzeptanz woertlich) und "kinderbuch
    # schreiben und drucken lassen" (= es existiert ein bezahlter Markt inkl. Druck).
    # Signalniveau wie "bericht"/"speisekarte" (je 3 Treffer, beide live).
    # Deliverable EHRLICH abgegrenzt: Geschichte + Text, KEINE Illustrationen und
    # KEIN Druck/Bindung (genau der eine Modifier, den wir nicht bedienen koennen).
    ("kinderbuch schreiben lassen", "Kinderbuch schreiben lassen – Text & Geschichte", "Altersgerechte Geschichte mit Figuren, Handlungsbogen und Seitenaufteilung als fertiger Text – ab 3,99 EUR, in 24h. Ohne Illustration und Druck."),
    # "fallstudie schreiben lassen" -> 2 Vorschlaege, KEIN "kostenlos"-Modifier,
    # darunter woertlich "fallstudie schreiben lassen ki" (KI-Akzeptanz explizit).
    # Gleiches Signalniveau wie "pressemitteilung"/"vortrag"/"pitch deck" (je 2, alle live).
    # B2B: Kundenreferenz/Case Study fuer Website und Vertrieb. Deliverable = reiner Text.
    # Abgrenzung EHRLICH: Marketing-Fallstudie aus DEINEN Zahlen, KEINE Pruefungs-
    # leistung zur Abgabe (gleiche Linie wie hausarbeit/referat/praktikumsbericht).
    ("fallstudie schreiben lassen", "Fallstudie schreiben lassen (Case Study)", "Kundenreferenz nach Schema Ausgangslage – Loesung – Ergebnis, mit Zitat und Zahlen – ab 3,99 EUR, in 24h geliefert."),
    # BEWUSST ABGELEHNT (2026-08-08 Tick):
    # - "praesentation erstellen lassen" (10 Treffer = groesstes Volumen des Ticks):
    #   deckt inhaltlich die bestehende Seite powerpoint-erstellen-lassen-ki ab
    #   (Vorschlag woertlich "powerpoint praesentation erstellen lassen ki") und
    #   enthaelt 2x "kostenlos" -> gleiche Begruendung wie das frueher abgelehnte
    #   "handout erstellen lassen". Kein Duplikat bauen.
    # - "logo erstellen lassen" (10, davon "...kosten", "...guenstig", "...freelancer"):
    #   starkes Kaufsignal, aber das Deliverable ist eine GRAFIK. Ein "Logo-Text" waere
    #   Over-Promise gegenueber dem Suchintent -> Regel: nur liefern, was wir koennen.
    # - "untertitel erstellen lassen" (7): Modifier premiere pro/davinci/youtube =
    #   der Sucher will es SELBST im eigenen Tool machen, plus "kostenlos".
    # - "gedicht schreiben lassen" (7): 3 der 7 Vorschlaege sind "kostenlos" ->
    #   kein Bezahlwille (schon in einem frueheren Tick aus dem gleichen Grund raus).
    # - "angebot erstellen lassen" (4): Modifier amazon/bauhaus/hornbach = Preisangebot
    #   vom Haendler, kein geschriebenes Dokument (Wiederholungsbefund, bleibt abgelehnt).
    # - "kinderbuch"-Nachbar "drehbuch schreiben lassen" (1) = kein Signal.
    # - 0-1 Treffer (kein Signal): stellenanzeige schreiben lassen, elevator pitch
    #   schreiben, geschaeftsbrief schreiben lassen, produkttexte schreiben lassen,
    #   social media beitraege erstellen lassen, video skript schreiben lassen,
    #   leitbild erstellen lassen.
    # - "erklaervideo skript" (2): zweiter Vorschlag ist "...vorlage" = Gratis-Vorlagen-
    #   Sucher, schwaecherer Bezahlwille als die zwei angenommenen -> zurueckgestellt.
    # 14 Seeds in diesem Tick geprueft, 2 angenommen.
]

def slug(kw):
    return kw.replace(" ", "-").replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")

def page(kw, title, desc):
    s = slug(kw)
    p = os.path.join(BLOG, f"{s}.html")
    if os.path.exists(p):
        return False, p
    html = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – KI in 24h</title>
<meta name="description" content="{desc}">
<style>
 body{{font-family:system-ui,sans-serif;max-width:680px;margin:40px auto;padding:0 16px;line-height:1.6;color:#1a1a1a}}
 h1{{font-size:2rem}} .cta{{background:#111;color:#fff;padding:14px 22px;border-radius:6px;text-decoration:none;display:inline-block;margin-top:1em}}
 .note{{color:#666;font-size:.85rem;margin-top:2em;border-top:1px solid #eee;padding-top:1em}}
</style>
</head>
<body>
<h1>{title}</h1>
<p>{desc}</p>
<p>Du beschreibst deinen Wunsch, wählst eine Preisstufe (ab 3,99 EUR) und erhältst
das fertige Deliverable nach Zahlung – erstellt von einer KI, geprüft, lieferbar in 24h.</p>
<a class="cta" href="{GIG}">Jetzt Auftrag geben &rarr;</a>
<p style="margin-top:1.5em">Weitere Beispiele: Bewerbungen, Notion-Templates, Python-Skripte,
Study-Guides, Social-Media-Posts – alles als Festpreis-Deliverable.</p>
<p id="rtd-crosslink" style="margin-top:2em;padding-top:1em;border-top:1px solid #eee;font-size:.9rem">Nicht gefunden, was du suchst? <a href="/new-business/rtd.html">Individuelles Deliverable anfragen (Study-Guide, Template, Text) &rarr;</a></p>
<div class="note"><a href="/new-business/impressum.html">Impressum</a> &middot; <a href="/new-business/agb.html">AGB</a> &middot; <a href="/new-business/datenschutz.html">Datenschutz</a></div>
</body>
</html>"""
    os.makedirs(BLOG, exist_ok=True)
    open(p, "w", encoding="utf-8").write(html)
    return True, p

if __name__ == "__main__":
    if len(sys.argv) > 1:
        kw = sys.argv[1]
        title = f"KI: {kw.title()}"
        created, path = page(kw, title, f"Aufgabe erledigt: {kw}.")
    else:
        # naechstes ungeschriebenes Keyword
        done = {slug(kw) for kw,_,_ in KEYWORDS
                if os.path.exists(os.path.join(BLOG, f"{slug(kw)}.html"))}
        nxt = next((k for k,_,_ in KEYWORDS if slug(k) not in done), None)
        if not nxt:
            print("ALLE KEYWORDS BELEGT — neue recherchieren.")
            sys.exit(0)
        title = f"KI: {nxt.title()}"
        by_kw = {k: (t, d) for k, t, d in KEYWORDS}
        # kuratierten Titel nutzen (vorher wurde er ignoriert -> "KI: Powerpoint Erstellen Lassen Ki")
        title, desc = by_kw[nxt]
        created, path = page(nxt, title, desc)
    print(f"{'NEU' if created else 'EXISTIERT'}: {path}")
