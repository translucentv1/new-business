"""
Batch-KDP-Generator: erzeugt KDP-Produkt-Specs fuer alle 1300 Buch-Landingpages.
Liest die Titel aus den */index.html (Public-Domain-Buecher) und erstellt pro Buch
ein vorbereitetes KDP-Notebook/Journal (speichern in kdp_products/).

Nur Prep — kein Upload (braucht Amazon-KDP-Account, manuell).
MEASURED: zaehlt erzeugte Specs, speichert JSON.
"""
import os
import re
import json
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "kdp_products")
PATTERN = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def extract_title(html_path):
    try:
        txt = open(html_path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return None
    m = PATTERN.search(txt)
    if not m:
        return None
    t = m.group(1)
    # strip " – Lese-Begleiter..." suffix if present
    t = re.split(r"\s*[–-]\s*", t)[0].strip()
    return t[:80] if t else None


def main():
    count = 0
    os.makedirs(OUT, exist_ok=True)
    for dirpath, _, files in os.walk(ROOT):
        if "index.html" not in files:
            continue
        if ".git" in dirpath or ".venv" in dirpath or "scripts" in dirpath:
            continue
        title = extract_title(os.path.join(dirpath, "index.html"))
        if not title:
            continue
        # reuse kdp_generator logic
        sys.path.insert(0, os.path.dirname(__file__))
        from kdp_generator import generate
        try:
            generate(title, niche="journal", size="6x9", pages=120, interior="lined")
            count += 1
        except Exception as e:
            print(f"skip {title}: {e}")
    print(f"KDP specs created: {count}")
    with open(os.path.join(OUT, "_count.txt"), "w") as f:
        f.write(str(count))


if __name__ == "__main__":
    main()
