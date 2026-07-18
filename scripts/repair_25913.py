"""TB-13a: Repair des korrupten Bundle 25913 (falsch als 'Metamorphosen/Ovid'
beschriftet). MEASURED: corpus/25913/text.txt enthaelt tatsaechlich
'Tales of Folk and Fairies' von Katharine Pyle (gutenberg.org/ebooks/25913).

Der Rohtext ist eine MAERCHENSAMMLUNG (14 Tales), keine einzelne Erzaehlung.
pd_processor.split_chapters erkennt nur 'Chapter/Kapitel N' -> 1 Kapitel ->
der Preview wuerde das ganze Buch leaken (Conversion-Killer). Deshalb hier
ein dedizierter Tale-Splitter anhand der Inhaltsverzeichnis-Titel.

Ausserdem: clean_source liess die 'pgdp.net'-Credit-Zeile durch (nur
gutenberg.org/net wurde gefiltert) -> content.md enthielt PG-Boilerplate ->
deliverable_gen.is_corrupt() sperrte 25913. Dieser Repair entfernt die
Header/Footer komplett, sodass kein PG-Leak uebrig bleibt.

Erzeugt:
  corpus/25913/product/content.md   (14 Tales, TOC, Wortregister, kein PG-Leak)
  corpus/25913/product/description.md
  corpus/25913/product/meta.json
  corpus/25913/meta.json            (korrigierter Titel/Autor)

KEIN Hard Stop: nur lokale Datei-Verarbeitung, kein Account/Geld/Netz.
"""
import os, re, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "corpus")
BOOK = "25913"
D = os.path.join(CORPUS, BOOK)
text_path = os.path.join(D, "text.txt")

# Inhaltsverzeichnis-Titel (MEASURED aus text.txt Zeilen 49-76).
TITLES = [
    "THE MEESTER STOORWORM",
    "JEAN MALIN AND THE BULL-MAN",
    "THE WIDOW'S SON",
    "THE WISE GIRL",
    "THE HISTORY OF ALI COGIA",
    "OH!",
    "THE TALKING EGGS",
    "THE FROG PRINCESS",
    "THE MAGIC TURBAN, THE MAGIC SWORD",
    "THE THREE SILVER CITRONS",
    "THE MAGIC PIPE",
    "THE TRIUMPH OF TRUTH",
    "LIFE'S SECRET",
    "DAME PRIDGETT AND THE FAIRIES",
]

TITLE_DISPLAY = {
    "THE MEESTER STOORWORM": "The Meester Stoorworm",
    "JEAN MALIN AND THE BULL-MAN": "Jean Malin and the Bull-Man",
    "THE WIDOW'S SON": "The Widow's Son",
    "THE WISE GIRL": "The Wise Girl",
    "THE HISTORY OF ALI COGIA": "The History of Ali Cogia",
    "OH!": "Oh!",
    "THE TALKING EGGS": "The Talking Eggs",
    "THE FROG PRINCESS": "The Frog Princess",
    "THE MAGIC TURBAN, THE MAGIC SWORD":
        "The Magic Turban, the Magic Sword and the Magic Carpet",
    "THE THREE SILVER CITRONS": "The Three Silver Citrons",
    "THE MAGIC PIPE": "The Magic Pipe",
    "THE TRIUMPH OF TRUTH": "The Triumph of Truth",
    "LIFE'S SECRET": "Life's Secret",
    "DAME PRIDGETT AND THE FAIRIES": "Dame Pridgett and the Fairies",
}


def _title_case(t: str) -> str:
    return TITLE_DISPLAY.get(t, " ".join(w.capitalize() for w in t.split()))


def main():
    raw = open(text_path, encoding="utf-8").read()
    lines = raw.splitlines()

    # Header bis zur ersten echten Tale-Ueberschrift abschneiden.
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "THE MEESTER STOORWORM":
            start = i
            break
    if start is None:
        raise RuntimeError("Tale-Start 'THE MEESTER STOORWORM' nicht gefunden")

    # Footer (End of Project Gutenberg) abschneiden.
    end = len(lines)
    for i, ln in enumerate(lines):
        if ln.strip().startswith("End of Project Gutenberg"):
            end = i
            break

    body_lines = lines[start:end]

    # Position jeder Tale-Ueberschrift. Manche Titel stehen im Inhaltsverzeichnis
    # ueber zwei Zeilen; im Body ist die Ueberschrift aber eine einzelne (ggf.
    # laengere) Zeile. Daher startswith-Match gegen den (gekuerzten) Titel-Key.
    positions = []
    for t in TITLES:
        found = False
        for i, ln in enumerate(body_lines):
            if ln.strip().startswith(t):
                positions.append((t, i))
                found = True
                break
        if not found:
            print(f"  WARN: Tale nicht gefunden: {t}")

    if not positions:
        raise RuntimeError("Keine Tale-Ueberschriften gefunden")

    # Kapitel bauen (Titel + optionale Subtitle-Zeile + Body).
    chapters = []
    for idx, (t, pos) in enumerate(positions):
        j = pos + 1
        sub = ""
        pos2 = pos
        if j < len(body_lines):
            nxt = body_lines[j].strip()
            if nxt and not nxt.isupper() and len(nxt) < 60 and not nxt[0].isdigit():
                sub = nxt
                pos2 = j
        nxt_pos = positions[idx + 1][1] if idx + 1 < len(positions) else len(body_lines)
        chap_body = "\n".join(body_lines[pos2 + 1:nxt_pos]).strip()
        chapters.append((t, sub, chap_body))

    # content.md
    toc = "\n".join(f"{i+1}. {_title_case(t)}" for i, (t, _, _) in enumerate(chapters))
    blocks = [f"# Tales of Folk and Fairies\n\n_von Katharine Pyle_\n\n# Inhaltsverzeichnis\n\n{toc}\n"]
    for t, sub, chap_body in chapters:
        block = f"## {_title_case(t)}"
        if sub:
            block += f"\n\n_{sub}_"
        block += f"\n\n{chap_body}"
        blocks.append(block)
    content = "\n\n---\n\n".join(blocks) + "\n"

    # Wortregister (DE/EN, >=5 Buchstaben).
    words = re.findall(r"[A-Za-zÄÖÜäöüß]{5,}", content)
    freq = {}
    for w in words:
        freq[w.lower()] = freq.get(w.lower(), 0) + 1
    top = sorted(freq.items(), key=lambda x: -x[1])[:200]
    reg = "\n".join(f"- {w} — {c}×" for w, c in top)
    content += f"\n---\n\n# Wortregister (häufigste Begriffe)\n\n{reg}\n"

    # Schreiben
    prod = os.path.join(D, "product")
    os.makedirs(prod, exist_ok=True)
    with open(os.path.join(prod, "content.md"), "w", encoding="utf-8") as f:
        f.write(content)

    desc = (
        "# Tales of Folk and Fairies\n\n"
        "Autor: Katharine Pyle\n"
        "Quelle: Project Gutenberg (Public Domain, EU Leben+70 Jahre)\n\n"
        "Dieses Werk ist gemeinfrei. Diese Ausgabe wurde neu gegliedert "
        "(Inhaltsverzeichnis + Wortregister) für bessere Lesbarkeit.\n\n"
        f"Umfang: {len(content)} Zeichen, {len(chapters)} Kapitel (Märchen)."
    )
    with open(os.path.join(prod, "description.md"), "w", encoding="utf-8") as f:
        f.write(desc)

    prod_meta = {
        "book_id": BOOK,
        "title": "Tales of Folk and Fairies",
        "author": "Katharine Pyle",
        "chapters": len(chapters),
        "chars": len(content),
        "built": int(time.time()),
        "files": ["content.md", "description.md"],
    }
    with open(os.path.join(prod, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(prod_meta, f, ensure_ascii=False, indent=2)

    root_meta = {
        "id": BOOK,
        "title": "Tales of Folk and Fairies",
        "author": "Katharine Pyle",
        "source": "gutenberg:25913",
        "fetched": int(time.time()),
    }
    with open(os.path.join(D, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(root_meta, f, ensure_ascii=False, indent=2)

    # Study-Guide-Geruest (14 Tales). Altes Geruest hatte chapter_count=1
    # von der falschen 'Metamorphosen'-Meta -> muss neu aufgebaut werden.
    blocks = []
    for i, (t, sub, _) in enumerate(chapters, 1):
        blocks.append({
            "nr": i,
            "title": f"{i}. {_title_case(t)}",
            "word_count": 0,
            "summary_placeholder": f"[ZUSAMMENFASSUNG Kapitel {i} — vom Agenten per LLM zu fuellen]",
            "questions_placeholder": f"[3 DISKUSSIONSFRAGEN Kapitel {i}]",
        })
    guide = {
        "book_id": BOOK,
        "title": "Tales of Folk and Fairies",
        "author": "Katharine Pyle",
        "chapter_count": len(chapters),
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
    with open(os.path.join(prod, "study_guide.json"), "w", encoding="utf-8") as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)

    # Verifikation (MEASURED)
    pg_leak = len(re.findall(r"project gutenberg|gutenberg-tm|pgdp\.net", content, re.IGNORECASE))
    print(f"  chapters={len(chapters)} chars={len(content)} PG-Leak-Zeilen={pg_leak}")
    print(f"  Titel: {prod_meta['title']} / {prod_meta['author']}")
    if pg_leak:
        print("  FEHLER: PG-Leak verblieben!")
    else:
        print("  OK: kein PG-Leak in content.md")
    return prod_meta


if __name__ == "__main__":
    main()
