"""
TB-2: PD-Text aufbereiten — Struktur + Begleit-Material.

Nimmt Rohtext aus corpus/<id>/text.txt, gliedert in Kapitel, baut
Inhaltsverzeichnis + Wortregister, erzeugt ein Produkt-Bundle in
corpus/<id>/product/ (content.md, description.md, meta.json).

KEIN eigenmaechtiges Umschreiben des Urheberwerks — nur Gliederung,
Register, Metadaten. Das ist die Agent-Differenzierung (Mehrwert).

PDF-Erzeugung: falls reportlab importierbar, wird content.pdf gebaut;
sonst nur markdown (Gumroad akzeptiert .md/.txt als digital file).
"""
import os, re, json, time

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")

# Kapitel-Erkennung (EN/DE, römisch + arabisch)
CHAPTER_RE = re.compile(
    r"^\s*(?:chapter|kapitel|book|buch|teil|part)\s+([IVXLC\d]+)\.?\s*[-–:]?\s*(.*)$",
    re.IGNORECASE | re.MULTILINE)

def split_chapters(text: str):
    parts = CHAPTER_RE.split(text)
    # parts[0] = front matter, then triples (num, title, body)
    if len(parts) < 4:
        return [("Gesamt", "", text)]
    chapters = []
    front = parts[0].strip()
    if front:
        chapters.append(("Vorspann", "", front))
    for i in range(1, len(parts), 3):
        num = parts[i].strip()
        title = parts[i + 1].strip() if i + 1 < len(parts) else ""
        body = parts[i + 2].strip() if i + 2 < len(parts) else ""
        chapters.append((num, title, body))
    return chapters

def build_index(chapters):
    lines = ["# Inhaltsverzeichnis\n"]
    for i, (num, title, _) in enumerate(chapters, 1):
        if title:
            t = title
        elif num == "Vorspann":
            t = "Vorspann"
        else:
            t = f"Kapitel {num}"
        lines.append(f"{i}. {t}")
    return "\n".join(lines)

def build_register(text, max_entries=200):
    # Einfaches Worthaeufigkeits-Register (Wörter >=5 Buchstaben, DE/EN)
    words = re.findall(r"[A-Za-zÄÖÜäöüß]{5,}", text)
    freq = {}
    for w in words:
        wl = w.lower()
        freq[wl] = freq.get(wl, 0) + 1
    top = sorted(freq.items(), key=lambda x: -x[1])[:max_entries]
    lines = ["# Wortregister (häufigste Begriffe)\n"]
    for w, c in top:
        lines.append(f"- {w} — {c}×")
    return "\n".join(lines)

def build_product(book_id: str):
    d = os.path.join(CORPUS, book_id)
    text_path = os.path.join(d, "text.txt")
    meta_path = os.path.join(d, "meta.json")
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"no text for {book_id}")
    text = open(text_path, encoding="utf-8").read()
    meta = json.load(open(meta_path, encoding="utf-8"))
    chapters = split_chapters(text)
    idx = build_index(chapters)
    reg = build_register(text)

    prod = os.path.join(d, "product")
    os.makedirs(prod, exist_ok=True)

    # content.md = strukturierter Haupttext + Anhang
    content = []
    for num, title, body in chapters:
        head = f"## {title}" if title else f"## Kapitel {num}"
        content.append(head + "\n\n" + body)
    content_md = "\n\n".join(content)
    full = f"# {meta['title']}\n\n_von {meta['author']}_\n\n{idx}\n\n---\n\n{content_md}\n\n---\n\n{reg}\n"
    with open(os.path.join(prod, "content.md"), "w", encoding="utf-8") as f:
        f.write(full)

    # description.md = Verkaufstext (faktisch, kein Fake)
    desc = (f"# {meta['title']}\n\n"
            f"Autor: {meta['author']}\n"
            f"Quelle: Project Gutenberg (Public Domain, EU Leben+70 Jahre)\n\n"
            f"Dieses Werk ist gemeinfrei. Diese Ausgabe wurde neu gegliedert "
            f"(Inhaltsverzeichnis + Wortregister) für bessere Lesbarkeit.\n\n"
            f"Umfang: {len(text)} Zeichen, {len(chapters)} Kapitel.")
    with open(os.path.join(prod, "description.md"), "w", encoding="utf-8") as f:
        f.write(desc)

    # meta.json
    prod_meta = {"book_id": book_id, "title": meta["title"], "author": meta["author"],
                 "chapters": len(chapters), "chars": len(text),
                 "built": int(time.time()), "files": ["content.md", "description.md"]}
    with open(os.path.join(prod, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(prod_meta, f, ensure_ascii=False, indent=2)

    # optional PDF
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        pdf = os.path.join(prod, "content.pdf")
        doc = SimpleDocTemplate(pdf, pagesize=A4)
        ss = getSampleStyleSheet()
        story = [Paragraph(meta["title"], ss["Title"]), Spacer(1, 12)]
        for num, title, body in chapters:
            story.append(Paragraph(f"{title}" if title else f"Kapitel {num}", ss["Heading2"]))
            story.append(Paragraph(body[:4000].replace("\n", "<br/>"), ss["BodyText"]))
            story.append(Spacer(1, 8))
        doc.build(story)
        prod_meta["files"].append("content.pdf")
        with open(os.path.join(prod, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(prod_meta, f, ensure_ascii=False, indent=2)
        print(f"  {book_id}: PDF gebaut")
    except ImportError:
        print(f"  {book_id}: reportlab fehlt -> nur markdown (ok)")
    return prod_meta

if __name__ == "__main__":
    import glob
    ids = [os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*")) if os.path.isdir(p)]
    for bid in ids:
        if os.path.exists(os.path.join(CORPUS, bid, "text.txt")):
            m = build_product(bid)
            print(f"built product {bid}: {m['title'][:40]} ({m['chapters']} chap)")
