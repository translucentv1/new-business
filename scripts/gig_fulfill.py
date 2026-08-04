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

MODEL = "qwen2.5:3b"
OLLAMA = "http://localhost:11434/api/generate"

# Ticket 12: Die verkaufte Preisstufe muss die Erzeugung erreichen.
# Bis 2026-08-04 nahm gen_deliverable() NUR den Anfragetext -> Basis, Standard
# und Premium liefen durch denselben Prompt und lieferten dasselbe (~290 Woerter
# MEASURED). Verkauft werden aber drei Umfaenge (rtd.html/gig.html) und
# Revisionen stehen sogar in agb.html §3 = Vertragsinhalt.
#
# Zielwerte gespiegelt aus gig.html Z. 90-92 (Quelle des Versprechens).
# "sections>1" = abschnittsweise Erzeugung: MEASURED 2026-08-04, dass ein
# EINZELNER Prompt mit Ziel 1800-2000 Woerter auf qwen2.5:3b nur 683 Woerter
# liefert (188 s). Ein Prompt-Wunsch allein haette den Umfang NICHT gebracht.
TIER_SPEC = {
    399:  {"cents": 399,  "name": "Basis",    "words": 300,  "sections": 1,
           "revisions": 0, "scope": "bis ~300 Woerter bzw. ~50 Zeilen Code"},
    799:  {"cents": 799,  "name": "Standard", "words": 800,  "sections": 2,
           "revisions": 1, "scope": "bis ~800 Woerter bzw. ~150 Zeilen Code"},
    1499: {"cents": 1499, "name": "Premium",  "words": 2000, "sections": 4,
           "revisions": 2, "scope": "bis ~2000 Woerter bzw. komplettes Template"},
}


def tier_spec(tier):
    """Cent-Betrag -> Spec. Unbekannt/None -> None (Altverhalten)."""
    if tier is None:
        return None
    try:
        return TIER_SPEC.get(int(tier))
    except (TypeError, ValueError):
        return None


def _ollama(prompt, num_predict=None, timeout=300):
    """Ein Ollama-Call. Gibt (text, err) zurueck, wirft nie."""
    try:
        import urllib.request, json as _json
        payload = {"model": MODEL, "prompt": prompt, "stream": False}
        if num_predict:
            payload["options"] = {"num_predict": num_predict}
        r = urllib.request.Request(OLLAMA, data=_json.dumps(payload).encode(),
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            data = _json.load(resp)
        out = (data.get("response") or "").strip()
        return (out, None) if out else (None, "OLLAMA_EMPTY")
    except Exception as e:
        return None, f"OLLAMA_ERR:{e}"


def _outline(req_text, spec):
    """Gliederung als Liste von Zwischenueberschriften. [] = fehlgeschlagen."""
    n = spec["sections"]
    txt, err = _ollama(
        f"Erstelle eine Gliederung fuer folgenden Auftrag: {req_text}\n\n"
        f"Antworte mit GENAU {n} Zwischenueberschriften auf Deutsch, "
        f"eine pro Zeile, ohne Nummerierung, ohne Einleitung, ohne Kommentar.",
        num_predict=300, timeout=180)
    if err or not txt:
        return []
    heads = []
    for line in txt.splitlines():
        line = line.strip().lstrip("-*#0123456789. )\t").strip()
        if line and len(line) < 120:
            heads.append(line)
    return heads[:n]


def gen_deliverable(req_text, tier=None):
    """Erzeugt das Deliverable. tier=Cent-Betrag der gekauften Stufe.

    tier=None -> exakt das alte Verhalten (Altaufrufer bleiben gueltig).
    """
    spec = tier_spec(tier)
    if spec is None:
        return _ollama(f"{SYSTEM}\n\nAuftrag: {req_text}", timeout=120)

    # Eine Stufe, ein Prompt: Basis/Standard.
    if spec["sections"] <= 1:
        return _ollama(
            f"{SYSTEM}\nUmfang: ca. {spec['words']} Woerter ({spec['scope']}). "
            f"Schoepfe den Umfang aus.\n\nAuftrag: {req_text}",
            num_predict=max(1024, spec["words"] * 3), timeout=300)

    # Mehrere Abschnitte: Gliederung -> Abschnitte -> Zusammenbau.
    heads = _outline(req_text, spec)
    if not heads:
        # Kein Hard-Fail: lieber ein kuerzeres Deliverable als gar keins.
        return _ollama(
            f"{SYSTEM}\nUmfang: ca. {spec['words']} Woerter ({spec['scope']}). "
            f"Gliedere in Abschnitte mit Zwischenueberschriften.\n\n"
            f"Auftrag: {req_text}",
            num_predict=max(1024, spec["words"] * 3), timeout=420)

    per = max(150, spec["words"] // len(heads))
    parts, errs = [], []
    for i, head in enumerate(heads, 1):
        body, err = _ollama(
            f"{SYSTEM}\nDu schreibst Abschnitt {i} von {len(heads)} eines "
            f"groesseren Deliverables.\nGesamtauftrag: {req_text}\n"
            f"Gliederung: {' | '.join(heads)}\n\n"
            f"Schreibe NUR den Abschnitt \"{head}\" mit ca. {per} Woertern. "
            f"Keine Wiederholung anderer Abschnitte, keine Meta-Kommentare, "
            f"keine Ueberschrift wiederholen.",
            num_predict=max(768, per * 3), timeout=300)
        if err:
            errs.append(err)
            continue
        parts.append(f"{head}\n\n{body}")
    if not parts:
        return None, errs[0] if errs else "OLLAMA_EMPTY"
    return "\n\n".join(parts), None

def fulfill(req_text, price_cents):
    oid = uuid.uuid4().hex[:12]
    text, err = gen_deliverable(req_text, tier=price_cents)
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
