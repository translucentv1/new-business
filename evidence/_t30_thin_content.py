#!/usr/bin/env python3
"""Thin-Content-Messung: wieviel Text einer blog/-Seite ist BOILERPLATE
(auf >=90 % der Seiten identisch) und wieviel ist seitenspezifisch?

Der exakte Rumpf-Hash (evidence/_t30_blog_dupes.py) sagt 0 % Duplikate, weil
Titel+Beschreibung pro Seite verschieden sind. Diese Messung geht feiner vor:
Satz-Ebene. Ein Satz, der auf fast allen Seiten steht, ist Boilerplate.
"""
import os
import re
import statistics
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def text_of(html):
    h = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", html)
    h = re.sub(r"(?s)<head\b.*?</head>", " ", h)
    t = re.sub(r"<[^>]+>", " ", h)
    t = re.sub(r"&[a-z]+;|&#\d+;", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def sentences(t):
    parts = re.split(r"(?<=[.!?:])\s+|\s+[–·]\s+", t)
    return [p.strip() for p in parts if len(p.strip().split()) >= 3]


def main(rel="blog", thresh=0.90):
    d = os.path.join(ROOT, rel)
    files = sorted(f for f in os.listdir(d) if f.endswith(".html"))
    per_file = {}
    cnt = Counter()
    for f in files:
        t = text_of(open(os.path.join(d, f), encoding="utf-8", errors="replace").read())
        ss = sentences(t)
        per_file[f] = (t, ss)
        for s in set(ss):
            cnt[s] += 1
    n = len(files)
    boiler = {s for s, c in cnt.items() if c >= thresh * n}
    print(f"== {rel}/ Thin-Content-Analyse ==")
    print(f"Seiten: {n}   Boilerplate-Saetze (auf >={thresh:.0%} der Seiten): {len(boiler)}")
    tot, uniq = [], []
    for f, (t, ss) in per_file.items():
        w_all = len(t.split())
        w_uni = sum(len(s.split()) for s in ss if s not in boiler)
        tot.append(w_all)
        uniq.append(w_uni)
    print(f"Woerter gesamt   : Median {statistics.median(tot):.0f}  min {min(tot)}  max {max(tot)}")
    print(f"Woerter EINZIGARTIG: Median {statistics.median(uniq):.0f}  min {min(uniq)}  max {max(uniq)}")
    share = 100.0 * statistics.median(uniq) / statistics.median(tot)
    print(f"=> seitenspezifischer Anteil (Median): {share:.1f} %")
    print(f"=> Seiten mit <40 einzigartigen Woertern: "
          f"{sum(1 for u in uniq if u < 40)}/{n}")
    print("\nBoilerplate (Auszug):")
    for s in sorted(boiler, key=len, reverse=True)[:6]:
        print("  -", (s[:110] + "...") if len(s) > 110 else s)
    worst = sorted(zip(per_file.keys(), uniq), key=lambda x: x[1])[:5]
    print("\nDuennste Seiten (einzigartige Woerter):")
    for f, u in worst:
        print(f"  {u:4d}  {f}")


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["blog"]))
