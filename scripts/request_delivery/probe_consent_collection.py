#!/usr/bin/env python3
"""Ticket 7 — MESSEN, ob ein Stripe **Payment Link** eine beweisbare Zustimmung
nach § 356 Abs. 6 BGB (`consent_collection[terms_of_service]`) tragen kann.
(Zitat korrigiert 2026-08-04: fuer digitale Inhalte ohne koerperlichen
Datentraeger gilt Abs. 6, nicht Abs. 5 — Primaerquelle gesetze-im-internet.de.)

Kein Schluss aus Analogie zu Checkout Sessions: es wird gegen die echte
Payment-Links-API geprueft.

Ablauf (bewusst in dieser Reihenfolge, weil er die einzige Einnahmequelle
beruehrt):
  1. Ist-Zustand ALLER Payment Links sichern (JSON-Backup, roh).
  2. Vorhandene Links read-only auf `consent_collection` inspizieren.
  3. Create-Probe: NEUEN Live-Link mit consent_collection[terms_of_service]
     =required anlegen (gleicher Preis wie Basis) und die API-Antwort roh
     protokollieren. Erfolg ODER Fehlertext sind beides MEASURED-Belege.
  4. Probe-Link sofort wieder deaktivieren (active=false), damit er nie
     im Verkauf landet.

Die 3 produktiven Links werden NICHT veraendert.

Nutzung: python probe_consent_collection.py [--keep-probe]
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import app  # noqa: E402  get_stripe_key

BACKUP = os.path.join(HERE, "plinks_backup_%s.json"
                      % datetime.date.today().isoformat())
PROBE_MARKER = "TICKET7-CONSENT-PROBE"


def api(path, data=None, key=None, method=None):
    """Gibt (ok, payload) zurueck. Fehler werden NICHT geschluckt, sondern
    als geparster Stripe-Fehler zurueckgegeben — der Fehlertext ist hier der
    eigentliche Messwert."""
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


def main():
    key = app.get_stripe_key()
    if not (key and key.startswith("sk_live_")):
        print("KEIN_LIVE_KEY -> nur DEMO moeglich, Stopp.")
        return 1

    # ---- 1) Ist-Zustand sichern -------------------------------------------
    ok, listed = api("payment_links?limit=100", key=key)
    if not ok:
        print("FEHLER beim Auflisten:", json.dumps(listed)[:400])
        return 1
    links = listed.get("data", [])
    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)
    print(f"[1] Backup: {len(links)} Payment Links -> {os.path.basename(BACKUP)}")

    # ---- 2) Ist-Zustand consent_collection (read-only) --------------------
    print("[2] consent_collection an den bestehenden LIVE-Links:")
    active = [pl for pl in links if pl.get("active")]
    for pl in active:
        print(f"    {pl['id']} active={pl.get('active')} "
              f"livemode={pl.get('livemode')} "
              f"consent_collection={json.dumps(pl.get('consent_collection'))}")
    has_field = any("consent_collection" in pl for pl in links)
    print(f"    -> Feld im Payment-Link-Objekt vorhanden: {has_field}")

    # Preis der Basis-Variante fuer die Create-Probe wiederverwenden.
    price_id = None
    if active:
        ok, li = api(f"payment_links/{active[0]['id']}/line_items?limit=1", key=key)
        if ok and li.get("data"):
            price_id = li["data"][0]["price"]["id"]
            amt = li["data"][0]["price"]["unit_amount"]
            print(f"    Referenzpreis fuer Probe: {price_id} "
                  f"({amt} cent = {amt/100:.2f} EUR)")
    if not price_id:
        print("    KEIN Preis gefunden -> Create-Probe nicht moeglich.")
        return 1

    # ---- 3) Create-Probe ---------------------------------------------------
    print("[3] Create-Probe: neuer Link MIT consent_collection[terms_of_service]"
          "=required")
    payload = {
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "consent_collection[terms_of_service]": "required",
        "metadata[probe]": PROBE_MARKER,
    }
    ok, resp = api("payment_links", payload, key=key)
    if ok:
        print("    HTTP 200 — Parameter AKZEPTIERT.")
        print("    id=", resp["id"], " url=", resp.get("url"))
        print("    consent_collection=",
              json.dumps(resp.get("consent_collection")))
        verdict = "CONSENT_MOEGLICH"
    else:
        err = resp.get("error", {})
        print("    ABGELEHNT von Stripe:")
        print("    type   =", err.get("type"))
        print("    code   =", err.get("code"))
        print("    param  =", err.get("param"))
        print("    message=", err.get("message"))
        verdict = "CONSENT_BLOCKIERT"

    # ---- 4) Probe-Link entschaerfen ---------------------------------------
    if ok and "--keep-probe" not in sys.argv:
        ok2, r2 = api(f"payment_links/{resp['id']}", {"active": "false"}, key=key)
        print(f"[4] Probe-Link deaktiviert: active={r2.get('active') if ok2 else r2}")
    elif ok:
        print("[4] Probe-Link BLEIBT aktiv (--keep-probe).")
    else:
        print("[4] nichts anzulegen/aufzuraeumen (Create schlug fehl).")

    print("ERGEBNIS:", verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
