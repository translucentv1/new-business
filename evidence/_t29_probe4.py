"""Ad-hoc-Sonde (Ticket 29), Teil 4: Gegenrichtung LIVE.

Der Deindex-Eingriff hat 468 Seiten auf `noindex` gesetzt. Teil 3 hat den
lokalen Baum gegengeprueft; hier wird der AUSGELIEFERTE Body der Geldseiten
gemessen - eine versehentlich mit-deindexierte Kaufseite waere der teuerste
denkbare Kollateralschaden und im Statuscode unsichtbar (Merkregel Ticket 20:
Statuscode != Inhalt).
"""
import re
import sys
import urllib.error
import urllib.request

BASE = "https://translucentv1.github.io/new-business/"
GELDSEITEN = ["", "rtd.html", "gig.html", "lead_magnet.html", "ki-text-service/",
              "agb.html", "datenschutz.html", "impressum.html"]
ERWARTET_NOINDEX = {"thanks.html"}
NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']', re.I)

defekt, unmessbar = [], []
for rel in GELDSEITEN + sorted(ERWARTET_NOINDEX):
    try:
        with urllib.request.urlopen(BASE + rel, timeout=25) as r:
            code, body = r.getcode(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code, body = e.code, ""
    except Exception as e:
        print(f"  {rel or '(root)':<24} UNMESSBAR {e}")
        unmessbar.append(rel)
        continue
    m = NOINDEX_RE.search(body)
    robots = m.group(1).strip().lower() if m else "(kein meta robots)"
    soll_noindex = rel in ERWARTET_NOINDEX
    ist_noindex = "noindex" in robots
    ok = (code == 200) and (ist_noindex == soll_noindex)
    print(f"  {rel or '(root)':<24} HTTP {code}  robots={robots:<24} {'OK' if ok else 'DEFEKT'}")
    if not ok:
        defekt.append(rel)

if defekt:
    print("ERGEBNIS: GELDSEITEN_INDEXIERBARKEIT_DEFEKT", defekt)
    sys.exit(1)
if unmessbar:
    print("ERGEBNIS: GELDSEITEN_INDEXIERBARKEIT_UNGEPRUEFT", unmessbar)
    sys.exit(2)
print(f"ERGEBNIS: GELDSEITEN_INDEXIERBAR_OK ({len(GELDSEITEN)} Seiten live ohne noindex, "
      f"{len(ERWARTET_NOINDEX)} bewusst mit)")
