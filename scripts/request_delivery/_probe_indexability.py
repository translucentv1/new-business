"""Einmal-Sonde: Verteilung von <meta name="robots"> im ausgelieferten Baum.

Zweck: belegen, welche live ausgelieferten Seiten noindex tragen.
Keine stehende Pruefung -> braucht keinen --selftest (Ad-hoc-Sonde).
"""

import os
import re
from collections import Counter

PAT = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', re.I
)
SKIP_DIRS = {".venv", "node_modules", ".git", "__pycache__"}


def main() -> None:
    vals: Counter = Counter()
    noindex: list[str] = []
    total = 0
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not fname.endswith(".html"):
                continue
            rel = os.path.join(dirpath, fname).replace("\\", "/").lstrip("./")
            if rel.startswith("docs/"):
                continue
            total += 1
            try:
                text = open(rel, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            match = PAT.search(text)
            value = match.group(1).strip().lower() if match else "(kein meta robots)"
            vals[value] += 1
            if "noindex" in value:
                noindex.append(rel)

    print(f"HTML-Dateien im Baum (ohne .venv/docs): {total}")
    print("--- Verteilung meta robots ---")
    for key, count in vals.most_common():
        print(f"  {count:6d}  {key}")
    print(f"--- Seiten mit NOINDEX: {len(noindex)} ---")
    for path in sorted(noindex):
        print("  ", path)


if __name__ == "__main__":
    main()
