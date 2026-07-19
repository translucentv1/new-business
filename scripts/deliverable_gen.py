"""Deliverable generator (ADR-0013 / Spec 2026-07-18-download-gate).

Generates a self-contained HTML eBook per book under:
    docs/dl/<hash>/<slug>.html
where
    hash = sha256(f"{book_id}:{SALT}")[:16]
    SALT = contents of .dl_salt (created randomly if missing; gitignored, local-only)
    slug = derived from the book title (stable, ascii)

The download URL is NEVER linked on any public page. It is served only via
the Stripe after_completion redirect (set in TB-10). It is excluded from
sitemap.xml and Disallowed in robots.txt so crawlers/seekers can't find it.

No external assets, no <script src>, no http(s):// links -> fully offline
readable. Tier-1 format per spec. Tier-2 (EPUB via zipfile) is a later ticket.

Quality guard: bundles whose content is corrupt (contains a Project Gutenberg
reference/credit, or has no detectable first chapter) are SKIPPED rather than
published as a broken deliverable. The id is reported so it can be fixed
deliberately (not silently shipped).
"""
import os, re, json, glob, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "corpus")
SITE = os.path.join(HERE, "..", "docs")
DL_ROOT = os.path.join(SITE, "dl")
SALT_FILE = os.path.join(HERE, "..", ".dl_salt")
GH_PAGES_BASE = "https://translucentv1.github.io/new-business"

# A bundle is corrupt if it still carries PG boilerplate or has no real chapter
# structure. We must not ship a "free full text" page that leaks gutenberg
# credits or a mashed-together file.
_PG_LINE = re.compile(r"project gutenberg|gutenberg-tm|gutenberg\.(?:org|net)|pgdp\.net",
                     re.IGNORECASE)


def is_corrupt(content: str) -> bool:
    if _PG_LINE.search(content):
        return True
    # needs at least one '## ' chapter heading to be a usable preview/deliverable
    if not re.search(r"^##\s", content, re.MULTILINE):
        return True
    return False


def _load_salt() -> str:
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


def download_hash(book_id: str, salt: str) -> str:
    """Deterministic, reproducible hash of book_id+salt (first 16 hex chars)."""
    return hashlib.sha256(f"{book_id}:{salt}".encode("utf-8")).hexdigest()[:16]


def slug_for(meta: dict, book_id: str) -> str:
    t = (meta.get("title") or book_id).lower()
    s = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return s or book_id


def deliverable_path(book_id: str) -> str:
    """Local absolute path of the generated download file (no existence check)."""
    meta_p = os.path.join(CORPUS, book_id, "product", "meta.json")
    meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
    salt = _load_salt()
    h = download_hash(book_id, salt)
    slug = slug_for(meta, book_id)
    return os.path.join(DL_ROOT, h, f"{slug}.html")


def deliverable_url(book_id: str) -> str:
    """Absolute GitHub-Pages URL of the download file (served only post-payment)."""
    meta_p = os.path.join(CORPUS, book_id, "product", "meta.json")
    meta = json.load(open(meta_p, encoding="utf-8")) if os.path.exists(meta_p) else {}
    salt = _load_salt()
    h = download_hash(book_id, salt)
    slug = slug_for(meta, book_id)
    return f"{GH_PAGES_BASE}/dl/{h}/{slug}.html"


def _md_to_html(text: str) -> str:
    """Minimal, dependency-free Markdown->HTML for a self-contained reader page.

    Headings (#/##/###) become <h1>/<h2>/<h3>; blank-line separated blocks
    become <p>. No external anything. Input is escaped; only our own tags
    are emitted, so it stays safe and self-contained.
    """
    esc = lambda s: (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    out = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = block.splitlines()
        # Heading detection on the first non-empty line.
        stripped = [l for l in lines if l.strip()]
        if not stripped:
            continue
        first = stripped[0]
        m = re.match(r"^(#{1,6})\s+(.*)$", first)
        if m and len(stripped) == 1:
            level = min(len(m.group(1)), 6)
            out.append(f"<h{level}>{esc(m.group(2).strip())}</h{level}>")
            continue
        # Otherwise treat the whole block as a paragraph (join wrapped lines).
        para = " ".join(l.strip() for l in lines if l.strip())
        out.append(f"<p>{esc(para)}</p>")
    return "\n".join(out)


def build_companion_html(book_id: str, meta: dict, content: str, epub_href: str = "") -> str:
    """ADR-0018: das verkaufsfaehige Deliverable ist der Lese-Begleiter
    (gefuellte study_guide.json), nicht der Rohtext. Rohtext wird als
    optionale 'Volltext'-Sektion unten angehaengt (ebenfalls PD, bereinigt)."""
    sg_p = os.path.join(CORPUS, book_id, "product", "study_guide.json")
    esc = lambda s: (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    title = meta.get("title", book_id)
    author = meta.get("author", "Unbekannt")
    year = meta.get("year", "")
    year_s = f" ({year})" if year else ""

    if not os.path.exists(sg_p):
        # Fallback: nur Rohtext
        return None
    sg = json.load(open(sg_p, encoding="utf-8"))

    # Begleiter-Bloecke
    parts = []
    if sg.get("summary"):
        parts.append(f"<h2>Zusammenfassung</h2>\n<p>{esc(sg['summary'])}</p>")
    if sg.get("setting"):
        parts.append(f"<h2>Zeit & Setting</h2>\n<p>{esc(sg['setting'])}</p>")
    if sg.get("characters"):
        items = "\n".join(f"<li>{esc(c)}</li>" for c in sg["characters"])
        parts.append(f"<h2>Figurenliste</h2>\n<ul>{items}</ul>")
    if sg.get("questions"):
        items = "\n".join(f"<li>{esc(q)}</li>" for q in sg["questions"])
        parts.append(f"<h2>Diskussionsfragen</h2>\n<ol>{items}</ol>")
    if sg.get("reading_plan"):
        items = "\n".join(f"<li>{esc(p)}</li>" for p in sg["reading_plan"])
        parts.append(f"<h2>30-Tage-Leseplan</h2>\n<ol>{items}</ol>")
    # Kapiteluebersicht (Geruest aus study_guide)
    if sg.get("chapters"):
        items = "\n".join(
            f"<li>Kap. {b['nr']}: {esc(b['title'])}</li>" for b in sg["chapters"][:60])
        parts.append(f"<h2>Kapiteluebersicht</h2>\n<ol>{items}</ol>")

    companion = "\n".join(parts)

    # Volltext (bereinigt) als optionale Sektion
    full_html = _md_to_html(content)
    full_section = (
        '<hr>\n<h2>Volltext (Public Domain)</h2>\n<p class="note">Der vollständige, '
        'bereinigte Originaltext – gemeinfrei.</p>\n' + full_html
    ) if content.strip() else ""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} – Lese-Begleiter von {esc(author)}{year_s}</title>
  <style>
    body{{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.7;color:#1a1a1a}}
    h1{{font-size:1.9em}} h2{{font-size:1.4em;margin-top:1.6em}} h3{{font-size:1.15em}}
    .byline{{color:#666;font-style:italic;margin-top:-.4em}}
    .note{{margin:1.4em 0;padding:1em;background:#f4f7ff;border-left:4px solid #2962ff;border-radius:6px;font-size:.9em}}
    .epub-dl{{margin:1.2em 0}}
    .epub-dl a{{display:inline-block;background:#2962ff;color:#fff;padding:.6em 1.1em;border-radius:6px;text-decoration:none;font-weight:bold}}
    .epub-dl a:hover{{background:#1c44b2}}
    hr{{border:none;border-top:1px solid #eee;margin:2em 0}}
    li{{margin:.3em 0}}
  </style>
</head>
<body>
  <article>
    <h1>Lese-Begleiter: {esc(title)}</h1>
    <p class="byline">von {esc(author)}{year_s}</p>
    <div class="note">Dein gekaufter Lese-Begleiter (KI-gestützte Analyse + gemeinfreier
       Originaltext). Offline lesbar, nur hier verfügbar – als HTML und EPUB.</div>
    <p class="epub-dl"><a href="{epub_href}">⬇ EPUB-Version herunterladen (Kindle / Apple Books / Tolino)</a></p>
    <hr>
    {companion}
    {full_section}
  </article>
</body>
</html>
"""
    return html


def build_one(book_id: str):
    meta_p = os.path.join(CORPUS, book_id, "product", "meta.json")
    content_p = os.path.join(CORPUS, book_id, "product", "content.md")
    if not (os.path.exists(meta_p) and os.path.exists(content_p)):
        raise FileNotFoundError(f"Missing product bundle for {book_id}")
    meta = json.load(open(meta_p, encoding="utf-8"))
    content = open(content_p, encoding="utf-8").read()
    if is_corrupt(content):
        # Do not ship a broken/credit-leaking deliverable. Report + skip.
        print(f"  SKIP {book_id}: corrupt bundle (PG ref or no chapter structure) -> not published")
        return None
    salt = _load_salt()
    h = download_hash(book_id, salt)
    slug = slug_for(meta, book_id)
    epub_href = f"{slug}.epub"
    # ADR-0018: Begleiter als Haupt-Deliverable, wenn gefuellt
    sg_p = os.path.join(CORPUS, book_id, "product", "study_guide.json")
    html = None
    if os.path.exists(sg_p):
        try:
            html = build_companion_html(book_id, meta, content, epub_href)
        except Exception as e:
            print(f"  {book_id}: companion build warn {e!r} -> fallback rohtext")
            html = None
    if html is None:
        # Fallback auf reinen Rohtext (altes Verhalten)
        body_html = _md_to_html(content)
        esc = lambda s: (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        title = meta.get("title", book_id)
        author = meta.get("author", "Unbekannt")
        year = meta.get("year", "")
        year_s = f" ({year})" if year else ""
        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} von {esc(author)}{year_s} – eBook (Download)</title>
  <style>
    body{{font-family:Georgia,serif;max-width:42em;margin:2em auto;padding:0 1em;line-height:1.7;color:#1a1a1a}}
    h1{{font-size:1.9em}} h2{{font-size:1.4em;margin-top:1.6em}} h3{{font-size:1.15em}}
    .byline{{color:#666;font-style:italic;margin-top:-.4em}}
    .note{{margin:1.4em 0;padding:1em;background:#f4f7ff;border-left:4px solid #2962ff;border-radius:6px;font-size:.9em}}
    .epub-dl{{margin:1.2em 0}}
    .epub-dl a{{display:inline-block;background:#2962ff;color:#fff;padding:.6em 1.1em;border-radius:6px;text-decoration:none;font-weight:bold}}
    .epub-dl a:hover{{background:#1c44b2}}
    hr{{border:none;border-top:1px solid #eee;margin:2em 0}}
  </style>
</head>
<body>
  <article>
    <h1>{esc(title)}</h1>
    <p class="byline">von {esc(author)}{year_s}</p>
    <div class="note">Dies ist dein gekauftes eBook (Public Domain, neu gegliedert und
       mit Register versehen). Es liegt nur hier und ist offline lesbar – als HTML und EPUB.</div>
    <p class="epub-dl"><a href="{epub_href}">⬇ EPUB-Version herunterladen (Kindle / Apple Books / Tolino)</a></p>
    <hr>
    {body_html}
  </article>
</body>
</html>
"""
    dest_dir = os.path.join(DL_ROOT, h)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"{slug}.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    # Tier-2 (ADR-0013): EPUB-Deliverable ins selbe (nicht verlinkte) Gate-Verzeichnis.
    try:
        from epub_gen import build_epub
        ep = build_epub(book_id)
        if ep:
            print(f"  + EPUB {book_id} -> {ep}")
    except Exception as e:
        print(f"  {book_id}: EPUB build warn {e!r}")
    return dest


def build_all() -> tuple:
    """Return (paths_built, skipped_ids)."""
    bids = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*"))
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "product", "meta.json"))
    )
    out, skipped = [], []
    for bid in bids:
        d = build_one(bid)
        if d is None:
            # Ensure no stale deliverable from a previous (broken) build lingers.
            stale = deliverable_path(bid)
            if os.path.exists(stale):
                os.remove(stale)
                # remove now-empty hash dir if present
                hd = os.path.dirname(stale)
                if os.path.isdir(hd) and not os.listdir(hd):
                    os.rmdir(hd)
            skipped.append(bid)
        else:
            out.append(d)
    return out, skipped


if __name__ == "__main__":
    paths = build_all()
    print(f"Generated {len(paths)} download deliverables under {DL_ROOT}")
    for p in paths:
        print("  " + p)
