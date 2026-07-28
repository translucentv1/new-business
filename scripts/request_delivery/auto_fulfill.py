#!/usr/bin/env python3
"""Auto-Fulfillment fuer LIVE-Stripe-Sales (statische Site, kein Server).

Flow (jeder Cron-Tick):
  1. Stripe: alle checkout.sessions mit payment_status=paid holen (LIVE key).
  2. Neue (nicht in fulfilled_live.json) verarbeiten:
     - Anfrage-Text aus custom_field "anfrage"
     - Deliverable via lokalem Ollama (qwen2.5:3b, $0) generieren
     - Als HTML unter dl/rtd/<sha256(session_id)[:16]>.html ins Repo schreiben
  3. git add/commit/push -> GitHub Pages liefert die Seite aus.
  4. Kunde landet nach Zahlung auf thanks.html?sid=<session_id>; deren JS
     berechnet denselben Hash und pollt die Deliverable-URL.

Delivery-Kette komplett ohne E-Mail (SMTP nicht konfiguriert = USER-Blocker).

Nutzung:
  python auto_fulfill.py            # poll + fulfill + push
  python auto_fulfill.py --dry-run  # poll + generate, KEIN git push
  python auto_fulfill.py --selftest # Pipeline mit Fake-Order testen (kein Stripe)
"""
import hashlib
import html
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import app  # noqa: E402  (get_stripe_key)
from gig_fulfill import gen_deliverable  # noqa: E402  (Ollama, $0)

STATE = os.path.join(HERE, "fulfilled_live.json")
DL_DIR = os.path.join(ROOT, "dl", "rtd")
SITE = "https://translucentv1.github.io/new-business"

PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Dein Deliverable</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;
padding:0 16px;line-height:1.65;color:#1a1a1a}}
pre{{white-space:pre-wrap;background:#f7f7f7;border:1px solid #e3e3e3;
border-radius:8px;padding:1.2em;font-family:inherit}}
.note{{color:#666;font-size:.9rem;border-top:1px solid #eee;margin-top:2em;
padding-top:1em}}</style></head><body>
<h1>Dein Deliverable ✅</h1>
<p><strong>Deine Anfrage:</strong> {req}</p>
<pre>{body}</pre>
<p><a href="javascript:window.print()">Als PDF speichern / drucken</a></p>
<div class="note"><p>Bestellung {oid} · Danke fuer deinen Kauf!
Rueckfragen: siehe <a href="../../impressum.html">Impressum</a>.</p></div>
</body></html>
"""


def sid_hash(sid: str) -> str:
    return hashlib.sha256(sid.encode()).hexdigest()[:16]


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {}


def save_state(d):
    json.dump(d, open(STATE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def stripe_get(path):
    key = app.get_stripe_key()
    assert key and key.startswith("sk_live_"), "kein LIVE key -> Stopp"
    req = urllib.request.Request("https://api.stripe.com/v1/" + path,
                                 headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def write_page(sid, anfrage, text):
    os.makedirs(DL_DIR, exist_ok=True)
    h = sid_hash(sid)
    path = os.path.join(DL_DIR, h + ".html")
    page = PAGE.format(req=html.escape(anfrage or "(kein Anfrage-Text im Checkout)"),
                       body=html.escape(text), oid=h)
    open(path, "w", encoding="utf-8").write(page)
    return path, f"{SITE}/dl/rtd/{h}.html"


def git_publish(msg):
    for cmd in (["git", "add", "dl/rtd"],
                ["git", "commit", "-m", msg],
                ["git", "push"]):
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if p.returncode != 0 and "nothing to commit" not in p.stdout + p.stderr:
            print("GIT FEHLER:", cmd, p.stdout, p.stderr)
            return False
    return True


def wait_live(url, tries=18, pause=10):
    for _ in range(tries):
        try:
            r = urllib.request.urlopen(url, timeout=15)
            if r.status == 200:
                return True
        except Exception:
            pass
        time.sleep(pause)
    return False


def fulfill_session(s, state, push=True, persist=True):
    sid = s["id"]
    email = (s.get("customer_details") or {}).get("email")
    anfrage = None
    for f in s.get("custom_fields") or []:
        if f.get("key") == "anfrage":
            anfrage = (f.get("text") or {}).get("value")
    req_text = anfrage or "Der Kunde hat kein Anfrage-Feld ausgefuellt."
    text, err = gen_deliverable(req_text)
    if err:
        text = (f"Deine Bestellung ist eingegangen. Die automatische Erstellung "
                f"war kurzzeitig nicht verfuegbar ({err}); diese Seite wird beim "
                f"naechsten Lauf aktualisiert.")
    path, url = write_page(sid, anfrage, text)
    state[sid] = {"ts": int(time.time()), "email": email,
                  "amount": s.get("amount_total"), "url": url,
                  "llm_err": err, "final": err is None}
    if persist:
        save_state(state)
    print(f"FULFILLED {sid} -> {path}")
    if push:
        ok = git_publish(f"RTD auto-fulfill {sid_hash(sid)} (LIVE sale)")
        live = ok and wait_live(url)
        print(f"  push={ok} live200={live} url={url}")
        # Sale-Log (MEASURED)
        with open(os.path.join(ROOT, "sales.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": int(time.time()), "source": "stripe_rtd",
                                "sid": sid, "amount": s.get("amount_total"),
                                "currency": s.get("currency"), "email": email,
                                "deliverable": url}, ensure_ascii=False) + "\n")
    return url


def main():
    dry = "--dry-run" in sys.argv
    if "--selftest" in sys.argv:
        fake = {"id": "cs_test_selftest_" + uuid_hex(), "amount_total": 399,
                "currency": "eur",
                "customer_details": {"email": "selftest@example.com"},
                "custom_fields": [{"key": "anfrage", "text": {
                    "value": "Schreibe 3 Instagram-Captions fuer ein Cafe in Berlin."}}]}
        url = fulfill_session(fake, {}, push=False, persist=False)
        h = sid_hash(fake["id"])
        p = os.path.join(DL_DIR, h + ".html")
        size = os.path.getsize(p)
        print(f"SELFTEST OK: {p} ({size} bytes) waere live unter {url}")
        os.remove(p)
        return
    sessions = stripe_get("checkout/sessions?limit=50")["data"]
    paid = [s for s in sessions if s.get("payment_status") == "paid"]
    state = load_state()
    new = [s for s in paid if s["id"] not in state]
    print(f"sessions={len(sessions)} paid={len(paid)} neu={len(new)}")
    for s in new:
        print("ERSTER SALE" if not os.path.exists(os.path.join(ROOT, "sales.log"))
              or "stripe_rtd" not in open(os.path.join(ROOT, "sales.log"),
                                          encoding="utf-8").read()
              else "SALE", "->", s["id"], s.get("amount_total"), s.get("currency"))
        fulfill_session(s, state, push=not dry)
    if not new:
        print("keine neuen Sales.")


def uuid_hex():
    import uuid
    return uuid.uuid4().hex[:10]


if __name__ == "__main__":
    main()
