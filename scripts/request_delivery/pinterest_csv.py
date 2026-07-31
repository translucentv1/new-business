"""
Pinterest-CSV Generator: erzeugt eine CSV zum Bulk-Upload der 1300 Buch-Covers.
Jede Zeile: Titel, Beschreibung, Link zur Buy-Box (Stripe) + Querlink rtd.html.

Pinterest erlaubt CSV-Import (Business-Account noetig). Du laedst die CSV hoch,
Hermes hat die Links schon gesetzt. Massen-Pinning in Minuten.

KEIN Account/Credential noetig zum ERZEUGEN. Nur Upload (dein Pinterest-Business).
"""
import os
import re
import csv
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RTD = "https://translucentv1.github.io/new-business/rtd.html"
OUT_CSV = os.path.join(ROOT, "pinterest_upload.csv")

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def extract(dirpath):
    hp = os.path.join(dirpath, "index.html")
    if not os.path.exists(hp):
        return None
    txt = open(hp, encoding="utf-8", errors="ignore").read()
    m = TITLE_RE.search(txt)
    title = m.group(1).split(" – ")[0].strip() if m else None
    return title


def main():
    rows = []
    for dp, _, files in os.walk(ROOT):
        if "index.html" not in files:
            continue
        if any(x in dp for x in (".git", ".venv", "scripts")):
            continue
        title = extract(dp)
        if not title:
            continue
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        if rel == ".":
            rel = ""
        buy = f"https://translucentv1.github.io/new-business/{rel}/" if rel else "https://translucentv1.github.io/new-business/"
        rows.append({
            "Title": f"{title} – Lese-Begleiter",
            "Description": f"KI-Lese-Begleiter zu {title}. Jetzt als Guide oder Buch: {buy} | Eigenes erstellen: {RTD}",
            "Link": buy,
            "RTD_Link": RTD,
        })
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Title", "Description", "Link", "RTD_Link"])
        w.writeheader()
        w.writerows(rows)
    print(f"Pinterest CSV: {len(rows)} rows -> {OUT_CSV}")


if __name__ == "__main__":
    main()
