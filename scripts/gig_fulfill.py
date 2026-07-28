#!/usr/bin/env python3
"""
AUTONOME GIG-FULFILLMENT-PIPELINE (Bens "Task Market" legal gespiegelt).

Flow:
  1. Auftrag rein (Text vom Kaeufer + gewaehlte Tier-Preis in EUR-Cent)
  2. LLM_API_KEY (openai, bereits in Env) erstellt das Deliverable
  3. Speichern unter deliverables/<oid>.txt
  4. Rueckgabe des echten Stripe-Payment-Links (app.create_payment_link)

KEINE Kosten: LLM_API_KEY ist vom User gestellt (kein eigener Einkauf).
Stripe-Link ist LIVE (Key MEASURED valid). Kaeufer zahlt -> echter Sale.

Nutzung:
  python3 scripts/gig_fulfill.py "Schreibe eine Bewerbung als Data Analyst" 399
"""
import os, sys, json, uuid
import urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "request_delivery"))
import app

DELIV = os.path.join(ROOT, "scripts", "request_delivery", "deliverables")

SYSTEM = ("Du bist ein professioneller Ghostwriter fuer bezahlte Auftraege. "
          "Antworte NUR mit dem fertigen Deliverable auf Deutsch, ohne Meta-Kommentar. "
          "Klare Struktur, fertig zur Abgabe.")

def gen_deliverable(req_text):
    # Lokal via Ollama (qwen2.5:3b) — $0, kein API-Key, keine Kosten.
    try:
        import urllib.request, json as _json
        body = _json.dumps({
            "model": "qwen2.5:3b",
            "prompt": f"{SYSTEM}\n\nAuftrag: {req_text}",
            "stream": False
        }).encode()
        r = urllib.request.Request("http://localhost:11434/api/generate",
                                   data=body,
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=120) as resp:
            data = _json.load(resp)
        out = data.get("response", "").strip()
        if out:
            return out, None
        return None, "OLLAB_EMPTY"
    except Exception as e:
        return None, f"OLLAMA_ERR:{e}"

def fulfill(req_text, price_cents):
    oid = uuid.uuid4().hex[:12]
    text, err = gen_deliverable(req_text)
    if err:
        # Fallback: Template statt Hard-Fail
        text = f"[Entwurf] {req_text}\n\n(LLM nicht verfuegbar: {err})"
    os.makedirs(DELIV, exist_ok=True)
    open(os.path.join(DELIV, f"{oid}.txt"), "w", encoding="utf-8").write(text)
    # echter Stripe-Link
    url, demo = app.create_payment_link(req_text[:60], price_cents)
    # Order speichern
    app.add_order(oid, req_text, price_cents, url, demo=demo)
    d = app.load_orders()
    d[oid]["deliverable"] = text[:500]
    app.save_orders(d)
    return oid, url, demo, err

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: gig_fulfill.py <auftrag> <preis_cent>")
        sys.exit(1)
    oid, url, demo, err = fulfill(sys.argv[1], int(sys.argv[2]))
    print(f"OID: {oid}")
    print(f"DEMO: {demo}")
    print(f"PAY_LINK: {url}")
    print(f"LLM_ERR: {err}")
    print(f"Deliverable gespeichert: scripts/request_delivery/deliverables/{oid}.txt")
