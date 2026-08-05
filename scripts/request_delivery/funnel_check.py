#!/usr/bin/env python3
"""Funnel-Zaehler fuer den RTD-Kaufpfad — ohne Analytics, ohne Cookies.

GRUNDLAGE (MEASURED 2026-08-04, siehe tickets/9-besucher-messung.md):
Ein *echter Browser*, der einen Stripe Payment Link oeffnet, legt sofort eine
checkout.session an — noch bevor irgendetwas ausgefuellt oder bezahlt wird.
Ein reiner curl-GET (ohne JS) tut das NICHT. Damit ist die Session-Liste ein
kostenloser First-Party-Zaehler fuer die Stufe "Browser hat die Kaufseite
geoeffnet".

TRENNSCHARFES MERKMAL:
  session.payment_link = "plink_..."  -> echter Browser-Aufruf eines LIVE-Links
  session.payment_link = None         -> von uns per API erzeugte Probe-Session
Zusaetzlich werden eigene Testsessions per Id in OWN_FILE ausgeschlossen.

GRENZE (bewusst, nicht verschwiegen): gezaehlt wird die Stufe *Kaufseite
geoeffnet*, NICHT Besucher auf rtd.html. Wer rtd.html ansieht und nicht auf
"Jetzt kaufen" klickt, ist hier unsichtbar. Die Retention der Stripe-Liste ist
UNGEMESSEN — dieser Zaehler ist ein Live-Signal, kein Archiv.

VOLLZAEHLIGKEIT (Ticket 15): Stripe liefert max. 100 Sessions pro Seite und
meldet Reste ueber `has_more`. Bis 2026-08-05 las dieses Skript nur die erste
Seite und ignorierte `has_more` — der Zaehler haette ab Session 101 still zu
wenig gemeldet. Jetzt wird geblaettert (`starting_after`); bleibt nach
MAX_PAGES noch etwas uebrig, sagt das Skript "vollzaehlig = NEIN" und gibt
rc=3 zurueck, statt eine zu kleine Zahl als Wahrheit auszugeben.

Nutzung:
  python scripts/request_delivery/funnel_check.py
  python scripts/request_delivery/funnel_check.py --expire-own   # eigene Tests schliessen
  python scripts/request_delivery/funnel_check.py --selftest     # Fault Injection
"""
import datetime as _dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import app  # noqa: E402  (get_stripe_key)

OWN_FILE = os.path.join(HERE, "funnel_own_sessions.json")

# Stripe liefert max. 100 Sessions/Seite. 20 Seiten = 2000 Sessions Reserve.
MAX_PAGES = 20


def own_ids():
    """Session-Ids, die wir selbst erzeugt haben (Tests/Proben)."""
    if not os.path.exists(OWN_FILE):
        return {}
    with open(OWN_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def api(path, data=None, method=None):
    key = app.get_stripe_key()
    url = "https://api.stripe.com/v1/" + path
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, json.load(r)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return False, json.loads(raw)
        except Exception:
            return False, {"_http": e.code, "_raw": raw}


def fetch_all_sessions():
    """Alle checkout.sessions holen, ueber Seitengrenzen hinweg.

    Rueckgabe: (ok, sessions, vollzaehlig, fehler)
    vollzaehlig=False heisst: Stripe meldet weiter `has_more`, die Zahl ist
    also eine UNTERGRENZE und darf nicht als Messwert gelesen werden.
    """
    sessions = []
    starting_after = None
    for _ in range(MAX_PAGES):
        path = "checkout/sessions?limit=100"
        if starting_after:
            path += "&starting_after=" + starting_after
        ok, payload = api(path)
        if not ok:
            return False, sessions, False, payload
        page = payload.get("data", [])
        sessions.extend(page)
        if not payload.get("has_more") or not page:
            return True, sessions, True, None
        starting_after = page[-1]["id"]
    return True, sessions, False, None


def ts(epoch):
    if not epoch:
        return "-"
    return _dt.datetime.utcfromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%SZ")


def classify(s, own):
    if s["id"] in own:
        return "EIGENTEST"
    if not s.get("payment_link"):
        return "API-PROBE"
    return "BESUCHER"


def main():
    argv = sys.argv[1:]
    own = own_ids()
    ok, sessions, vollzaehlig, fehler = fetch_all_sessions()
    if not ok:
        print("STRIPE-FEHLER:", json.dumps(fehler)[:300])
        return 2

    buckets = {"BESUCHER": [], "API-PROBE": [], "EIGENTEST": []}
    for s in sessions:
        buckets[classify(s, own)].append(s)

    print("== RTD-Funnel (LIVE) ==")
    print(f"sessions_roh      = {len(sessions)}")
    print(f"vollzaehlig       = {'ja' if vollzaehlig else 'NEIN (Untergrenze!)'}")
    for kind in ("BESUCHER", "API-PROBE", "EIGENTEST"):
        print(f"{kind:<17} = {len(buckets[kind])}")

    besucher = buckets["BESUCHER"]
    bezahlt = [s for s in besucher if s.get("payment_status") == "paid"]
    print(f"davon bezahlt     = {len(bezahlt)}")
    if besucher:
        quote = 100.0 * len(bezahlt) / len(besucher)
        print(f"Conversion        = {quote:.1f} %  ({len(bezahlt)}/{len(besucher)})")
    else:
        print("Conversion        = n/a (kein einziger Browser hat die Kaufseite geoeffnet)")

    for kind in ("BESUCHER", "API-PROBE", "EIGENTEST"):
        for s in buckets[kind]:
            print(f"  [{kind}] {ts(s.get('created'))} {str(s.get('payment_status')):<8} "
                  f"{s.get('amount_total')} {s.get('currency')} "
                  f"link={s.get('payment_link')} id={s['id'][:28]}...")

    if "--expire-own" in argv:
        offen = [s for s in buckets["EIGENTEST"] if s.get("status") == "open"]
        print(f"\n-- expire-own: {len(offen)} offene Eigentests --")
        for s in offen:
            ok2, res = api(f"checkout/sessions/{s['id']}/expire", data={}, method="POST")
            print(f"  {s['id'][:28]}... -> ok={ok2} status={res.get('status') if ok2 else res}")

    print("\nHinweis: gezaehlt wird 'Browser hat die Kaufseite geoeffnet', "
          "NICHT Seitenaufrufe auf rtd.html.")
    if not vollzaehlig:
        print("WARNUNG: Stripe meldet weitere Seiten — die Zahlen sind eine "
              "UNTERGRENZE, kein Messwert.")
        return 3
    return 0


def _sess(sid, link=None, paid="unpaid", amount=399, status="open",
          created=1785848408):
    """Minimale, aber feldtreue checkout.session (Felder gegen die LIVE-API
    abgeglichen, siehe Ticket 15)."""
    return {"id": sid, "payment_link": link, "payment_status": paid,
            "amount_total": amount, "currency": "eur", "status": status,
            "created": created}


def _run_main(pages, own=None, argv=None, error=False):
    """Faehrt die ECHTE main() gegen eine injizierte Stripe-Antwort.

    Kein Reimplementat: gemessen wird der Produktivpfad inkl. classify(),
    fetch_all_sessions() und der echten Ausgabe.
    """
    import contextlib
    import io

    global api, own_ids
    orig_api, orig_own, orig_argv = api, own_ids, sys.argv
    calls = {"n": 0, "paths": []}

    def fake_api(path, data=None, method=None):
        calls["paths"].append(path)
        if error:
            return False, {"error": {"message": "injizierter Stripe-Fehler"}}
        i = calls["n"]
        calls["n"] += 1
        if i < len(pages):
            return True, pages[i]
        return True, {"data": [], "has_more": False}

    api = fake_api
    own_ids = lambda: (own or {})  # noqa: E731
    sys.argv = ["funnel_check.py"] + (argv or [])
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = main()
    finally:
        api, own_ids = orig_api, orig_own
        sys.argv = orig_argv
    return rc, buf.getvalue(), calls


def _num(out, key):
    import re
    m = re.search(r"^" + re.escape(key) + r"\s*=\s*(\d+)", out, re.M)
    return int(m.group(1)) if m else -1


def selftest():
    """Fault Injection durch den Produktivpfad. rc=0 nur wenn alles gruen."""
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    # 1 — leer: der Zustand, den dieses Skript bisher IMMER gemeldet hat
    rc, out, _ = _run_main([{"data": [], "has_more": False}])
    check("leer -> BESUCHER=0, rc=0",
          rc == 0 and _num(out, "BESUCHER") == 0 and "n/a" in out)

    # 2 — echter Browser: DER Fall, der nie bewiesen wurde
    rc, out, _ = _run_main([{"data": [_sess("cs_live_v1", link="plink_ABC")],
                             "has_more": False}])
    check("echter Browser -> BESUCHER=1",
          rc == 0 and _num(out, "BESUCHER") == 1
          and _num(out, "API-PROBE") == 0 and _num(out, "EIGENTEST") == 0,
          f"BESUCHER={_num(out, 'BESUCHER')}")

    # 3 — eigene API-Probe (payment_link=None)
    rc, out, _ = _run_main([{"data": [_sess("cs_live_p1", link=None)],
                             "has_more": False}])
    check("API-Probe -> API-PROBE=1",
          _num(out, "API-PROBE") == 1 and _num(out, "BESUCHER") == 0)

    # 4 — Eigentest schlaegt payment_link (Ticket-9-Trennmerkmal)
    rc, out, _ = _run_main([{"data": [_sess("cs_live_o1", link="plink_ABC")],
                             "has_more": False}], own={"cs_live_o1": "ticket9"})
    check("Eigentest schlaegt plink -> EIGENTEST=1",
          _num(out, "EIGENTEST") == 1 and _num(out, "BESUCHER") == 0)

    # 5 — gemischt
    rc, out, _ = _run_main([{"data": [_sess("cs_live_v2", link="plink_A"),
                                      _sess("cs_live_p2", link=None),
                                      _sess("cs_live_o2", link="plink_B")],
                             "has_more": False}], own={"cs_live_o2": "x"})
    check("gemischt -> 1/1/1",
          _num(out, "BESUCHER") == 1 and _num(out, "API-PROBE") == 1
          and _num(out, "EIGENTEST") == 1)

    # 6 — Conversion: 1 von 2 Besuchern bezahlt
    rc, out, _ = _run_main([{"data": [_sess("cs_live_v3", link="plink_A", paid="paid"),
                                      _sess("cs_live_v4", link="plink_B")],
                             "has_more": False}])
    check("Conversion 1/2 -> 50.0 %",
          "50.0 %" in out and "davon bezahlt     = 1" in out,
          out.split("Conversion")[1].splitlines()[0] if "Conversion" in out else "")

    # 7 — payment_status=None darf nicht crashen (war ein echter TypeError)
    rc, out, _ = _run_main([{"data": [_sess("cs_live_n1", link="plink_A", paid=None)],
                             "has_more": False}])
    check("payment_status=None ohne Crash",
          rc == 0 and "Traceback" not in out and _num(out, "BESUCHER") == 1)

    # 8 — Pagination: 2 Seiten muessen BEIDE gezaehlt werden
    rc, out, calls = _run_main([
        {"data": [_sess("cs_live_a%d" % i, link="plink_A") for i in range(100)],
         "has_more": True},
        {"data": [_sess("cs_live_b1", link="plink_A")], "has_more": False},
    ])
    check("Pagination -> 101 statt 100",
          rc == 0 and _num(out, "sessions_roh") == 101
          and _num(out, "BESUCHER") == 101,
          f"roh={_num(out, 'sessions_roh')} calls={len(calls['paths'])}")
    check("Pagination nutzt starting_after",
          any("starting_after=cs_live_a99" in p for p in calls["paths"]),
          str(calls["paths"][-1])[:80])

    # 9 — Truncation-Guard: has_more reisst nicht ab -> UNTERGRENZE + rc=3
    rc, out, _ = _run_main([{"data": [_sess("cs_live_t%d" % i, link="plink_A")],
                             "has_more": True} for i in range(MAX_PAGES + 2)])
    check("Dauer-has_more -> vollzaehlig NEIN + rc=3",
          rc == 3 and "NEIN" in out and "UNTERGRENZE" in out,
          f"rc={rc}")

    # 10 — Stripe-Fehler -> rc=2, keine erfundene Null
    rc, out, _ = _run_main([], error=True)
    check("Stripe-Fehler -> rc=2, kein 'BESUCHER = 0'",
          rc == 2 and "STRIPE-FEHLER" in out and _num(out, "BESUCHER") == -1,
          f"rc={rc}")

    # 11 — MUTATION (Rot-Probe): classify kaputt -> Fall 2 MUSS umkippen.
    #      Exit-Code-Falle: ein Absturz zaehlt NICHT als Erkennung.
    global classify
    orig_classify = classify
    try:
        classify = lambda s, own: "API-PROBE"  # noqa: E731
        rc_m, out_m, _ = _run_main([{"data": [_sess("cs_live_v1", link="plink_ABC")],
                                     "has_more": False}])
    finally:
        classify = orig_classify
    mutant_gefangen = (_num(out_m, "BESUCHER") == 0
                       and "Traceback" not in out_m)
    check("Mutation (classify kaputt) wird bemerkt, ohne Absturz",
          mutant_gefangen,
          f"BESUCHER_mutant={_num(out_m, 'BESUCHER')} traceback={'Traceback' in out_m}")

    # 12 — Kontrollprobe: nach Reparatur wieder gruen (rc-Wechsel belegt)
    rc, out, _ = _run_main([{"data": [_sess("cs_live_v1", link="plink_ABC")],
                             "has_more": False}])
    check("nach Mutations-Ruecknahme wieder BESUCHER=1",
          _num(out, "BESUCHER") == 1)

    print("== funnel_check --selftest (Fault Injection) ==")
    fails = 0
    for name, ok_, detail in results:
        print(f"  [{'OK ' if ok_ else 'ROT'}] {name}" + (f"   {detail}" if detail and not ok_ else ""))
        if not ok_:
            fails += 1
    print(f"\n{len(results) - fails}/{len(results)} "
          + ("SELFTEST_OK" if not fails else "SELFTEST_ROT"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        raise SystemExit(selftest())
    raise SystemExit(main())
