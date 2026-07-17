"""
TB-1: PD-Quelle scannen — Project Gutenberg DE/EN Public-Domain Texte.

Holt Metadaten + rohen Text gemeinfreier Werke und speichert sie in corpus/.
Nur Public-Domain (Gutenberg markiert Lebensdaten -> EU Leben+70J sicher).
Kein Echtbetrieb, kein Account, free-to-build.
"""
import os, re, json, time, urllib.request, urllib.error

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
os.makedirs(CORPUS, exist_ok=True)

GUTENBERG_CATALOG = "https://www.gutenberg.org/cache/epub/feeds/pg-catalog.csv.zip"
# Wir nutzen die stabile Gutenberg-API fuer einzelne Werke:
# https://www.gutenberg.org/ebooks/<id>  und  /files/<id>/<id>-0.txt (plain text)

def fetch_text(book_id: str) -> str | None:
    """Lade plain-text eines Gutenberg-Werks. None bei Fehler."""
    urls = [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
    ]
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "pd-scanner/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode("utf-8", errors="ignore")
            if len(data) > 1000:
                return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            continue
    return None

def strip_gutenberg_header(text: str) -> str:
    """Entferne Gutenberg-Lizenz-Header/Footer ( zwischen *** START/END)."""
    m = re.search(r"\*{3}\s*START OF.*?\*{3}(.*?)\*{3}\s*END OF", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

def save_corpus(book_id: str, title: str, author: str, text: str):
    meta = {"id": book_id, "title": title, "author": author,
            "source": f"gutenberg:{book_id}", "fetched": int(time.time())}
    d = os.path.join(CORPUS, book_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(os.path.join(d, "text.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    return meta

def scan(ids: list[tuple[str, str, str]]):
    """ids = [(book_id, title, author), ...]. Scannt, speichert, retourniert Metadaten."""
    out = []
    for book_id, title, author in ids:
        text = fetch_text(book_id)
        if not text:
            print(f"  skip {book_id} ({title}): no text")
            continue
        clean = strip_gutenberg_header(text)
        meta = save_corpus(book_id, title, author, clean)
        out.append(meta)
        print(f"  saved {book_id}: {title[:50]} ({len(clean)} chars)")
    return out

if __name__ == "__main__":
    # Beispiel-IDs (Public-Domain, Europa Leben+70J):
    # 11 = Alice im Wunderland (Carroll, 1865), 1342 = Pride and Prejudice (Austen, 1813),
    # 158 = Emma (Austen), 25913 = Metamorphosen (Ovid, antik)
    samples = [
        ("11", "Alice's Adventures in Wonderland", "Lewis Carroll"),
        ("1342", "Pride and Prejudice", "Jane Austen"),
        ("158", "Emma", "Jane Austen"),
    ]
    res = scan(samples)
    print(f"scanned {len(res)} works -> corpus/")
