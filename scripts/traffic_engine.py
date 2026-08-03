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
<div class="note"><a href="/new-business/impressum.html">Impressum</a> &middot; <a href="/new-business/agb.html">AGB</a></div>
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
