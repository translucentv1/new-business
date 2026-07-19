"""EPUB-Deliverable-Generator (Tier-2, ADR-0013).

Erzeugt pro Buch ein valides EPUB3 (stdlib ``zipfile``, keine externen
Dependencies) unter demselben privaten Download-Gate-Pfad wie das HTML-
Deliverable:

    docs/dl/<hash>/<slug>.epub

wobei ``hash``/``slug`` identisch zum HTML-Deliverable (deliverable_gen)
berechnet werden, damit beide Dateien im selben gehashten Ordner liegen
und der Kaeufer sie nach dem Kauf aus derselben (nicht verlinkten) URL
herunterladen kann.

Inhalt des EPUB:
  - Lese-Begleiter (aus study_guide.json, wenn gefuellt) als erstes Kapitel
  - ggf. Einleitung (Preamble vor dem ersten '## '-Kapitel)
  - alle '## '-Kapitel des bereinigten Originaltexts (Public Domain)

Qualitaets-Guard: korrupte Bundles (PG-Boilerplate / keine Kapitel) werden
uebersprungen statt als kaputtes EPUB verschifft. Bei Fehler wird None
zurueckgegeben, damit der HTML-Build nicht abstuerzt.

Die Datei ist NUR ueber den Stripe-after_completion-Redirect erreichbar
(genau wie das HTML). Sie liegt unter /dl/ (robots.txt Disallow, nicht in
sitemap.xml).
"""
import os, re, json, zipfile, hashlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "corpus")
SITE = os.path.join(HERE, "..", "docs")
DL_ROOT = os.path.join(SITE, "dl")
SALT_FILE = os.path.join(HERE, "..", ".dl_salt")

_PG_LINE = re.compile(r"project gutenberg|gutenberg-tm|gutenberg\.(?:org|net)|pgdp\.net",
                      re.IGNORECASE)


# --- kleine lokale Kopie der Hashing-/Slug-Logik (kein Import-Zyklus) ------
def _load_salt():
    if not os.path.exists(SALT_FILE):
        try:
            import secrets
            val = secrets.token_hex(16)
        except Exception:
            import random
            val = "".join("%02x" % random.randrange(256) for _ in range(16))
        with open(SALT_FILE, "w", encoding="utf-8") as f:
            f.write(val)
    return open(SALT_FILE, encoding="utf-8").read().strip()


def download_hash(book_id, salt):
    return hashlib.sha256(f"{book_id}:{salt}".encode("utf-8")).hexdigest()[:16]


def slug_for(meta, book_id):
    t = (meta.get("title") or book_id).lower()
    s = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return s or book_id


def is_corrupt(content):
    if _PG_LINE.search(content):
        return True
    if not re.search(r"^##\s", content, re.MULTILINE):
        return True
    return False


def epub_path(book_id):
    meta_p = os.path.join(CORPUS, book_id, "product", "meta.json")
    meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
    salt = _load_salt()
    h = download_hash(book_id, salt)
    slug = slug_for(meta, book_id)
    return os.path.join(DL_ROOT, h, f"{slug}.epub")


# --- XML/HTML-Escaping ------------------------------------------------------
def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _esc_attr(s):
    return _esc(s).replace('"', "&quot;")


def md_to_xhtml(text):
    """Minimale, dependency-freie Markdown->XHTML-Umwandlung fuer einen
    Block-Text: '#'/'##'/'###' -> h1/h2/h3, Rest -> <p>."""
    out = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for b in blocks:
        lines = [l for l in b.splitlines() if l.strip()]
        if not lines:
            continue
        first = lines[0]
        m = re.match(r"^(#{1,6})\s+(.*)$", first)
        if m and len(lines) == 1:
            lvl = min(len(m.group(1)), 6)
            out.append(f"<h{lvl}>{_esc(m.group(2).strip())}</h{lvl}>")
            continue
        para = " ".join(l.strip() for l in lines if l.strip())
        out.append(f"<p>{_esc(para)}</p>")
    return "\n".join(out)


def _split_chapters(content):
    """Liefert (preamble_text, [(titel, body), ...]) aufgeteilt nach '## '."""
    lines = content.splitlines()
    preamble = []
    chapters = []
    cur_title = None
    cur = []
    seen = False
    for ln in lines:
        m = re.match(r"^##\s+(.*)$", ln)
        if m:
            seen = True
            if cur_title is not None or cur:
                chapters.append((cur_title, "\n".join(cur).strip()))
            cur_title = m.group(1).strip()
            cur = []
        else:
            (cur if seen else preamble).append(ln)
    if cur_title is not None or cur:
        chapters.append((cur_title, "\n".join(cur).strip()))
    # fuehrende H1 aus der Preamble entfernen (wird als EPUB-Titel genutzt)
    preamble_text = "\n".join(preamble).strip()
    preamble_text = re.sub(r"^\s*#\s+.*\n?", "", preamble_text).strip()
    return preamble_text, chapters


def guide_to_xhtml(sg):
    parts = []
    if sg.get("summary"):
        parts.append(f"<h2>Zusammenfassung</h2>\n<p>{_esc(sg['summary'])}</p>")
    if sg.get("setting"):
        parts.append(f"<h2>Zeit &amp; Setting</h2>\n<p>{_esc(sg['setting'])}</p>")
    if sg.get("characters"):
        items = "\n".join(f"<li>{_esc(c)}</li>" for c in sg["characters"])
        parts.append(f"<h2>Figurenliste</h2>\n<ul>{items}</ul>")
    if sg.get("questions"):
        items = "\n".join(f"<li>{_esc(q)}</li>" for q in sg["questions"])
        parts.append(f"<h2>Diskussionsfragen</h2>\n<ol>{items}</ol>")
    if sg.get("reading_plan"):
        items = "\n".join(f"<li>{_esc(p)}</li>" for p in sg["reading_plan"])
        parts.append(f"<h2>30-Tage-Leseplan</h2>\n<ol>{items}</ol>")
    if sg.get("chapters"):
        items = "\n".join(f"<li>Kap. {_esc(str(b.get('nr','')))}: {_esc(b.get('title',''))}</li>"
                          for b in sg["chapters"][:60])
        parts.append(f"<h2>Kapiteluebersicht</h2>\n<ol>{items}</ol>")
    return "\n".join(parts)


def _xhtml_doc(title, body):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" lang="de">\n'
        '<head><meta charset="utf-8"/>\n'
        f'<title>{_esc(title)}</title>\n'
        '</head>\n'
        f'<body>\n{body}\n</body>\n</html>\n'
    )


def build_epub(book_id):
    meta_p = os.path.join(CORPUS, book_id, "product", "meta.json")
    content_p = os.path.join(CORPUS, book_id, "product", "content.md")
    if not (os.path.exists(meta_p) and os.path.exists(content_p)):
        return None
    meta = json.load(open(meta_p, encoding="utf-8"))
    content = open(content_p, encoding="utf-8").read()
    if is_corrupt(content):
        print(f"  SKIP EPUB {book_id}: corrupt bundle -> not published")
        return None

    salt = _load_salt()
    h = download_hash(book_id, salt)
    slug = slug_for(meta, book_id)
    title = meta.get("title", book_id)
    author = meta.get("author", "Unbekannt")
    year = meta.get("year", "")
    year_s = f" ({year})" if year else ""

    dest_dir = os.path.join(DL_ROOT, h)
    os.makedirs(dest_dir, exist_ok=True)
    epub_path_out = os.path.join(dest_dir, f"{slug}.epub")

    # --- XHTML-Dokumente zusammenstellen (Reihenfolge = Spine) -------------
    docs = []  # (dateiname, titel, body_xhtml)

    # 1) Lese-Begleiter (falls gefuellt)
    sg_p = os.path.join(CORPUS, book_id, "product", "study_guide.json")
    if os.path.exists(sg_p):
        try:
            sg = json.load(open(sg_p, encoding="utf-8"))
            if sg.get("filled") and sg.get("summary"):
                g = guide_to_xhtml(sg)
                if g.strip():
                    docs.append(("guide.xhtml", f"Lese-Begleiter: {title}", g))
        except (ValueError, OSError):
            pass

    # 2) Preamble als Einleitung
    preamble_text, chapters = _split_chapters(content)
    if preamble_text.strip():
        docs.append(("intro.xhtml", "Einleitung", md_to_xhtml(preamble_text)))

    # 3) Originaltext-Kapitel
    for i, (ch_title, ch_body) in enumerate(chapters, start=1):
        label = ch_title or f"Kapitel {i}"
        docs.append((f"ch{i}.xhtml", label, md_to_xhtml(ch_body)))

    if not docs:
        print(f"  SKIP EPUB {book_id}: no usable content")
        return None

    # --- OPF / NAV ----------------------------------------------------------
    uid = "urn:uuid:" + hashlib.md5(
        f"{book_id}:{salt}".encode("utf-8")).hexdigest().replace("-", "")
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest_items = ['    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>']
    spine_items = ['    <itemref idref="nav"/>']
    for i, (fname, dtitle, _) in enumerate(docs, start=1):
        cid = f"doc{i}"
        manifest_items.append(
            f'    <item id="{cid}" href="{fname}" media-type="application/xhtml+xml"/>')
        spine_items.append(f'    <itemref idref="{cid}"/>')

    nav_li = "\n".join(
        f'      <li><a href="{fname}">{_esc_attr(dtitle)}</a></li>'
        for fname, dtitle, _ in docs)
    nav_xhtml = _xhtml_doc(
        f"{title} – Inhaltsverzeichnis",
        f'<h1>Inhaltsverzeichnis</h1>\n<nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">\n'
        f'<ol>\n{nav_li}\n  </ol>\n</nav>')

    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="bookid" xml:lang="de">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="bookid">{_esc(uid)}</dc:identifier>\n'
        f'    <dc:title>{_esc(title)} – Lese-Begleiter (Public Domain)</dc:title>\n'
        f'    <dc:creator>{_esc(author)}</dc:creator>\n'
        '    <dc:language>de</dc:language>\n'
        '    <meta property="dcterms:modified">' + modified + '</meta>\n'
        '  </metadata>\n'
        '  <manifest>\n'
        + "\n".join(manifest_items) + "\n"
        '  </manifest>\n'
        '  <spine>\n'
        + "\n".join(spine_items) + "\n"
        '  </spine>\n'
        '</package>\n')

    container = (
        '<?xml version="1.0"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendigitalfile:1.0">\n'
        '  <rootfiles>\n'
        '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
        '  </rootfiles>\n'
        '</container>\n')

    # --- ZIP schreiben (mimetype zuerst, unkomprimiert) --------------------
    try:
        with zipfile.ZipFile(epub_path_out, "w", zipfile.ZIP_DEFLATED) as z:
            mi = zipfile.ZipInfo("mimetype", date_time=(1980, 1, 1, 0, 0, 0))
            mi.compress_type = zipfile.ZIP_STORED
            mi.external_attr = 0o644 << 16
            z.writestr(mi, "application/epub+zip")
            z.writestr("META-INF/container.xml", container)
            z.writestr("OEBPS/content.opf", opf)
            z.writestr("OEBPS/nav.xhtml", nav_xhtml)
            for fname, dtitle, body in docs:
                z.writestr(f"OEBPS/{fname}", _xhtml_doc(dtitle, body))
    except Exception as e:
        print(f"  EPUB {book_id}: write error {e!r}")
        return None

    return epub_path_out


def build_all():
    """Alle Produkt-EPUBs erzeugen. Liefert (erzeugte_pfade, uebersprungene_ids)."""
    bids = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*"))
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "product", "meta.json"))
    )
    out, skipped = [], []
    for bid in bids:
        p = build_epub(bid)
        if p is None:
            skipped.append(bid)
        else:
            out.append(p)
    return out, skipped


if __name__ == "__main__":
    import glob
    paths, skipped = build_all()
    print(f"Generated {len(paths)} EPUB deliverables under {DL_ROOT}")
    for p in paths:
        print("  " + p)
    if skipped:
        print(f"SKIPPED (corrupt/no bundle): {skipped}")
