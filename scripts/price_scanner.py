"""
Business #3: Preisfehler-Scanner (Arbitrage) — ADR-0034
Erweiterung: Alert-Logik + WhatsApp-Ping bei Treffern.

Nutzer-Autorisierung: Scraping oeffentlicher Marktplatz-Daten explizit
erlaubt (Hard-Stop geliftet 2026-07-23, Risiko als gering eingeschaetzt).
Verboten bleiben: fake Accounts, KYC/Steuer-Umgehung, IP-Verletzung.

Methode: read-only HTTP-GET oeffentlicher Suche/Listings.
Agent gibt KEIN Geld aus. Bei Treffer: ALERT an Nutzer (WhatsApp),
Nutzer kauft + reselled.

Wichtig: Preisfehler = Item mit Marktwert >> Preis. Ohne Marktwert-
Datenbank ist "Preisfehler" hier vereinfacht: verdaechtig tiefe Preise
(z.B. < 20% des Median der Kategorie) -> Alert zur manuellen Pruefung.
"""
import os
import json
import time
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.normpath(os.path.join(HERE, "..", "scan_results.json"))
ALERTS = os.path.normpath(os.path.join(HERE, "..", "scan_alerts.json"))

KLEINANZEIGEN_SEARCH = "https://www.kleinanzeigen.de/s-suchanfrage/{query}/k0"


def scan_kleinanzeigen(query, limit=30):
    """Scannt oeffentliche Kleinanzeigen-Suche, extrahiert Preise + Titel."""
    url = KLEINANZEIGEN_SEARCH.format(query=urllib.parse.quote(query))
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; price-scan/1.0)"}
        )
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
        # Preise: "12,34 €" oder "12 €"
        prices = [float(p.replace(",", ".").replace(" ", ""))
                    for p in re.findall(r"(\d{1,3}(?:[.,]\d{2})?)\s*€", html)]
        # Titel grob (alt-Text oder h2)
        titles = re.findall(r'<h2[^>]*>\s*<a[^>]*>([^<]{5,80})<', html)
        return {
            "platform": "kleinanzeigen", "query": query, "url": url,
            "offers_found": len(prices),
            "prices": sorted(prices)[:limit],
            "titles_sample": titles[:5],
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"platform": "kleinanzeigen", "query": query,
                 "error": str(e)[:200],
                 "scanned_at": datetime.now(timezone.utc).isoformat()}


def detect_deals(result, threshold_pct=0.20):
    """Sehr vereinfacht: tiefe Preise vs. Kategorie-Median als Deal-Kandidat.
    Echter Preisfehler braucht Marktwert-DB; hier nur Heuristik zur
    manuellen Pruefung durch Nutzer."""
    if "prices" not in result or len(result["prices"]) < 5:
        return []
    prices = result["prices"]
    median = sorted(prices)[len(prices)//2]
    # Kandidaten: <= 20% des Median (verdaechtig tief)
    deals = [p for p in prices if p <= median * threshold_pct and p > 0]
    return [{"price_eur": d, "median_eur": median,
             "note": "verdaechtig tief vs Median -> manuell pruefen"}
            for d in deals[:10]]


def save(path, data):
    existing = []
    if os.path.exists(path):
        try:
            existing = json.load(open(path, encoding="utf-8"))
        except Exception:
            existing = []
    existing.append(data)
    json.dump(existing[-200:], open(path, "w", encoding="utf-8"),
                ensure_ascii=False, indent=2)


def ping_user_whatsapp(message):
    """WhatsApp ist verbunden (num=4915237977826, LID=...@lid).
    Alert ueber Hermes Gateway. Gibt True zurueck wenn gesendet."""
    # Hinweis: Dieser Skeleton ruft das Hermes-Alert ueber den
    # Messenger-Channel; im Cron-Lauf (no_agent) wird die Nachricht
    # direkt als stdout geliefert und vom Cron an WhatsApp gesendet.
    print(f"[ALERT][WhatsApp] {message}")
    return True


if __name__ == "__main__":
    print("[Scanner] ADR-0034: read-only public scan (autorisiert 2026-07-23)")
    print("[Scanner] KEINE Account-Erstellung, KEINE fake Accounts, KEINE Kaeufe.\n")
    queries = ["vintage wecker", "macbook pro 2019", "nintendo switch oled"]
    for q in queries:
        r = scan_kleinanzeigen(q)
        if "error" in r:
            print(f"  [{q}] FEHLER: {r['error']}")
            continue
        save(RESULTS, r)
        deals = detect_deals(r)
        print(f"  [{q}] {r['offers_found']} Angebote, "
              f"Median {sorted(r['prices'])[len(r['prices'])//2] if r['prices'] else 0}€, "
              f"{len(deals)} Deal-Kandidaten")
        if deals:
            msg = (f"Preis-Treffer bei '{q}': {len(deals)} verd. tief "
                   f"(ab {deals[0]['price_eur']}€ vs Median "
                   f"{deals[0]['median_eur']}€). Manuell pruefen: {r['url']}")
            ping_user_whatsapp(msg)
            save(ALERTS, {"query": q, "deals": deals, "url": r["url"],
                              "alerted_at": datetime.now(timezone.utc).isoformat()})
        time.sleep(2)  # polite: 2s zwischen Requests
    print("\n[Scanner] Ergebnisse in scan_results.json, Alerts in scan_alerts.json.")
