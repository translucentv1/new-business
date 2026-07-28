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
    ("bewerbung schreiben lassen ki", "KI-Bewerbung in 24h", "Eine uberzeugende Bewerbung, von KI geschrieben und in 24h geliefert."),
    ("notion template erstellen lassen", "Notion-Template auf Auftrag", "Individuelles Notion-Template, das genau deinen Workflow abbildet."),
    ("text schreiben lassen guenstig", "Texte zum Festpreis", "Blog, Produkttext oder E-Mail — fertig ab 3,99 EUR."),
    ("python skript erstellen lassen", "Python-Skript auf Auftrag", "Automatisierung, CSV/JSON, API — kleines Script, feste Preis."),
    ("study guide erstellen lassen", "Study-Guide als Deliverable", "Zusammenfassung, Charaktere, Verstaendnisfragen zu jedem Buch."),
    ("instagram caption ki", "Social-Media-Posts von KI", "Instagram/TikTok-Captions, die Klicks bringen."),
    ("hausarbeit schreiben lassen ki", "KI-Hausarbeit-Entwurf", "Struktur, Quellen, Gliederung – KI-Entwurf als Lernhilfe."),
    ("ebook cover erstellen lassen", "Ebook-Cover von KI", "Professionelles Cover fuer Self-Publishing, in 24h."),
    ("linkedin post schreiben lassen", "KI-LinkedIn-Posts", "Posts, die Reichweite bringen – fuer Recruiter sichtbar."),
    ("expose schreiben lassen ki", "KI-Expose Immobilien", "Verkaufsfertiges Expose fuer Vermieter und Makler."),
    ("quiz fragen erstellen lassen", "KI-Quiz-Fragen", "Für Schulung, Event oder Lead-Gen – fertige Fragen."),
    # 2026-07-28 Tick: Nachfrage ASSUMED (web_search blockiert, Firecrawl 402) — Intents analog zu bewerbung/text
    ("lebenslauf erstellen lassen ki", "KI-Lebenslauf in 24h", "Moderner, ATS-tauglicher Lebenslauf – von KI erstellt, geprueft, in 24h geliefert."),
    ("produktbeschreibung schreiben lassen", "Produkttexte fuer deinen Shop", "Verkaufsstarke Produktbeschreibungen fuer Shopify, Etsy oder Amazon – Festpreis ab 3,99 EUR."),
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
        created, path = page(nxt, title, dict((k,d) for k,_,d in KEYWORDS)[nxt])
    print(f"{'NEU' if created else 'EXISTIERT'}: {path}")
