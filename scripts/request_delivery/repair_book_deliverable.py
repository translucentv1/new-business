#!/usr/bin/env python3
"""Repariert fehlende Buch-Deliverables (dl/<hash>/<slug>.html).

Hintergrund: Einige LIVE-Stripe-Payment-Links leiten nach der Zahlung auf
dl/<hash>/<slug>.html um. Fehlt diese Datei, bekommt ein zahlender Kunde einen
404 -> Geld ohne Leistung. Dieses Skript baut die Seite aus BEREITS VORHANDENEN
Quellen im Repo neu auf -- es erfindet keine Inhalte:

  Zusammenfassung    <- seo/<slug>/lesen/index.html   (Fliesstext)
  Figurenliste       <- seo/<slug>/figuren/index.html (Listenpunkte)
  Diskussionsfragen  <- seo/<slug>/analyse/index.html (Listenpunkte)
  30-Tage-Leseplan   <- seo/<slug>/leseplan/index.html(Listenpunkte)
  Kapiteluebersicht  <- seo/<slug>/kapitel/index.html (Listenpunkte)
  Volltext           <- dl/<hash>/<slug>.epub         (OEBPS/*.xhtml)

Abschnitte ohne Quelle werden WEGGELASSEN (nie erfunden).

Nutzung:
  python repair_book_deliverable.py --check
  python repair_book_deliverable.py --slug tales-of-folk-and-fairies --hash 0c4edba1e68ecd3e
"""
import argparse
import html as html_mod
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

STYLE = """    body{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.7;color:#1a1a1a}
    h1{font-size:1.9em} h2{font-size:1.4em;margin-top:1.6em} h3{font-size:1.15em}
    .byline{color:#666;font-style:italic;margin-top:-.4em}
    .note{margin:1.4em 0;padding:1em;background:#f4f7ff;border-left:4px solid #2962ff;border-radius:6px;font-size:.9em}
    .epub-dl{margin:1.2em 0}
    .epub-dl a{display:inline-block;background:#2962ff;color:#fff;padding:.6em 1.1em;border-radius:6px;text-decoration:none;font-weight:bold}
    .epub-dl a:hover{background:#1c44b2}
    hr{border:none;border-top:1px solid #eee;margin:2em 0}
    li{margin:.3em 0}"""


def strip_tags(s):
    s = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html_mod.unescape(s)).strip()


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def seo_path(slug, page):
    return os.path.join(ROOT, "seo", slug, page, "index.html")


def list_items(slug, page, drop_nav=True):
    """Listenpunkte einer SEO-Seite; Navigations-/Footer-Links werden verworfen."""
    p = seo_path(slug, page)
    if not os.path.exists(p):
        return []
    body = read(p)
    m = re.search(r"(?s)<article\b.*?</article>", body)
    if m:
        body = m.group(0)
    out = []
    for li in re.findall(r"(?s)<li\b[^>]*>(.*?)</li>", body):
        txt = strip_tags(li)
        if not txt:
            continue
        if drop_nav and ("<a " in li.lower() and len(txt) < 60):
            continue          # reine Navigationslinks
        out.append(txt)
    return out


def summary_text(slug):
    """Beschreibende Absaetze der 'lesen'-Seite (ohne CTA-Boxen/Nav)."""
    p = seo_path(slug, "lesen")
    if not os.path.exists(p):
        return []
    body = read(p)
    m = re.search(r"(?s)<article\b.*?</article>", body)
    if m:
        body = m.group(0)
    body = re.sub(r'(?s)<div class="box".*?</div>', " ", body)
    paras = []
    for pr in re.findall(r"(?s)<p\b[^>]*>(.*?)</p>", body):
        if 'class="byline"' in pr or "href=" in pr:
            continue
        txt = strip_tags(pr)
        if len(txt) > 120:
            paras.append(txt)
    return paras


def meta(slug):
    """Titel + Autor aus einer beliebigen SEO-Seite."""
    for page in ("lesen", "kaufen", "begleiter", "figuren"):
        p = seo_path(slug, page)
        if not os.path.exists(p):
            continue
        body = read(p)
        t = re.search(r"(?s)<h1[^>]*>(.*?)</h1>", body)
        a = re.search(r'(?s)<p class="byline"[^>]*>(.*?)</p>', body)
        if t:
            author = strip_tags(a.group(1)) if a else ""
            return strip_tags(t.group(1)), re.sub(r"^von\s+", "", author)
    return slug.replace("-", " ").title(), ""


def epub_guide(epub_path):
    """Lese-Begleiter-Abschnitte aus OEBPS/guide.xhtml (bereits im EPUB enthalten)."""
    if not os.path.exists(epub_path):
        return ""
    z = zipfile.ZipFile(epub_path)
    name = next((n for n in z.namelist() if n.endswith("guide.xhtml")), None)
    if not name:
        return ""
    raw = z.read(name).decode("utf-8", "replace")
    m = re.search(r"(?s)<body\b[^>]*>(.*?)</body>", raw)
    inner = m.group(1) if m else raw
    inner = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", inner)
    return inner.strip()


def epub_fulltext(epub_path):
    """Volltext aus dem EPUB: Kapitel in Spine-Reihenfolge, Tags bereinigt.

    guide.xhtml und nav werden ausgelassen -- der Begleiter steht schon oben.
    """
    if not os.path.exists(epub_path):
        return ""
    z = zipfile.ZipFile(epub_path)
    names = z.namelist()
    opf = next((n for n in names if n.endswith(".opf")), None)
    order = []
    if opf:
        opf_txt = z.read(opf).decode("utf-8", "replace")
        base = os.path.dirname(opf)
        ids = dict(re.findall(r'<item\b[^>]*id="([^"]+)"[^>]*href="([^"]+)"', opf_txt))
        ids.update({i: h for h, i in re.findall(
            r'<item\b[^>]*href="([^"]+)"[^>]*id="([^"]+)"', opf_txt)})
        for idref in re.findall(r'<itemref\b[^>]*idref="([^"]+)"', opf_txt):
            href = ids.get(idref)
            if not href:
                continue
            full = (base + "/" + href) if base else href
            if full in names:
                order.append(full)
    if not order:
        order = sorted(n for n in names if n.endswith((".xhtml", ".html")))
    order = [n for n in order
             if not n.endswith(("guide.xhtml", "nav.xhtml", "toc.xhtml"))]
    chunks = []
    for n in order:
        raw = z.read(n).decode("utf-8", "replace")
        m = re.search(r"(?s)<body\b[^>]*>(.*?)</body>", raw)
        inner = m.group(1) if m else raw
        inner = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", inner)
        title = re.search(r"(?s)<title\b[^>]*>(.*?)</title>", raw)
        t = strip_tags(title.group(1)) if title else ""
        if t and t.lower() not in ("einleitung", "introduction"):
            chunks.append(f"<h2>{html_mod.escape(t)}</h2>")
        for tag, content in re.findall(r"(?s)<(h[1-6]|p)\b[^>]*>(.*?)</\1>", inner):
            txt = strip_tags(content)
            if txt and txt != "---":
                chunks.append(f"<{tag}>{html_mod.escape(txt)}</{tag}>")
    return "\n".join(chunks)


def build(slug, dl_hash, write=True):
    dl_dir = os.path.join(ROOT, "dl", dl_hash)
    epub_rel = f"{slug}.epub"
    epub_abs = os.path.join(dl_dir, epub_rel)
    title, author = meta(slug)

    sec = []
    guide = epub_guide(epub_abs)
    src = {}
    if guide:
        # Der Begleiter steckt bereits fertig im EPUB -> 1:1 uebernehmen.
        sec.append(guide)
        src["quelle_begleiter"] = "epub:guide.xhtml"
        src["begleiter_abschnitte"] = re.findall(r"<h2>(.*?)</h2>", guide)
    else:
        # Fallback: aus den SEO-Seiten zusammensetzen (nur vorhandene Abschnitte).
        src["quelle_begleiter"] = "seo-seiten"
        summary = summary_text(slug)
        figuren = list_items(slug, "figuren")
        fragen = list_items(slug, "analyse")
        plan = list_items(slug, "leseplan")
        kapitel = list_items(slug, "kapitel")
        if summary:
            sec.append("<h2>Zusammenfassung</h2>\n" +
                       "\n".join(f"<p>{html_mod.escape(s)}</p>" for s in summary))
        if figuren:
            sec.append("<h2>Figurenliste</h2>\n<ul>" + "\n".join(
                f"<li>{html_mod.escape(x)}</li>" for x in figuren) + "</ul>")
        if fragen:
            sec.append("<h2>Diskussionsfragen</h2>\n<ol>" + "\n".join(
                f"<li>{html_mod.escape(x)}</li>" for x in fragen) + "</ol>")
        if plan:
            sec.append("<h2>30-Tage-Leseplan</h2>\n<ol>" + "\n".join(
                f"<li>{html_mod.escape(x)}</li>" for x in plan) + "</ol>")
        if kapitel:
            sec.append("<h2>Kapiteluebersicht</h2>\n<ol>" + "\n".join(
                f"<li>{html_mod.escape(x)}</li>" for x in kapitel) + "</ol>")
        src.update({"zusammenfassung": len(summary), "figuren": len(figuren),
                    "fragen": len(fragen), "leseplan": len(plan),
                    "kapitel": len(kapitel)})

    volltext = epub_fulltext(epub_abs)
    if volltext:
        sec.append('<h2>Volltext (Public Domain)</h2>\n'
                   '<p class="note">Der vollständige, bereinigte Originaltext '
                   '– gemeinfrei.</p>\n' + volltext)
    src["volltext_bytes"] = len(volltext)

    if not sec:
        raise SystemExit(f"FEHLER: keine Quellen fuer {slug} gefunden -> nichts gebaut")

    epub_line = (f'<p class="epub-dl"><a href="{epub_rel}">'
                 f'⬇ EPUB-Version herunterladen (Kindle / Apple Books / Tolino)</a></p>'
                 if os.path.exists(epub_abs) else "")

    doc = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{html_mod.escape(title)} – Lese-Begleiter von {html_mod.escape(author)}</title>
  <style>
{STYLE}
  </style>
</head>
<body>
  <article>
    <h1>Lese-Begleiter: {html_mod.escape(title)}</h1>
    <p class="byline">von {html_mod.escape(author)}</p>
    <div class="note">Dein gekaufter Lese-Begleiter (Analyse + gemeinfreier
       Originaltext). Offline lesbar, nur hier verfügbar – als HTML und EPUB.</div>
    {epub_line}
    <hr>
{chr(10).join(sec)}
  </article>
</body>
</html>
"""
    out = os.path.join(dl_dir, f"{slug}.html")
    if write:
        os.makedirs(dl_dir, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(doc)
    return out, len(doc), src


def check():
    """Listet alle dl/<hash>/ mit EPUB aber ohne passende HTML."""
    base = os.path.join(ROOT, "dl")
    missing = []
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d)
        if not os.path.isdir(p):
            continue
        files = os.listdir(p)
        for f in files:
            if f.endswith(".epub") and f[:-5] + ".html" not in files:
                missing.append((f[:-5], d))
    print(f"dl-Ordner mit EPUB ohne HTML: {len(missing)}")
    for slug, h in missing:
        print(f"  {h}  {slug}")
    return missing


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--hash", dest="dl_hash")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        check()
        sys.exit(0)
    if not (a.slug and a.dl_hash):
        ap.error("--slug und --hash noetig (oder --check)")
    out, size, stats = build(a.slug, a.dl_hash)
    print(f"GEBAUT: {out} ({size} bytes)")
    print("Quellen:", stats)
