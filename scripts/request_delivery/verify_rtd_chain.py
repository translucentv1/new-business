#!/usr/bin/env python3
"""Ketten-Integritaet fuer RTD (Request-to-Delivery) MEASURED pruefen.

Liest die geminteten LIVE-Payment-Links aus rtd.html, fragt Stripe live ab
(active/livemode/Preis/anfrage-Feld/Redirect) und misst, ob der JS-Hash in
thanks.html denselben Deliverable-Pfad erzeugt wie der Python-Hash in
auto_fulfill.py.

Read-only gegen Stripe: erstellt KEINE Links, bucht NICHTS, aendert NICHTS.

Nutzung:
  python verify_rtd_chain.py              # echter Lauf gegen LIVE-Stripe
  python verify_rtd_chain.py --selftest   # Fault Injection (Ticket 16)

Ergebnisworte / Exit-Codes:
  KETTE_OK          rc=0  alles gemessen und gruen
  KETTE_PROBLEM     rc=1  ein Defekt auf dem Geldpfad
  KETTE_UNGEPRUEFT  rc=2  eine Etappe war nicht messbar (z.B. node fehlt)
                          -> ausdruecklich NICHT gruen, aber auch kein Defekt-Claim
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import app  # get_stripe_key

RTD = os.path.join(ROOT, "rtd.html")
THANKS = os.path.join(ROOT, "thanks.html")
DL_DIR = os.path.join(ROOT, "dl", "rtd")


def sid_hash(sid: str) -> str:
    return hashlib.sha256(sid.encode()).hexdigest()[:16]


def fmt_preis(amt, cur="eur") -> str:
    """Stripe liefert unit_amount in der KLEINSTEN Waehrungseinheit (Cent).

    Frueher wurde "amount=399 eur" in Handoffs als "399 EUR" gelesen -> 100x-
    Fehler in der Doku. Deshalb IMMER beide Einheiten ausgeben.
    """
    if not isinstance(amt, int) or isinstance(amt, bool):
        return f"amount={amt} (kein Preis gelesen)"
    return f"{amt} cent = {amt / 100:.2f} {(cur or 'eur').upper()}"


# --------------------------------------------------------------------------
# Aussenwelt — genau diese vier Funktionen ersetzt der --selftest.
# Alles darunter ist Produktivlogik und wird im Selftest ECHT durchlaufen.
# --------------------------------------------------------------------------
def get_key():
    return app.get_stripe_key()


def stripe_get(path, key):
    req = urllib.request.Request(
        "https://api.stripe.com/v1/" + path,
        headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def run_node(script_src, arg):
    """Fuehrt JS aus. Rueckgabe (verfuegbar, stdout, fehler)."""
    exe = shutil.which("node")
    if not exe:
        return False, "", "node nicht gefunden"
    fd, p = tempfile.mkstemp(suffix=".mjs")
    os.close(fd)
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(script_src)
        r = subprocess.run([exe, p, arg], capture_output=True, text=True,
                           timeout=60, check=False)
        if r.returncode != 0:
            return True, r.stdout.strip(), (r.stderr.strip() or f"rc={r.returncode}")
        return True, r.stdout.strip(), None
    except (OSError, subprocess.SubprocessError) as e:  # Umgebungsfehler
        return False, "", f"{type(e).__name__}: {e}"
    finally:
        try:
            os.unlink(p)
        except OSError:
            pass


def count_deliverables():
    if not os.path.isdir(DL_DIR):
        return None
    return len([f for f in os.listdir(DL_DIR) if f.endswith(".html")])


# --------------------------------------------------------------------------
# Produktivlogik
# --------------------------------------------------------------------------
def list_payment_links(key):
    """Alle Payment Links, mit Pagination.

    Ohne has_more-Auswertung waere ein Link ab Nr. 101 unsichtbar -> das
    Skript haette 'NICHT gefunden' gemeldet (Fehlalarm). Gleiche Klasse wie
    der Pagination-Defekt aus Ticket 15.
    """
    out, after, guard = [], None, 0
    while True:
        q = "payment_links?limit=100" + (f"&starting_after={after}" if after else "")
        j = stripe_get(q, key)
        page = j.get("data", [])
        out.extend(page)
        guard += 1
        if not j.get("has_more") or not page or guard >= 20:
            return out, bool(j.get("has_more")) and guard >= 20
        after = page[-1].get("id")


def js_parity(thanks_html, sid):
    """Fuehrt die ECHTEN JS-Zeilen aus thanks.html in node aus.

    Kein Nachbau: die drei Zeilen werden aus der ausgelieferten Datei
    extrahiert und unveraendert ausgefuehrt. Rueckgabe:
    (status, js_url, detail) mit status in OK / ROT / UNGEPRUEFT.
    """
    z_buf = re.search(r"^[ \t]*(const\s+buf\s*=.*crypto\.subtle\.digest\(.*)$",
                      thanks_html, re.M)
    z_hex = re.search(r"^[ \t]*(const\s+hex\s*=.*)$", thanks_html, re.M)
    z_url = re.search(r"^[ \t]*(const\s+url\s*=\s*'dl/rtd/'.*)$", thanks_html, re.M)
    fehlend = [n for n, m in (("buf/digest", z_buf), ("hex", z_hex), ("url", z_url))
               if m is None]
    if fehlend:
        return "ROT", None, "JS-Zeilen nicht gefunden: " + ", ".join(fehlend)

    src = ("const sid = process.argv[2];\n(async () => {\n"
           + z_buf.group(1) + "\n" + z_hex.group(1) + "\n" + z_url.group(1) + "\n"
           + "process.stdout.write(String(url));\n})().catch(e => {"
           + "process.stderr.write(String(e)); process.exit(9); });\n")
    verfuegbar, out, err = run_node(src, sid)
    if not verfuegbar:
        return "UNGEPRUEFT", None, f"JS nicht ausfuehrbar ({err})"
    if err:
        return "ROT", out or None, f"node-Fehler: {err}"
    return ("OK" if out == f"dl/rtd/{sid_hash(sid)}.html" else "ROT"), out, ""


def main():
    key = get_key()
    if not (key and key.startswith("sk_live_")):
        print("KEIN_LIVE_KEY -> DEMO moeglich, Stopp.")
        return 1

    ok = True
    ungeprueft = False

    # 1) URLs aus rtd.html extrahieren
    html = read_text(RTD)
    urls = sorted(set(re.findall(r'https://buy\.stripe\.com/[A-Za-z0-9]+', html)))
    # Soll-Zahl aus der Datei selbst ableiten, nicht raten: jede Preisoption im
    # Dropdown braucht einen Link. Verliert ein Tier seinen Link, faellt das auf.
    tiers = re.findall(r'<option value="([0-9.]+)"', html)
    print(f"[1] rtd.html LIVE-Links gefunden: {len(urls)} (Preis-Optionen: {len(tiers)})")
    for u in urls:
        print("    ", u)
    if not urls:
        print("    KEIN EINZIGER LIVE-LINK auf der Kaufseite -> kein Geldpfad.")
        ok = False
    elif tiers and len(urls) != len(tiers):
        print(f"    ABWEICHUNG: {len(tiers)} Preis-Optionen, aber {len(urls)} Links.")
        ok = False

    # 2) Links live abfragen — buy.stripe.com-Slugs sind NICHT die API-IDs,
    #    daher ueber /v1/payment_links auflisten und per url-Feld matchen.
    print("[2] Stripe-Status je Link:")
    listed, abgeschnitten = list_payment_links(key)
    if abgeschnitten:
        print("    WARNUNG: Payment-Link-Liste abgeschnitten (has_more) -> unvollstaendig.")
        ungeprueft = True
    by_url = {pl.get("url"): pl for pl in listed}
    for u in urls:
        pl = by_url.get(u)
        if pl is None:
            print(f"    {u} -> NICHT in payment_links gefunden (evtl. inaktiv/geloescht)")
            ok = False
            continue
        ac = (pl.get("after_completion") or {}).get("redirect", {}).get("url", "")
        fields = [cf.get("key") for cf in pl.get("custom_fields", [])]
        # line_items im List-Response oft NICHT expandiert -> Sub-Endpoint.
        amt, cur = None, None
        try:
            lj = stripe_get(f"payment_links/{pl['id']}/line_items?limit=1", key).get("data", [])
            if lj:
                amt = (lj[0].get("price") or {}).get("unit_amount")
                cur = (lj[0].get("price") or {}).get("currency")
        except Exception as e:
            print(f"      (Preis-Abfrage fehlgeschlagen: {e})")
        good = (pl.get("livemode") is True and pl.get("active") is True
                and "anfrage" in fields
                and "thanks.html?sid={CHECKOUT_SESSION_ID}" in ac
                and isinstance(amt, int) and not isinstance(amt, bool) and amt > 0)
        ok = ok and good
        print(f"    livemode={pl.get('livemode')} active={pl.get('active')} "
              f"preis={fmt_preis(amt, cur)} fields={fields}")
        print(f"      redirect={ac}  -> {'OK' if good else 'PROBLEM'}")

    # 3) Hash-Paritaet: JS aus thanks.html WIRKLICH ausfuehren und mit Python
    #    vergleichen. Bis Ticket 16 stand hier nur ein Behauptungssatz.
    print("[3] Hash-Paritaet (JS aus thanks.html real ausgefuehrt vs Python):")
    sample = "cs_live_" + "a" * 24   # plausibles Format, kein echter Sale
    status, js_url, detail = js_parity(read_text(THANKS), sample)
    py_url = f"dl/rtd/{sid_hash(sample)}.html"
    print(f"    sample_sid={sample}")
    print(f"    python -> {py_url}")
    print(f"    js     -> {js_url}   [{status}]" + (f"  {detail}" if detail else ""))
    if status == "ROT":
        ok = False
    elif status == "UNGEPRUEFT":
        ungeprueft = True

    # 4) Deliverable-Verzeichnis (nur Information: leer ist bei 0 Sales korrekt;
    #    dass der Publish-Weg traegt, hat Ticket 11 separat gemessen)
    n = count_deliverables()
    print(f"[4] dl/rtd/*.html vorhanden: {'Verzeichnis fehlt' if n is None else n}"
          f" (Info, kein Gruen-Kriterium)")

    if not ok:
        print("ERGEBNIS: KETTE_PROBLEM")
        return 1
    if ungeprueft:
        print("ERGEBNIS: KETTE_UNGEPRUEFT (nicht gruen — eine Etappe war nicht messbar)")
        return 2
    print("ERGEBNIS: KETTE_OK")
    return 0


# --------------------------------------------------------------------------
# Selftest (Ticket 16) — Fault Injection durch die ECHTE main()
# --------------------------------------------------------------------------
def _pl(url, active=True, livemode=True, fields=("anfrage",),
        redirect="https://translucentv1.github.io/new-business/thanks.html"
                 "?sid={CHECKOUT_SESSION_ID}", pid=None):
    """Feldtreuer payment_link (Felder gegen die LIVE-API abgeglichen)."""
    return {"id": pid or ("plink_" + url[-6:]), "url": url, "active": active,
            "livemode": livemode,
            "custom_fields": [{"key": k} for k in fields],
            "after_completion": {"type": "redirect", "redirect": {"url": redirect}}}


_RTD_TPL = """<select id="tier">
      <option value="3.99">Basis</option>
      <option value="7.99">Standard</option>
      <option value="14.99">Premium</option>
    </select>
<script>const LINKS = {%s};</script>"""

_URLS = ["https://buy.stripe.com/AAAAAA1", "https://buy.stripe.com/BBBBBB2",
         "https://buy.stripe.com/CCCCCC3"]


def _rtd_html(urls=None):
    urls = _URLS if urls is None else urls
    return _RTD_TPL % ",".join(f'"{i}":"{u}"' for i, u in enumerate(urls))


def _thanks_html(slice_n=16, algo="SHA-256", drop=None):
    zeilen = {
        "buf": f"  const buf = await crypto.subtle.digest('{algo}', "
               f"new TextEncoder().encode(sid));",
        "hex": "  const hex = Array.from(new Uint8Array(buf)).map(b=>b.toString(16)"
               f".padStart(2,'0')).join('').slice(0,{slice_n});",
        "url": "  const url = 'dl/rtd/' + hex + '.html';",
    }
    if drop:
        zeilen.pop(drop, None)
    return "<script>\n(async function(){\n" + "\n".join(zeilen.values()) + "\n})();\n</script>"


def _run_main(links=None, rtd=None, thanks=None, amount=399, pages=None,
              node_weg=False):
    """Faehrt die ECHTE main() gegen injizierte Aussenwelt."""
    import contextlib
    import io

    global get_key, stripe_get, read_text, run_node, count_deliverables
    orig = (get_key, stripe_get, read_text, run_node, count_deliverables)
    seiten = pages if pages is not None else [
        {"data": (_pl_default() if links is None else links), "has_more": False}]
    state = {"i": 0}

    def fake_get_key():
        return "sk_live_" + "x" * 20

    def fake_stripe_get(path, key):
        if "/line_items" in path:
            return {"data": [{"price": {"unit_amount": amount, "currency": "eur"}}]}
        i = state["i"]
        state["i"] += 1
        return seiten[i] if i < len(seiten) else {"data": [], "has_more": False}

    def fake_read_text(path):
        if path == RTD:
            return _rtd_html() if rtd is None else rtd
        if path == THANKS:
            return _thanks_html() if thanks is None else thanks
        raise AssertionError("unerwarteter Pfad " + path)

    def fake_run_node(src, arg):
        if node_weg:
            return False, "", "node nicht gefunden"
        return orig[3](src, arg)

    get_key, stripe_get, read_text, run_node, count_deliverables = (
        fake_get_key, fake_stripe_get, fake_read_text, fake_run_node, lambda: 0)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = main()
    finally:
        (get_key, stripe_get, read_text, run_node, count_deliverables) = orig
    return rc, buf.getvalue()


def _pl_default():
    return [_pl(u) for u in _URLS]


def selftest():
    """Fault Injection durch den Produktivpfad. rc=0 nur wenn alles gruen."""
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    def rot(name, rc, out, wort="KETTE_PROBLEM"):
        # Exit-Code-Falle: ein Absturz ist KEINE Erkennung.
        check(name, rc == 1 and wort in out and "Traceback" not in out,
              f"rc={rc} traceback={'Traceback' in out}")

    # 1 — gesund (Referenz; JS wird hier ECHT in node ausgefuehrt)
    rc, out, = _run_main()
    check("gesund -> KETTE_OK, rc=0",
          rc == 0 and "KETTE_OK" in out and "Traceback" not in out, f"rc={rc}")

    # 2 — Link deaktiviert
    rc, out = _run_main(links=[_pl(_URLS[0], active=False)] + [_pl(u) for u in _URLS[1:]])
    rot("active=False wird rot", rc, out)

    # 3 — Testmodus statt LIVE
    rc, out = _run_main(links=[_pl(_URLS[0], livemode=False)] + [_pl(u) for u in _URLS[1:]])
    rot("livemode=False wird rot", rc, out)

    # 4 — Preis 0
    rc, out = _run_main(amount=0)
    rot("Preis 0 wird rot", rc, out)

    # 5 — Preis fehlt ganz
    rc, out = _run_main(amount=None)
    rot("fehlender Preis wird rot", rc, out)

    # 6 — Pflichtfeld 'anfrage' weg (ohne Anfragetext ist die Ware unerzeugbar)
    rc, out = _run_main(links=[_pl(_URLS[0], fields=())] + [_pl(u) for u in _URLS[1:]])
    rot("fehlendes Pflichtfeld 'anfrage' wird rot", rc, out)

    # 7 — Redirect auf fremde/tote Domain
    rc, out = _run_main(links=[_pl(_URLS[0], redirect="https://example.com/danke")]
                              + [_pl(u) for u in _URLS[1:]])
    rot("falscher Redirect wird rot", rc, out)

    # 8 — Link existiert bei Stripe gar nicht mehr
    rc, out = _run_main(links=[_pl(u) for u in _URLS[1:]])
    rot("verschwundener Link wird rot", rc, out)

    # 9 — 0 Links auf der Kaufseite. DAS war der reale Defekt: die alte Fassung
    #     lief mit leerer Schleife durch und meldete KETTE_OK.
    rc, out = _run_main(rtd=_rtd_html([]), links=[])
    rot("0 Links auf rtd.html wird rot", rc, out)

    # 10 — ein Tier hat seinen Link verloren (2 Links, 3 Preis-Optionen)
    rc, out = _run_main(rtd=_rtd_html(_URLS[:2]), links=[_pl(u) for u in _URLS[:2]])
    rot("Link-Anzahl != Preis-Optionen wird rot", rc, out)

    # 11 — Hash-Paritaet verletzt: JS schneidet auf 15 statt 16 Zeichen
    rc, out = _run_main(thanks=_thanks_html(slice_n=15))
    rot("Hash-Paritaet (slice 15) wird rot", rc, out)

    # 12 — Hash-Paritaet verletzt: JS nutzt SHA-1
    rc, out = _run_main(thanks=_thanks_html(algo="SHA-1"))
    rot("Hash-Paritaet (SHA-1) wird rot", rc, out)

    # 13 — Hash-Zeile aus thanks.html verschwunden
    rc, out = _run_main(thanks=_thanks_html(drop="hex"))
    rot("fehlende JS-Hashzeile wird rot", rc, out)

    # 14 — node fehlt: NICHT gruen, aber auch kein Defekt-Claim
    rc, out = _run_main(node_weg=True)
    check("node fehlt -> KETTE_UNGEPRUEFT, rc=2",
          rc == 2 and "KETTE_UNGEPRUEFT" in out and "KETTE_OK" not in out
          and "Traceback" not in out, f"rc={rc}")

    # 15 — Pagination: Links liegen erst auf Seite 2 (Ticket-15-Defektklasse)
    rc, out = _run_main(pages=[{"data": [_pl("https://buy.stripe.com/ZZZZZZ9")],
                                "has_more": True},
                               {"data": _pl_default(), "has_more": False}])
    check("Pagination holt Seite 2 -> KETTE_OK",
          rc == 0 and "KETTE_OK" in out, f"rc={rc}")

    # 16 — Kontrollprobe: rc-Wechsel zurueck nach 0 belegt
    rc, out = _run_main()
    check("nach allen Rot-Faellen wieder KETTE_OK", rc == 0 and "KETTE_OK" in out)

    print("== verify_rtd_chain --selftest (Fault Injection) ==")
    fails = 0
    for name, ok_, detail in results:
        print(f"  [{'OK ' if ok_ else 'ROT'}] {name}"
              + (f"   {detail}" if detail and not ok_ else ""))
        if not ok_:
            fails += 1
    print(f"\n{len(results) - fails}/{len(results)} "
          + ("SELFTEST_OK" if not fails else "SELFTEST_ROT"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    sys.exit(main())
