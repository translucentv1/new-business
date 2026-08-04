#!/usr/bin/env python3
"""IndexNow-Submission fuer die statische GitHub-Pages-Site (Bing/Yandex/Seznam).

Warum: Google /ping ist tot (404) und Search Console braucht Login. IndexNow ist
der EINZIGE autonome, kostenlose, ToS-konforme Indexierungs-Hebel ohne Login.

WICHTIG (Scope-Regel der IndexNow-Spezifikation):
  Liegt die Key-Datei unter https://host/pfad/<key>.txt, duerfen NUR URLs unter
  /pfad/ eingereicht werden. Unsere Site liegt unter /new-business/, die
  Key-Datei im gh-pages-ROOT -> live unter /new-business/<key>.txt.
  Damit ist genau unser URL-Raum autorisiert.

Belegpflicht: das Skript druckt den echten HTTP-Status.
  200/202 = angenommen.
  403     = Bing hat die Key-Datei noch NICHT gecrawlt (kein URL-Fehler!)
            -> spaeter erneut einreichen.
  422     = URL-Scope/Key passt nicht zur Key-Datei.

Nutzung:
  python scripts/indexnow_submit.py            # alle Sitemap-URLs
  python scripts/indexnow_submit.py --limit 10 # kleiner Erst-Submit
  python scripts/indexnow_submit.py --check    # nur Key-Datei live pruefen
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HOST = "translucentv1.github.io"
BASE = "https://translucentv1.github.io/new-business/"
KEY = "49bf6b5c07acd9038ee05981c1810baa"
KEY_URL = BASE + KEY + ".txt"
SITEMAP = os.path.join(ROOT, "sitemap.xml")
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000  # Spec-Limit pro Request


def http(url, data=None, headers=None, timeout=60):
    """Liefert (status, body) auch bei HTTP-Fehlercodes (kein Raise)."""
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:  # Netzwerk/DNS
        return 0, repr(e)


def check_key_live():
    status, body = http(KEY_URL)
    ok = status == 200 and body.strip() == KEY
    print("[key] %s -> HTTP %s body=%r ok=%s" % (KEY_URL, status, body[:60], ok))
    return ok


def sitemap_urls():
    if not os.path.exists(SITEMAP):
        print("[sitemap] FEHLT: %s" % SITEMAP)
        return []
    with open(SITEMAP, "r", encoding="utf-8") as f:
        raw = f.read()
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", raw)
    # Nur autorisierter Scope (Key-Datei liegt unter /new-business/)
    scoped = [u for u in urls if u.startswith(BASE)]
    # /dl/ ist per robots.txt disallow (ADR-0013) -> nicht einreichen
    scoped = [u for u in scoped if "/dl/" not in u]
    dropped = len(urls) - len(scoped)
    print("[sitemap] %d URLs gelesen, %d im Scope (%d verworfen)"
          % (len(urls), len(scoped), dropped))
    return scoped


def submit(urls):
    payload = {"host": HOST, "key": KEY, "keyLocation": KEY_URL, "urlList": urls}
    body = json.dumps(payload).encode("utf-8")
    status, resp = http(ENDPOINT, data=body,
                        headers={"Content-Type": "application/json; charset=utf-8"})
    print("[submit] %d URLs -> HTTP %s %s" % (len(urls), status, resp.strip()[:200]))
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N URLs")
    ap.add_argument("--check", action="store_true", help="nur Key-Datei pruefen")
    args = ap.parse_args()

    key_ok = check_key_live()
    if args.check:
        return 0 if key_ok else 1
    if not key_ok:
        print("ERGEBNIS: KEY_NICHT_LIVE - erst pushen/warten, dann erneut einreichen.")
        return 1

    urls = sitemap_urls()
    if not urls:
        print("ERGEBNIS: KEINE_URLS")
        return 1
    if args.limit:
        urls = urls[:args.limit]

    codes = []
    for i in range(0, len(urls), BATCH):
        codes.append(submit(urls[i:i + BATCH]))

    if all(c in (200, 202) for c in codes):
        print("ERGEBNIS: SUBMIT_OK codes=%s" % codes)
        return 0
    if 403 in codes:
        print("ERGEBNIS: SUBMIT_403_KEY_NOCH_NICHT_GECRAWLT (kein URL-Fehler) "
              "codes=%s" % codes)
        return 2
    print("ERGEBNIS: SUBMIT_FEHLER codes=%s" % codes)
    return 1


if __name__ == "__main__":
    sys.exit(main())
