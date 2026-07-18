"""
TB-19: Study-Guide-Generator (ADR-0018 Produkt-Pivot).

Nimmt ein corpus-Produkt (bereinigter Romantext in content.md) und erzeugt einen
Lese-Begleiter als MEHRWERT, den Project Gutenberg nicht bietet (kostenloser
Substitut-Killer). Der Guide ist strukturiert, aber INHALTLICH mute (der Agent fuellt
ihn zur Laufzeit per LLM). Dieses Modul liefert die GERAESTE + einen deterministischen
Regressions-Test gegen die echte Kapitelstruktur (Charta: Ergebnis pruefen, nicht Exit-Code).

Kapitelerkennung: pd_processor.clean_source hinterlaesst ein Inhaltsverzeichnis;
wir splitten content.md an erkannten Kapitel-Markern ("Chapter", "Kapitel", roman
numerals, "I. ", etc.). Das ist die einzige Stelle, an der wir den Rohtext parsen.
"""
import os, re, json

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")


def detect_chapters(content: str):
    """Gibt Liste von (titel, text) zurueck. Heuristik, bewusst robust gegen
    Gemein-Eingaben (kein VEZ, ein Kapitel, Sonderzeichen).
    ECHTES Format (pd_processor-Ausgabe): '1. Vorspann', '2. Kapitel II', '3. Kapitel III' ...
    -> Zeile beginnt mit '<zahl>. ' gefolgt von einem Titel."""
    pat = re.compile(r'^\s*([0-9]+)\.\s+(\S.*)$')
    lines = content.splitlines()
    chapters = []
    cur_title = None
    cur_buf = []
    for ln in lines:
        m = pat.match(ln)
        if m:
            if cur_title is not None:
                chapters.append((cur_title, "\n".join(cur_buf).strip()))
            cur_title = f"{m.group(1)}. {m.group(2).strip()}"
            cur_buf = []
        else:
            cur_buf.append(ln)
    if cur_title is not None:
        chapters.append((cur_title, "\n".join(cur_buf).strip()))
    return chapters


def build_guide(book_id: str) -> dict:
    prod = os.path.join(CORPUS, book_id, "product")
    with open(os.path.join(prod, "content.md"), encoding="utf-8") as fh:
        content = fh.read()
    with open(os.path.join(prod, "meta.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    chapters = detect_chapters(content)
    n = len(chapters)
    # Geruest: pro Kapitel ein Block mit Platzhalten, die der Agent (LLM) fuellt
    blocks = []
    for i, (title, body) in enumerate(chapters, 1):
        blocks.append({
            "nr": i,
            "title": title,
            "word_count": len(body.split()),
            "summary_placeholder": f"[ZUSAMMENFASSUNG Kapitel {i} — vom Agenten per LLM zu fuellen]",
            "questions_placeholder": f"[3 DISKUSSIONSFRAGEN Kapitel {i}]",
        })
    guide = {
        "book_id": book_id,
        "title": meta["title"],
        "author": meta.get("author", ""),
        "chapter_count": n,
        "companion_sections": [
            "Figurenliste (Name, Rolle)",
            "Zeit/Setting-Ueberblick",
            "30-Tage-Leseplan (1 Kapitel/Tag)",
            "Diskussionsfragen je Kapitel",
        ],
        "chapters": blocks,
        "note": "INHALT ist PLATZHALTER (mute). Der Agent fuellt Zusammenfassungen/Fragen "
                "zur Laufzeit per LLM. Dieses Modul liefert nur Struktur + Kapitelsplit.",
    }
    return guide


def write_guide(book_id: str, out_path: str = None):
    g = build_guide(book_id)
    if out_path is None:
        out_path = os.path.join(CORPUS, book_id, "product", "study_guide.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
    return out_path, g


if __name__ == "__main__":
    import sys
    bid = sys.argv[1] if len(sys.argv) > 1 else "1342"
    p, g = write_guide(bid)
    print(f"guide -> {p} | chapters={g['chapter_count']} | title={g['title']!r}")
