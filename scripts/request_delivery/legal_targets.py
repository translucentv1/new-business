"""Gemeinsame Ableitung der Zielmenge fuer die Rechtslink-Pruefer (Ticket 29).

Warum ein eigenes Modul: `legal_link_audit.py` (Baum) und
`verify_ticket13_live.py` (LIVE) meinen DIESELBE Seitenmenge. Bis Ticket 29
hatte jeder seine eigene Kopie der Glob-Liste ("*.html", "blog/*.html") --
beide veralteten still, waehrend der Baum um `seo/` (693) und `t/` (468) wuchs.
Merkregel Ticket 17: zwei Pruefer, die dieselbe Menge meinen, muessen dieselbe
Ableitungsregel benutzen, sonst driften sie auseinander. Also: eine Quelle.

Ableitungsbasis ist der REKURSIVE Baum, nicht eine Verzeichnisliste. Eine
Verzeichnisliste ist genau die eingefrorene Stichprobe aus Ticket 17, nur eine
Ebene hoeher.
"""
from __future__ import annotations

import os
import subprocess

# Die drei Pflichtlinks. Ein Pflicht-SET wird vollzaehlig geprueft, nie ein
# Merkmal daraus (Merkregel Ticket 17).
REQUIRED = ("impressum.html", "datenschutz.html", "agb.html")

# Verzeichnisse, die GitHub Pages nicht ausliefert bzw. die nicht zum Baum
# gehoeren. Gegen `git ls-tree` gegengemessen (2026-08-10: os.walk 1287 ==
# git-Tree 1287, 0 Drift) -- die Liste darf die Zielmenge also nicht verkuerzen.
SKIP_DIRS = frozenset({".git", ".hermes", "node_modules", "__pycache__", ".venv", "venv"})

# Bezahlte Kundenware. Kein Teil des oeffentlichen Webangebots: nicht verlinkt,
# nicht in der Sitemap, `noindex` (dl_noindex_audit.py). Die Impressumspflicht
# des § 5 DDG trifft das Angebot, nicht die ausgelieferte Ware.
EXEMPT_PREFIX = ("dl/",)

STUB_BYTES = 400


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def iter_html(root: str) -> list[str]:
    """Alle HTML-Dateien im Baum, rekursiv, als sortierte relative Pfade."""
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name.lower().endswith(".html"):
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                out.append(rel.replace("\\", "/"))
    return sorted(out)


def is_exempt(rel: str, text: str) -> tuple[bool, str]:
    """(ausgenommen, Begruendung). Jede Ausnahme muss benennbar sein."""
    base = os.path.basename(rel).lower()
    if base in REQUIRED:
        return True, "Rechtsseite selbst"
    if rel.startswith(EXEMPT_PREFIX):
        return True, "bezahlte Kundenware unter dl/ (noindex, kein Webangebot)"
    low = text.lower()
    if 'http-equiv="refresh"' in low or "http-equiv='refresh'" in low:
        return True, "Redirect-Seite"
    if len(text) < STUB_BYTES:
        return True, "Stub (<%d B)" % STUB_BYTES
    return False, ""


def missing_links(text: str) -> list[str]:
    return [r for r in REQUIRED if r not in text]


def tree_drift(root: str, walked: list[str]) -> tuple[str, list[str], list[str]]:
    """Deckungsabgleich der Ziel-Ableitung gegen den ausgelieferten git-Tree.

    Merkregel Ticket 18: eine Pruefzahl ist kein Deckungsbeweis. GitHub Pages
    liefert den gh-pages-Tree aus -- weicht die gelaufene Menge davon ab, ist
    die Pruefflaeche unvollstaendig und das Ergebnis nicht belastbar.

    Rueckgabe: ("ok" | "drift" | "unmessbar", nur_im_tree, nur_gelaufen)
    """
    try:
        res = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD", "--name-only"],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return "unmessbar: git nicht ausfuehrbar (%s)" % exc, [], []
    if res.returncode != 0:
        return "unmessbar: git rc=%d" % res.returncode, [], []
    tree = {p for p in res.stdout.split() if p.lower().endswith(".html")}
    if not tree:
        return "unmessbar: git-Tree enthaelt keine HTML-Dateien", [], []
    walked_set = set(walked)
    nur_tree = sorted(tree - walked_set)
    nur_walk = sorted(walked_set - tree)
    if nur_tree or nur_walk:
        return "drift", nur_tree, nur_walk
    return "ok", [], []
