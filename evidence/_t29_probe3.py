"""Ad-hoc-Sonde (Ticket 29), Teil 3: Wirkt der Deindex-Eingriff LIVE?

Der Fremdlauf (Commit 6dd6238) behauptet, 468 Doorway-Seiten unter t/ trügen
jetzt `noindex,follow`. Belegt war das nur im lokalen Baum ("verify 77 ok").
Merkregel der Map: "gebaut" ist nie "live", und Statuscode != Inhalt.
Hier wird der AUSGELIEFERTE BODY jeder einzelnen t/-Seite gemessen (vollzaehlig,
keine Stichprobe), plus die Gegenrichtung: traegt versehentlich eine
Nicht-Doorway-Seite ein noindex?

Selbstbefund 2026-08-10: die erste Fassung globbte `t/*.html` und fand 1 statt
468 Seiten (die Doorways liegen als t/<produkt>/<slug>/index.html). Zielmenge
wird jetzt REKURSIV aus dem Baum abgeleitet; eine Zielmenge, die deutlich
kleiner ist als der Claim (468), ist NICHT gruen.
"""
import concurrent.futures as cf
import glob
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://translucentv1.github.io/new-business/"
DOORWAY_DIR = "t"
ERWARTET_MIN = 400  # Claim des Fremdlaufs: 468
# thanks.html traegt bewusst noindex (Seite nach dem Checkout, kein Suchziel).
NOINDEX_ERLAUBT = {"thanks.html"}
NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']', re.I)


def robots_of(text):
    m = NOINDEX_RE.search(text)
    return m.group(1).strip().lower() if m else None


def read(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rel_url(path):
    return path.replace(os.sep, "/")


def fetch(rel):
    """5xx/429 sind Ratelimit/Serverlaunen, kein Defekt der Seite -> einmal
    nachfassen, dann als unmessbar melden (Konvention: unmessbar != Defekt).
    """
    url = BASE + rel
    letzte = None
    for versuch in range(2):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return rel, r.getcode(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 or 500 <= e.code < 600:
                letzte = ("transient", e.code)
                time.sleep(3 + 5 * versuch)
                continue
            return rel, e.code, ""
        except Exception as e:  # Netzfehler -> unmessbar, nicht Defekt
            letzte = ("net", str(e))
            time.sleep(3 + 5 * versuch)
    return rel, -1, f"unmessbar {letzte}"


def main():
    doorways = sorted(glob.glob(os.path.join(DOORWAY_DIR, "**", "*.html"), recursive=True))
    print(f"[1] lokale Doorway-Seiten unter {DOORWAY_DIR}/ (rekursiv): {len(doorways)}")
    if len(doorways) < ERWARTET_MIN:
        print(f"    Zielmenge kleiner als der Claim ({ERWARTET_MIN}+) -> Ableitung verdaechtig")
        print("ERGEBNIS: DEINDEX_UNGEPRUEFT (Zielmenge unplausibel klein)")
        return 2

    if "--rotprobe" in sys.argv:
        # Fault Injection: index.html ist live HTTP 200 und traegt bewusst KEIN
        # noindex. Wird sie in die Zielmenge geschmuggelt, MUSS die Sonde rot
        # werden - sonst ist ihr Gruen wertlos.
        doorways = doorways[:3] + ["index.html"]
        print(f"    [ROTPROBE] Zielmenge kuenstlich auf {len(doorways)} gesetzt, "
              "index.html eingeschmuggelt (erwartet: DEINDEX_DEFEKT)")

    lokal_ohne = [p for p in doorways if "noindex" not in (robots_of(read(p)) or "")]
    print(f"    lokal OHNE noindex: {len(lokal_ohne)}")
    for p in lokal_ohne[:10]:
        print("      !", p)

    andere = glob.glob("*.html") + glob.glob("blog/*.html") + glob.glob("seo/*.html")
    falsch_noindex = []
    for p in andere:
        r = robots_of(read(p)) or ""
        if "noindex" in r and rel_url(p) not in NOINDEX_ERLAUBT:
            falsch_noindex.append((p, r))
    print(f"[2] Nicht-Doorway-Seiten mit unerwartetem noindex: {len(falsch_noindex)}"
          f" (geprueft: {len(andere)}, erlaubt: {sorted(NOINDEX_ERLAUBT)})")
    for p, r in falsch_noindex:
        print(f"      ! {p}  robots={r}")

    print(f"[3] LIVE-Auslieferung aller {len(doorways)} Doorway-Seiten ...")
    live_kein_noindex, nicht_200, unmessbar = [], [], []
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for rel, code, body in ex.map(fetch, [rel_url(p) for p in doorways]):
            if code == -1:
                unmessbar.append(rel)
            elif code != 200:
                nicht_200.append((rel, code))
            elif "Page not found" in body[:4000]:
                nicht_200.append((rel, "soft404"))
            elif "noindex" not in (robots_of(body) or ""):
                live_kein_noindex.append(rel)
    print(f"    live ohne noindex: {len(live_kein_noindex)}  nicht_200: {len(nicht_200)}"
          f"  unmessbar: {len(unmessbar)}")
    for rel in live_kein_noindex[:10]:
        print("      ! LIVE ohne noindex:", rel)
    for rel, c in nicht_200[:10]:
        print("      ! LIVE Status:", rel, c)

    if lokal_ohne or live_kein_noindex or nicht_200 or falsch_noindex:
        print("ERGEBNIS: DEINDEX_DEFEKT")
        return 1
    if unmessbar:
        print(f"ERGEBNIS: DEINDEX_UNGEPRUEFT ({len(unmessbar)} Seiten nicht abrufbar)")
        return 2
    print(f"ERGEBNIS: DEINDEX_LIVE_OK ({len(doorways)} Seiten vollzaehlig live geprueft)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
