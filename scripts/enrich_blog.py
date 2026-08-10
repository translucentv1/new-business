#!/usr/bin/env python3
"""enrich_blog.py — macht die duennen Geldseiten unter blog/ inhaltlich eigenstaendig.

HINTERGRUND (MEASURED 2026-08-10, evidence/_t30_thin_content.py):
  blog/: 51 Seiten, Median 116 Woerter gesamt / 79 seitenspezifisch.
  0 % exakte Duplikate, aber durchgehend Thin Content. Tag 7 in Folge
  0 Index-Treffer (DDG/Bing-Proxy) bei zaehlfaehiger Kontrolle.

WAS ES TUT
  Erzeugt pro Seite einen seitenspezifischen Block (Nutzen, Ablauf-Beispiel,
  3 FAQ, ehrliche Abgrenzung) mit dem LOKALEN Ollama-Modell -> 0 EUR Kosten,
  kein API-Key. Der Block wird zwischen Marker eingesetzt und ist idempotent:
  ein zweiter Lauf laesst bereits anger. Seiten unveraendert (ausser --force).

QUALITAETSSCHRANKE (harte Ablehnung, kein Text landet ungeprueft auf der Seite)
  - Modell liefert JSON; alles wird serverseitig zu HTML gerendert + escaped.
  - Verbotene Claims: kostenlos/gratis/garantiert/Erfolgsgarantie/Rechtsberatung.
  - Preise: nur 3,99 / 7,99 / 14,99 EUR duerfen vorkommen.
  - Mindest-/Hoechstlaenge, Deutsch-Heuristik, keine Markdown-Zaeune, kein HTML.

Nutzung:
  python scripts/enrich_blog.py --check          # nur zaehlen, nichts schreiben
  python scripts/enrich_blog.py --limit 3        # 3 Seiten anreichern
  python scripts/enrich_blog.py                  # alle offenen Seiten
"""
from __future__ import annotations

import argparse
import html as htmllib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(ROOT, "blog")
OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("ENRICH_MODEL", "qwen2.5:7b")

START = "<!-- ENRICH:v1 START -->"
END = "<!-- ENRICH:v1 END -->"
# Einfuegepunkt. scripts/interlink.py verlangt, dass der Cluster-Absatz
# <p id="related"> UNMITTELBAR vor <p id="rtd-crosslink"> steht — der
# Anreicherungsblock muss also DAVOR landen, sonst meldet verify.py die Seite
# als "nicht im Cluster verlinkt" (MEASURED 2026-08-10, VERIFY_DEFEKT).
ANCHORS = ('<p id="related"', '<p id="rtd-crosslink"')
ANCHOR = ANCHORS[1]


def anchor_of(html: str):
    for a in ANCHORS:
        if a in html:
            return a
    return None

# Immer verboten — wir verschenken nichts und versprechen keine Ergebnisse.
FORBIDDEN = [
    "kostenlos", "gratis", "umsonst", "100%", "bestnote",
    "geld-zurueck", "geld zurück", "erfolgsgarantie",
]
# Nur verboten, wenn NICHT verneint. "Das ersetzt keine Rechtsberatung" ist ein
# erwuenschter Disclaimer; "wir bieten Rechtsberatung" ist es nicht.
NEEDS_NEGATION = [
    "rechtsberatung", "rechtsverbindlich", "steuerberat", "anwalt",
    "garantie", "garantiert", "garantieren",
]
NEGATIONS = ("kein", "nicht", "ohne", "ersetzt", "keinerlei", "statt", "nein")

# Widersprueche zum eigenen Angebot. Ein 3b-Lauf schrieb "Die Mahnung wird exakt
# wie in der AI-Vorlage erstellt und kann nicht angepasst werden" — legal, aber
# sachlich falsch, weil 7,99/14,99 EUR ausdruecklich Korrekturschleifen enthalten.
CONTRADICTIONS = [
    r"kann(st)?\s+(sie|es|ihn|der|die|das)?\s*nicht\s+(mehr\s+)?(angepasst|geaendert|ge\u00e4ndert|bearbeitet|korrigiert)",
    r"nicht\s+(anpassbar|aenderbar|\u00e4nderbar|korrigierbar)",
    r"keine\s+(aenderungen|\u00e4nderungen|korrekturen|korrekturschleife)",
    r"ohne\s+korrekturschleife",
]


def _sentences(text: str):
    return [s for s in re.split(r"(?<=[.!?;:])\s+|\n", text) if s.strip()]
ALLOWED_PRICES = {"3,99", "7,99", "14,99", "24"}
PRICE_RE = re.compile(r"\b\d{1,3}(?:[.,]\d{2})?\s*(?:EUR|€|Euro)", re.I)

PROMPT = """Du schreibst Website-Text fuer einen deutschen Mikro-Dienstleister.
Angebot: Ein Mensch beauftragt einen Text/Datei-Auftrag, eine KI erstellt den
Entwurf, ein Mensch prueft ihn, Lieferung innerhalb von 24 Stunden.
Preisstufen: 3,99 EUR (klein), 7,99 EUR (mittel), 14,99 EUR (gross).

Thema dieser Seite: "{kw}"
Ueberschrift der Seite: "{title}"

WICHTIGSTE REGEL: Sprich den Leser durchgehend mit "du" an (du, dir, dein,
deine). Benutze NIEMALS die Hoeflichkeitsform "Sie", "Ihnen" oder "Ihre" —
der Rest der Seite duzt, ein Wechsel wirkt wie ein Fremdtext.

Schreibe AUSSCHLIESSLICH gueltiges JSON (kein Markdown, keine Codezaeune) mit
genau diesen Schluesseln:
{{
  "intro": "2-3 Saetze: fuer wen diese Seite ist und welches konkrete Problem geloest wird. Konkret zum Thema, keine Floskeln.",
  "lieferung": ["3 bis 5 Stichpunkte: was der Kunde konkret als Datei/Text bekommt", "..."],
  "brauchen": ["2 bis 4 Stichpunkte: welche Angaben der Kunde liefern muss", "..."],
  "faq": [
    {{"f": "Konkrete Frage zum Thema", "a": "Ehrliche Antwort, 1-3 Saetze"}},
    {{"f": "...", "a": "..."}},
    {{"f": "...", "a": "..."}}
  ],
  "abgrenzung": "1-2 Saetze: was ausdruecklich NICHT enthalten ist."
}}

Regeln:
- Deutsch, sachlich, ohne Werbefloskeln, ohne Ausrufezeichen.
- Natuerliches, fehlerfreies Deutsch. Keine Wortneuschoepfungen.
- Du-Form, siehe wichtigste Regel oben. Kein "Sie", kein "Ihnen", kein "Ihre".
- Verspreche NICHTS Unhaltbares: keine Erfolgs-, Noten- oder Zusagegarantie.
- Keine Rechts-, Steuer- oder Medizinberatung anbieten.
- Die Woerter "kostenlos", "gratis", "garantiert" duerfen nicht vorkommen.
- Nenne Preise nur als 3,99 / 7,99 / 14,99 EUR oder gar nicht.
- Ab 7,99 EUR ist eine Korrekturschleife enthalten. Behaupte NIEMALS, der Text
  koenne nicht angepasst oder geaendert werden.
- Erwaehne nicht, dass eine KI den Text schreibt; das steht bereits auf der Seite.
- Gesamtlaenge aller Texte zusammen: 180 bis 350 Woerter.
"""


# ---------------------------------------------------------------- Ollama
def ollama(prompt: str, timeout: int = 300) -> str:
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.4, "num_predict": 900},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())["response"]


# ---------------------------------------------------------------- Pruefung
def _flat(d: dict) -> list:
    parts = [str(d.get("intro", "")), str(d.get("abgrenzung", ""))]
    parts += [str(x) for x in d.get("lieferung", []) or []]
    parts += [str(x) for x in d.get("brauchen", []) or []]
    for q in d.get("faq", []) or []:
        if isinstance(q, dict):
            parts += [str(q.get("f", "")), str(q.get("a", ""))]
    return parts


def wordcount(d: dict) -> int:
    return len(" ".join(_flat(d)).split())


def _units(d: dict) -> list:
    """Pruefeinheiten fuer die Verneinungsregel.

    Eine FAQ-Frage ist KEIN Claim ("Ist das eine Rechtsberatung?") — sie wird
    deshalb zusammen mit ihrer Antwort als EINE Einheit geprueft, damit das
    "Nein, ..." der Antwort zaehlt. Fliesstext wird satzweise geprueft, damit
    eine Verneinung an anderer Stelle nichts freikauft.
    """
    units = []
    for key in ("intro", "abgrenzung"):
        units += _sentences(str(d.get(key, "")))
    units += [str(x) for x in d.get("lieferung", []) or []]
    units += [str(x) for x in d.get("brauchen", []) or []]
    for q in d.get("faq", []) or []:
        if isinstance(q, dict):
            units.append(f"{q.get('f','')} {q.get('a','')}")
    return units


def validate(d) -> tuple[bool, str]:
    if not isinstance(d, dict):
        return False, "kein JSON-Objekt"
    for k in ("intro", "lieferung", "brauchen", "faq", "abgrenzung"):
        if k not in d:
            return False, f"Schluessel fehlt: {k}"
    if not isinstance(d["faq"], list) or len(d["faq"]) < 2:
        return False, "faq < 2 Eintraege"
    if not (2 <= len(d["lieferung"]) <= 6):
        return False, f"lieferung {len(d['lieferung'])} Punkte"
    blob = json.dumps(d, ensure_ascii=False).lower()
    for bad in FORBIDDEN:
        if bad in blob:
            return False, f"verbotener Claim: {bad!r}"
    for u in _units(d):
        s = u.lower()
        for w in NEEDS_NEGATION:
            if w in s and not any(n in s for n in NEGATIONS):
                return False, f"Claim ohne Verneinung: {w!r} in {s.strip()[:60]!r}"
    plain = " ".join(_flat(d)).lower()
    for pat in CONTRADICTIONS:
        m = re.search(pat, plain)
        if m:
            return False, f"Widerspruch zum Angebot: {m.group(0)!r}"
    # Anrede-Bruch: der Rest der Seite duzt. Mehr als zwei Siez-Marker = Fremdtext.
    formal = len(re.findall(r"\b(Sie|Ihnen|Ihre[rnms]?|Ihr)\b", " ".join(_flat(d))))
    if formal > 2:
        return False, f"Anrede-Bruch: {formal}x Siez-Form statt Du-Form"
    if "<" in blob or "```" in blob:
        return False, "HTML/Markdown im Text"
    for m in PRICE_RE.findall(json.dumps(d, ensure_ascii=False)):
        num = re.search(r"\d{1,3}(?:[.,]\d{2})?", m).group()
        if num not in ALLOWED_PRICES:
            return False, f"fremder Preis: {m!r}"
    n = wordcount(d)
    if not (140 <= n <= 480):
        return False, f"Laenge {n} Woerter ausserhalb 140-480"
    # Deutsch-Heuristik
    if not re.search(r"\b(und|der|die|das|dein|dir|wird|nicht)\b", blob):
        return False, "wirkt nicht deutsch"
    return True, f"ok ({n} Woerter)"


# ---------------------------------------------------------------- Rendern
def e(s: str) -> str:
    return htmllib.escape(str(s).strip())


def render(d: dict) -> str:
    li = "\n".join(f"    <li>{e(x)}</li>" for x in d["lieferung"])
    br = "\n".join(f"    <li>{e(x)}</li>" for x in d["brauchen"])
    faq = "\n".join(
        f"    <h3>{e(q.get('f',''))}</h3>\n    <p>{e(q.get('a',''))}</p>"
        for q in d["faq"])
    return f"""{START}
  <p>{e(d['intro'])}</p>
  <h2>Was du bekommst</h2>
  <ul>
{li}
  </ul>
  <h2>Was ich von dir brauche</h2>
  <ul>
{br}
  </ul>
  <h2>Preisstufen</h2>
  <ul>
    <li><strong>3,99 EUR</strong> — kleiner Umfang, ein Entwurf.</li>
    <li><strong>7,99 EUR</strong> — mittlerer Umfang, eine Korrekturschleife.</li>
    <li><strong>14,99 EUR</strong> — grosser Umfang, zwei Korrekturschleifen.</li>
  </ul>
  <h2>Haeufige Fragen</h2>
{faq}
  <h2>Was nicht enthalten ist</h2>
  <p>{e(d['abgrenzung'])}</p>
{END}"""


# ---------------------------------------------------------------- Seiten
def pages():
    return sorted(f for f in os.listdir(BLOG) if f.endswith(".html"))


def page_meta(html: str, fname: str):
    m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else fname
    kw = fname[:-5].replace("-", " ")
    return kw, title


def enrich_one(fname: str, force=False, retries=2):
    path = os.path.join(BLOG, fname)
    html = open(path, encoding="utf-8").read()
    if START in html and not force:
        return "skip", "bereits angereichert"
    anchor = anchor_of(html)
    if anchor is None:
        return "fail", "Ankerpunkt related/rtd-crosslink fehlt"
    kw, title = page_meta(html, fname)
    last = "?"
    for attempt in range(retries + 1):
        try:
            raw = ollama(PROMPT.format(kw=kw, title=title))
        except (urllib.error.URLError, TimeoutError, OSError) as ex:
            last = f"Ollama nicht erreichbar: {ex}"
            time.sleep(2)
            continue
        try:
            d = json.loads(raw)
        except json.JSONDecodeError as ex:
            last = f"JSON kaputt: {ex}"
            continue
        ok, why = validate(d)
        if not ok:
            last = why
            continue
        block = render(d)
        if force and START in html:
            new = re.sub(re.escape(START) + r".*?" + re.escape(END), block,
                         html, flags=re.S)
        else:
            new = html.replace(anchor, block + "\n" + anchor, 1)
        if new == html:
            return "fail", "Einsetzen wirkungslos"
        open(path, "w", encoding="utf-8").write(new)
        return "ok", why
    return "fail", last


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="nur zaehlen")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="Block neu erzeugen")
    ap.add_argument("--only", default="", help="Teilstring des Dateinamens")
    ap.add_argument("--thinnest", action="store_true",
                    help="duennste Seiten zuerst (wenigste Woerter)")
    a = ap.parse_args(argv)

    fs = [f for f in pages() if a.only in f]
    open_ = [f for f in fs
             if START not in open(os.path.join(BLOG, f), encoding="utf-8").read()]
    print(f"blog/: {len(fs)} Seiten, angereichert {len(fs)-len(open_)}, offen {len(open_)}")
    if a.check:
        print("ERGEBNIS: " + ("ENRICH_OK" if not open_ else "ENRICH_OFFEN"))
        return 0 if not open_ else 1

    todo = fs if a.force else open_
    if a.thinnest:
        def words(f):
            t = open(os.path.join(BLOG, f), encoding="utf-8").read()
            t = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", t)
            return len(re.sub(r"<[^>]+>", " ", t).split())
        todo = sorted(todo, key=words)
    if a.limit:
        todo = todo[:a.limit]
    print(f"Modell: {MODEL}  zu bearbeiten: {len(todo)}")
    ok = fail = skip = 0
    for i, f in enumerate(todo, 1):
        t0 = time.time()
        st, why = enrich_one(f, force=a.force)
        dt = time.time() - t0
        print(f"[{i}/{len(todo)}] {st.upper():4s} {f} — {why} ({dt:.0f}s)", flush=True)
        ok += st == "ok"
        fail += st == "fail"
        skip += st == "skip"
    print(f"\nFERTIG: ok={ok} fail={fail} skip={skip}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
