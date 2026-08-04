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


def _selftest() -> int:
    """Fault Injection: beweist, dass dieser Pruefer ueberhaupt ROT werden kann.

    Hintergrund (Repo-Konvention "Pruefer pruefen"): ein Verifikationsskript ohne
    Negativ-Test winkt einen kaputten Zustand durch, und sein "0 Defekte" ist dann
    ein ASSUMED-Claim. Zusaetzlich die Exit-Code-Falle beachten: rc=1 allein beweist
    nicht, dass ein Defekt *erkannt* wurde - es kann ein Absturz sein. Darum wird bei
    jedem Rot-Fall die erwartete Meldung geprueft UND auf 'Traceback' gefiltert.
    """
    import io
    import contextlib

    base = DEFAULT_SITEMAP.rsplit("/", 1)[0]
    url_ok = f"{base}/rtd.html"
    url_404 = f"{base}/__healthcheck_selftest_gibt_es_nicht__.html"

    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    def run_main(sitemap_urls, fake_status=None):
        """Faehrt die ECHTE main() mit injizierter Sitemap (und optional Status)."""
        xml = "<urlset>" + "".join(f"<loc>{u}</loc>" for u in sitemap_urls) + "</urlset>"
        real_fetch, real_status = globals()["fetch"], globals()["status"]
        globals()["fetch"] = lambda url, timeout=20: xml
        if fake_status:
            globals()["status"] = fake_status
        buf = io.StringIO()
        argv = sys.argv
        sys.argv = ["sitemap_healthcheck.py"]
        try:
            with contextlib.redirect_stdout(buf):
                rc = main()
        finally:
            sys.argv = argv
            globals()["fetch"] = real_fetch
            globals()["status"] = real_status
        return rc, buf.getvalue()

    # 1+2: status() gegen echtes HTTP - erkennt es 200 und 404 auseinander?
    _, code_ok, size_ok = status(url_ok)
    check("status() liefert 200 fuer eine existierende Seite", code_ok == 200, f"code={code_ok}")
    _, code_bad, _ = status(url_404)
    check("status() liefert 404 fuer eine fehlende Seite", code_bad == 404, f"code={code_bad}")

    # 3: die 404-Seite von GitHub Pages hat einen FETTEN Body (MEASURED 9379 B).
    #    Eine Groessen-Heuristik wuerde sie fuer eine gesunde Seite halten -> genau
    #    darum wird der Statuscode geprueft und nicht die Byte-Zahl.
    check(
        "404 wird NICHT ueber die Body-Groesse erkannt (Statuscode ist das Kriterium)",
        code_bad == 404 and size_ok > 0,
        f"200-body={size_ok}B",
    )

    # 4: ROT-Fall - eine kaputte URL in der Sitemap muss rc=1 + DEFEKT erzeugen
    rc, out = run_main([url_ok, url_404])
    check("Fault Injection: 404 in der Sitemap -> rc=1", rc == 1, f"rc={rc}")
    check("Fault Injection: meldet 'DEFEKT 404'", "DEFEKT 404" in out)
    check("Fault Injection: meldet SITEMAP_DEFEKT", "SITEMAP_DEFEKT" in out)
    check("Rot-Fall ist kein Absturz (kein Traceback)", "Traceback" not in out)

    # 5: GRUEN-Fall - rc muss von 1 auf 0 wechseln, sonst ist rc bedeutungslos
    rc_ok, out_ok = run_main([url_ok])
    check("Gesunde Sitemap -> rc=0 (rc-Wechsel 1->0 belegt)", rc_ok == 0, f"rc={rc_ok}")
    check("Gruen-Fall meldet SITEMAP_OK", "SITEMAP_OK" in out_ok)
    check("Gruen-Fall ist kein Absturz (kein Traceback)", "Traceback" not in out_ok)

    # 6: DUENN-Zweig - 200 mit Mini-Body muss auffallen
    thin = lambda u, timeout=20: (u, 200, 12)
    rc_thin, out_thin = run_main([url_ok], fake_status=thin)
    check("Duenne Seite (12 B) wird als DUENN gemeldet", "DUENN" in out_thin)
    check("Duenne Seite allein macht NICHT rot (nur Hinweis)", rc_thin == 0, f"rc={rc_thin}")

    # 7: Netzfehler darf nicht still durchgewunken werden
    boom = lambda u, timeout=20: (u, -1, 0)
    rc_net, out_net = run_main([url_ok], fake_status=boom)
    check("Netzfehler (-1) zaehlt als NICHT_200 -> rc=1", rc_net == 1, f"rc={rc_net}")

    passed = sum(1 for _, ok, _ in results if ok)
    print("== sitemap_healthcheck --selftest (Fault Injection) ==")
    for name, ok, detail in results:
        print(f"  [{'OK ' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    print(f"ERGEBNIS: {passed}/{len(results)} " + ("SELFTEST_OK" if passed == len(results) else "SELFTEST_FAIL"))
    return 0 if passed == len(results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sitemap", default=DEFAULT_SITEMAP)
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N URLs pruefen (0=alle)")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--selftest", action="store_true", help="Fault Injection: kann dieser Pruefer rot werden?")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

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
