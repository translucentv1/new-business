#!/usr/bin/env python3
"""Duplikatmessung fuer blog/ mit DERSELBEN Methode wie beim t/-Befund (2026-08-10).

Eigennamen -> X, Zahlen -> N, dann Hash des Rumpftextes. Gruppen >1 = Duplikat.
Ausgabe: Gesamtzahl, Duplikatquote, groesste Gruppen, Median-Woerter.
"""
import hashlib
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def text_of(html):
    h = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", html)
    h = re.sub(r"(?s)<head\b.*?</head>", " ", h)
    t = re.sub(r"<[^>]+>", " ", h)
    t = re.sub(r"&[a-z]+;|&#\d+;", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def rumpf(t):
    """Eigennamen (Grossbuchstabenwoerter) -> X, Zahlen -> N."""
    t = re.sub(r"\d+([.,]\d+)?", "N", t)
    t = re.sub(r"\b[A-ZÄÖÜ][\wäöüß-]+", "X", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def measure(d):
    files = sorted(f for f in os.listdir(d) if f.endswith(".html"))
    groups = defaultdict(list)
    words = []
    for f in files:
        html = open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
        t = text_of(html)
        words.append(len(t.split()))
        groups[hashlib.sha1(rumpf(t).encode()).hexdigest()].append(f)
    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    n_dupe = sum(len(v) for v in dupes.values())
    return files, groups, dupes, n_dupe, words


def main():
    for rel in sys.argv[1:] or ["blog", "t", "seo"]:
        d = os.path.join(ROOT, rel)
        if not os.path.isdir(d):
            print(f"== {rel}/ == nicht vorhanden")
            continue
        files, groups, dupes, n_dupe, words = measure(d)
        if not files:
            print(f"== {rel}/ == 0 Dateien")
            continue
        q = 100.0 * n_dupe / len(files)
        print(f"== {rel}/ ==")
        print(f"  Dateien: {len(files)}  Median Woerter: {statistics.median(words):.0f}"
              f"  min/max: {min(words)}/{max(words)}")
        print(f"  in Duplikatgruppen: {n_dupe}/{len(files)} = {q:.1f} %")
        sizes = sorted((len(v) for v in dupes.values()), reverse=True)[:5]
        print(f"  groesste Gruppen: {sizes if sizes else '-'}")
        for v in sorted(dupes.values(), key=len, reverse=True)[:1]:
            print(f"  Beispiel-Gruppe ({len(v)}): {', '.join(sorted(v)[:4])} ...")
        print(f"  eindeutige Ruempfe: {len(groups)}")


if __name__ == "__main__":
    main()
