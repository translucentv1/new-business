#!/usr/bin/env python3
"""Ticket 5 - Ist die Site in einem Bing-gespeisten Index angekommen?

WARUM DIESES SKRIPT UEBERHAUPT EXISTIERT
----------------------------------------
Ticket 5 schrieb vor: "Bing-Suche abfragen und Treffer zaehlen. 0 Treffer =
noch nicht indexiert." Genau so darf es NICHT gemacht werden. Gemessen am
2026-08-07:

  bing.com/search (curl)   site:wikipedia.org -> 0 parsebare Treffer
  bing.com/search (Browser) site:wikipedia.org -> 0 Treffer im DOM
  bing.com/search?format=rss site:wikipedia.org -> 10 Items, alle amazon.fr

Alle drei Wege liefern HTTP 200 und sehen nach einer Messung aus. Eine
POSITIVKONTROLLE gegen eine zweifelsfrei indexierte Domain zeigt, dass sie
NICHTS sehen koennen. Ohne diese Kontrolle haette der Tick "0 Treffer" notiert
und daraus laut Ticket-Entscheidungsregel "IndexNow abschreiben" gefolgert -
eine Strategieentscheidung auf Basis eines blinden Instruments.

REGEL DIESES SKRIPTS: Jede Quelle wird zuerst gegen die Kontrolle gefahren.
Sieht die Kontrolle nichts, ist die Quelle BLIND und ihre Aussage ueber die
eigene Domain wird VERWORFEN - nicht als "nicht indexiert" gelesen.

GELTUNGSBEREICH (ehrlich): gemessen wird der DuckDuckGo-Index. Laut DDGs
eigener Hilfeseite (primaer abgerufen, HTTP 200) stammen die klassischen
Weblinks "largely from Bing" - ein starker, aber kein deckungsgleicher Proxy
fuer Bings Index. "largely" ist nicht "ausschliesslich".

ERGEBNISWOERTER
  BING_INDEXIERT       rc=0  Treffer auf der eigenen Domain gefunden
  BING_NICHT_INDEXIERT rc=1  gemessene Null mit nachweislich zaehlfaehigem Instrument
  BING_UNGEPRUEFT      rc=2  keine brauchbare Quelle - KEINE Aussage
"""
import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

TARGET_QUERY = "site:translucentv1.github.io/new-business"
TARGET_HOST = "translucentv1.github.io"
CONTROL_QUERY = "site:wikipedia.org"
CONTROL_HOST = "wikipedia.org"

OK, NICHT, UNGEPRUEFT = "BING_INDEXIERT", "BING_NICHT_INDEXIERT", "BING_UNGEPRUEFT"


# ---------------------------------------------------------------- Netzschicht
def real_fetch(url):
    """Vertrag: liefert (status:int, body:str). Wirft nie. -1 = Netzfehler."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            return e.code, ""
    except Exception as e:  # noqa: BLE001
        return -1, repr(e)


# ------------------------------------------------------------------- Parser
def ddg_url(q):
    return "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)


def ddg_parse(status, body, host):
    """-> (treffer:int|None, marker:str). None = nicht auswertbar (blind)."""
    if status == -1:
        return None, "netzfehler"
    if status == 202 or "anomaly" in body.lower():
        return None, "ratelimit/anomaly (HTTP %s)" % status
    if status != 200:
        return None, "HTTP %s" % status
    explicit_empty = ("No results found for" in body
                      or "result--no-result" in body)
    targets = [urllib.parse.unquote(u) for u in re.findall(r"uddg=([^&\"']+)", body)]
    hits = sorted({u for u in targets if host in u})
    if not hits and not explicit_empty:
        # Weder Treffer noch ausdrueckliche Leermeldung -> Seite unverstanden.
        return None, "kein Ergebnisblock und keine Leermeldung"
    return len(hits), ("explizite Leermeldung" if explicit_empty
                       else "%d Ergebnis-URLs" % len(hits))


def bing_url(q):
    return "https://www.bing.com/search?q=" + urllib.parse.quote(q) + "&count=50"


def bing_parse(status, body, host):
    if status == -1:
        return None, "netzfehler"
    if status != 200:
        return None, "HTTP %s" % status
    algo = len(re.findall(r'class="b_algo"', body))
    cites = re.findall(r"<cite[^>]*>([^<]*)</cite>", body)
    hits = sorted({c for c in cites if host in c})
    if algo == 0 and not hits:
        # Bing liefert von hier aus eine JS-Huelle ohne Ergebnisliste.
        return None, "keine Ergebnisliste im HTML (b_algo=0, cite=0)"
    return len(hits), "%d cite-Treffer (b_algo=%d)" % (len(hits), algo)


SOURCES = [
    ("ddg_html", ddg_url, ddg_parse),
    ("bing_html", bing_url, bing_parse),
]


# --------------------------------------------------------------------- Kern
def main(argv=None, fetch=real_fetch, sources=None, sleep=time.sleep):
    argv = [] if argv is None else argv
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--retries", type=int, default=1,
                    help="Wiederholungen, wenn die Quelle ratelimitet (Default 1)")
    ap.add_argument("--wait", type=int, default=90,
                    help="Sekunden Abkuehlung vor einer Wiederholung (Default 90)")
    args, _ = ap.parse_known_args(argv)
    src = SOURCES if sources is None else sources

    out = []

    def say(s=""):
        out.append(s)
        if not args.quiet:
            print(s)

    def probe(url_of, parse, query, host):
        """Holt und wertet aus; wiederholt NUR bei Ratelimit, nie bei einer Null."""
        for attempt in range(max(1, args.retries + 1)):
            st, body = fetch(url_of(query))
            n, why = parse(st, body, host)
            if not (n is None and "ratelimit" in why):
                return n, why
            if attempt < args.retries:
                say("    ratelimit (%s) - Abkuehlung %ds, Versuch %d/%d"
                    % (why, args.wait, attempt + 2, args.retries + 1))
                sleep(args.wait)
        return n, why

    say("== Bing-Indexierung (Ticket 5) ==")
    say("Ziel     : %s" % TARGET_QUERY)
    say("Kontrolle: %s  (zweifelsfrei indexiert)" % CONTROL_QUERY)
    say("Geltungsbereich: DDG-Index; Weblinks laut DDG 'largely from Bing' -> Proxy, "
        "nicht deckungsgleich mit Bing.")
    say()

    if not src:
        say("! keine Quelle konfiguriert - leere Zielmenge ist NICHT gruen")
        say("ERGEBNIS: %s (0 Quellen)" % UNGEPRUEFT)
        return 2, "\n".join(out)

    usable = []          # (name, treffer_ziel, notiz)
    for name, url_of, parse in src:
        n_c, why_c = probe(url_of, parse, CONTROL_QUERY, CONTROL_HOST)
        if n_c is None or n_c == 0:
            say("[%s] KONTROLLE sieht nichts (%s) -> BLIND, Quelle verworfen"
                % (name, why_c if n_c is None else "0 Treffer trotz auswertbarer Seite"))
            continue
        say("[%s] Kontrolle OK: %d Treffer auf %s (%s)" % (name, n_c, CONTROL_HOST, why_c))
        sleep(2)
        n_t, why_t = probe(url_of, parse, TARGET_QUERY, TARGET_HOST)
        if n_t is None:
            say("[%s] Ziel nicht auswertbar (%s) -> Quelle verworfen" % (name, why_t))
            continue
        say("[%s] ZIEL: %d Treffer auf %s (%s)" % (name, n_t, TARGET_HOST, why_t))
        usable.append((name, n_t, why_t))
        sleep(2)

    say()
    if not usable:
        say("Keine Quelle hat ihre Positivkontrolle bestanden.")
        say("Das heisst NICHT 'nicht indexiert' - es heisst 'von hier aus nicht messbar'.")
        say("ERGEBNIS: %s" % UNGEPRUEFT)
        return 2, "\n".join(out)

    total = sum(n for _, n, _ in usable)
    say("brauchbare Quellen: %d (%s)" % (len(usable), ", ".join(n for n, _, _ in usable)))
    if total > 0:
        say("ERGEBNIS: %s (%d Treffer)" % (OK, total))
        return 0, "\n".join(out)
    say("Instrument nachweislich zaehlfaehig (Kontrolle > 0), Ziel bleibt 0.")
    say("ERGEBNIS: %s" % NICHT)
    return 1, "\n".join(out)


# ----------------------------------------------------------------- Selftest
def _fake(pages):
    """Attrappe mit demselben Vertrag wie real_fetch: (status, body), wirft nie."""
    def f(url):
        for frag, resp in pages:
            if frag in url:
                return resp
        return 200, "<html></html>"
    return f


def _ddg_body(urls, empty_for=None):
    if empty_for:
        return ('<div class="no-results__container result__title">'
                "<h1>No results found for <strong>%s</strong></h1></div>" % empty_for)
    parts = ['<div class="results">']
    for u in urls:
        parts.append('<a class="result__a" href="//duckduckgo.com/l/?uddg=%s">x</a>'
                     % urllib.parse.quote(u, safe=""))
    parts.append("</div>")
    return "".join(parts)


def selftest():
    res = []

    def t(cond, label):
        res.append((bool(cond), label))
        print("  %s %s" % ("ok  " if cond else "FAIL", label))

    def run(pages, sources=None):
        rc, out = main(["--quiet"], fetch=_fake(pages), sources=sources, sleep=lambda _s: None)
        return rc, out

    def word(out):
        for line in out.splitlines():
            if line.startswith("ERGEBNIS:"):
                return line.split()[1]
        return "(kein Ergebniswort)"

    ddg_only = [("ddg_html", ddg_url, ddg_parse)]
    ctrl_ok = _ddg_body(["https://en.wikipedia.org/wiki/A", "https://de.wikipedia.org/wiki/B"])

    print("== selftest bing_index_check ==")

    # 1 gruen: Kontrolle sieht, Ziel hat Treffer
    rc, out = run([("wikipedia.org", (200, ctrl_ok)),
                   ("translucentv1", (200, _ddg_body(
                       ["https://translucentv1.github.io/new-business/rtd.html"])))], ddg_only)
    t(rc == 0, "Treffer -> rc=0")
    t(word(out) == OK, "Treffer -> Ergebniswort exakt %s" % OK)

    # 2 rot: Kontrolle sieht, Ziel ausdruecklich leer
    rc, out = run([("wikipedia.org", (200, ctrl_ok)),
                   ("translucentv1", (200, _ddg_body([], empty_for=TARGET_QUERY)))], ddg_only)
    t(rc == 1, "gemessene Null -> rc=1")
    t(word(out) == NICHT, "gemessene Null -> Ergebniswort exakt %s" % NICHT)

    # 3 DER Kernfall: Kontrolle blind -> niemals 'nicht indexiert'
    rc, out = run([("wikipedia.org", (200, _ddg_body([], empty_for=CONTROL_QUERY))),
                   ("translucentv1", (200, _ddg_body([], empty_for=TARGET_QUERY)))], ddg_only)
    t(rc == 2, "blinde Kontrolle -> rc=2 (nicht 1!)")
    t(word(out) == UNGEPRUEFT, "blinde Kontrolle -> Ergebniswort exakt %s" % UNGEPRUEFT)
    t("BLIND, Quelle verworfen" in out, "blinde Kontrolle -> exakte Diagnosezeile")

    # 4 RSS-Falle: Kontrolle liefert Ergebnisse, aber auf fremdem Host
    rc, out = run([("wikipedia.org", (200, _ddg_body(["https://www.amazon.fr/"] * 10))),
                   ("translucentv1", (200, _ddg_body(["https://www.amazon.fr/"] * 10)))], ddg_only)
    t(rc == 2, "Kontrolle liefert Fremdhost-Treffer -> rc=2")

    # 5 Ratelimit 202
    rc, out = run([("wikipedia.org", (202, "<html>anomaly detected</html>")),
                   ("translucentv1", (202, "<html>anomaly detected</html>"))], ddg_only)
    t(rc == 2, "HTTP 202/anomaly -> rc=2")
    t("ratelimit/anomaly" in out, "HTTP 202 -> exakte Diagnose 'ratelimit/anomaly'")

    # 6 Netzfehler
    rc, out = run([("wikipedia.org", (-1, "URLError")), ("translucentv1", (-1, "URLError"))],
                  ddg_only)
    t(rc == 2, "Netzfehler -> rc=2")

    # 7 leere Quellenliste ist NICHT gruen
    rc, out = run([], sources=[])
    t(rc == 2, "0 Quellen -> rc=2 (leere Zielmenge nicht gruen)")
    t("leere Zielmenge ist NICHT gruen" in out, "0 Quellen -> exakte Diagnosezeile")

    # 8 Kontrolle gut, Ziel unverstanden (weder Treffer noch Leermeldung)
    rc, out = run([("wikipedia.org", (200, ctrl_ok)),
                   ("translucentv1", (200, "<html>irgendwas</html>"))], ddg_only)
    t(rc == 2, "Ziel unverstanden -> rc=2, kein Null-Claim")

    # 9 eine blinde + eine sehende Quelle: die sehende entscheidet
    both = [("blind", ddg_url, lambda s, b, h: (None, "immer blind")),
            ("ddg_html", ddg_url, ddg_parse)]
    rc, out = run([("wikipedia.org", (200, ctrl_ok)),
                   ("translucentv1", (200, _ddg_body([], empty_for=TARGET_QUERY)))], both)
    t(rc == 1, "blinde Quelle blockiert die sehende nicht -> rc=1")

    # 10 bing_parse: JS-Huelle ohne Ergebnisliste ist blind, nicht null
    n, why = bing_parse(200, "<html><body>nur navigation</body></html>", CONTROL_HOST)
    t(n is None, "bing_parse: JS-Huelle -> None (blind), nicht 0")
    n2, _ = bing_parse(200, '<li class="b_algo"><cite>https://wikipedia.org/x</cite></li>',
                       CONTROL_HOST)
    t(n2 == 1, "bing_parse: echte Ergebnisliste -> zaehlt")

    # 11 Retry: erster Versuch ratelimitet, zweiter liefert -> Quelle brauchbar
    calls = {"n": 0}

    def flaky(url):
        calls["n"] += 1
        if calls["n"] == 1:
            return 202, "<html>anomaly detected</html>"
        if "wikipedia.org" in url:
            return 200, ctrl_ok
        return 200, _ddg_body([], empty_for=TARGET_QUERY)

    rc, out = main(["--quiet", "--retries", "2"], fetch=flaky, sources=ddg_only,
                   sleep=lambda _s: None)
    t(rc == 1, "Retry nach Ratelimit -> Quelle wird doch brauchbar (rc=1)")
    t(word(out) == NICHT, "Retry -> Ergebniswort exakt %s" % NICHT)

    # 12 Retry feuert NICHT bei einer echten Null (sonst Messung verschleppt)
    calls2 = {"n": 0}

    def counting(url):
        calls2["n"] += 1
        if "wikipedia.org" in url:
            return 200, ctrl_ok
        return 200, _ddg_body([], empty_for=TARGET_QUERY)

    rc, out = main(["--quiet", "--retries", "3"], fetch=counting, sources=ddg_only,
                   sleep=lambda _s: None)
    t(calls2["n"] == 2, "echte Null wird nicht wiederholt (genau 2 Abrufe, war %d)"
      % calls2["n"])

    # 13 kein Traceback in irgendeinem Lauf
    t("Traceback (most recent call last)" not in out, "kein Traceback im Output")

    okc = sum(1 for c, _ in res if c)
    print("\n%d/%d %s" % (okc, len(res), "SELFTEST_OK" if okc == len(res) else "SELFTEST_FAIL"))
    return 0 if okc == len(res) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    rc_, _out = main(sys.argv[1:])
    sys.exit(rc_)
