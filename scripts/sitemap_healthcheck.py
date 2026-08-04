#!/usr/bin/env python3
"""Sitemap-Healthcheck: prueft JEDE <loc>-URL der LIVE-Sitemap auf echten HTTP-Status.

Hintergrund (MEASURED 2026-08-04): IndexNow hat 1207 URLs eingereicht. "Eingereicht"
sagt nichts darueber aus, ob die URLs live erreichbar sind. Eine Sitemap mit 404ern
verbrennt Crawl-Budget und Vertrauen bei Bing/Google.

Nutzung:
    python scripts/sitemap_healthcheck.py [--limit N] [--sitemap URL]

Exit-Code 0 = alle URLs 200. 1 = mindestens eine URL != 200.
Ausgabe ist MEASURED: echte Statuscodes, keine Annahmen.
"""
import argparse
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

DEFAULT_SITEMAP = "https://translucentv1.github.io/new-business/sitemap.xml"
UA = "Mozilla/5.0 (compatible; sitemap-healthcheck/1.0)"


def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def status(url: str, timeout: int = 20):
    """GET (nicht HEAD: GitHub Pages antwortet auf HEAD teils abweichend)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return url, r.status, len(body)
    except urllib.error.HTTPError as e:
        return url, e.code, 0
    except Exception as e:  # Netzfehler etc. - ehrlich als -1 markieren
        return url, -1, 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", default=DEFAULT_SITEMAP)
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N URLs pruefen (0=alle)")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    xml = fetch(args.sitemap)
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    if args.limit:
        urls = urls[: args.limit]
    print(f"sitemap={args.sitemap}")
    print(f"urls_gefunden={len(urls)}")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, res in enumerate(ex.map(status, urls), 1):
            results.append(res)
            if i % 200 == 0:
                print(f"  ... {i}/{len(urls)} geprueft", flush=True)

    ok = [r for r in results if r[1] == 200]
    bad = [r for r in results if r[1] != 200]
    empty = [r for r in ok if r[2] < 500]

    print(f"HTTP_200={len(ok)}  NICHT_200={len(bad)}  VERDAECHTIG_KLEIN(<500B)={len(empty)}")
    for url, code, size in bad[:40]:
        print(f"  DEFEKT {code}  {url}")
    if len(bad) > 40:
        print(f"  ... und {len(bad)-40} weitere")
    for url, code, size in empty[:20]:
        print(f"  DUENN  {size}B  {url}")

    print("ERGEBNIS: SITEMAP_OK" if not bad else "ERGEBNIS: SITEMAP_DEFEKT")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
