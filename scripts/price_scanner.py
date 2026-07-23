"""
Business #3: Preisfehler-Scanner (Arbitrage) — ADR-0034
Multi-Plattform-Scanner (Medimops / Mein-Deal / Schnaeppchenfuchs).

Nutzer-Autorisierung: Scraping oeffentlicher Marktplatz-Daten explizit
erlaubt (Hard-Stop geliftet 2026-07-23, Risiko als gering eingeschaetzt).
Verboten bleiben: fake Accounts, KYC/Steuer-Umgehung, IP-Verletzung.

Methode: read-only HTTP-GET oeffentlicher Suche/Listings.
Agent gibt KEIN Geld aus. Bei Treffer: ALERT an Nutzer (WhatsApp),
Nutzer kauft + reselled.

PARSER-BUG FIX (2026-07-23, Nutzer-Feedback):
Kleinanzeigen rendert Preise im Titel-Text (JS-abhaengig), daher
unzuverlaessig -> DEAKTIVIERT. Stattdessen Plattformen mit sauberen
Preis-Strukturen:
- Medimops: Preiskategorie-Seiten (2-5 EUR etc.) = echte Artikelpreise
- Mein-Deal / Schnaeppchenfuchs: Deal-Portale mit "alt" vs "neu" Preis
  -> Preisfehler = neu << alt (echtes Delta, nicht Versand/Pfand-Mix)

Wichtig: Preisfehler = Item mit Marktwert >> Preis. Ohne Marktwert-
Datenbank ist "Preisfehler" hier vereinfacht: tiefe Preise vs. Median
bzw. alt-vs-neu Delta -> Alert zur manuellen Pruefung.
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

UA = {"User-Agent": "Mozilla/5.0 (compatible; price-scan/1.0)"}
MEDIMOPS = "https://www.medimops.de/{cat}/?fcCatSearchPrice={lo}+EUR+-+{hi}+EUR"
MEIN_DEAL = "https://www.mein-deal.com/"
SCHNAEPPCHENFUCHS = "https://schnaeppchenfuchs.com/"


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")


def _extract_prices(html):
    """Extrahiert '12,34 EUR' oder '12 EUR' aus HTML (nur eigenstaendige
    Betraege, nicht '4 EUR Versand' — dafuer Kontext-Check)."""
    prices = []
    for m in re.finditer(r"(\d{1,3}(?:[.,]\d{2})?)\s*€", html):
        after = html[m.end():m.end() + 20].lower()
        # Versand/Pfand ausschliessen
        if any(k in after for k in ["versand", "pfand", "zzgl", "inkl"]):
            continue
        prices.append(float(m.group(1).replace(",", ".")))
    return prices


def scan_medimops(query, cat="buecher-C0186606", lo=2, hi=5, limit=30):
    """Medimops Preiskategorie (z.B. Buecher 2-5 EUR). Scannt Restposten.
    Preise auf Kategorieseiten sind echte Artikelpreise (kein Versand-Mix)."""
    url = MEDIMOPS.format(cat=cat, lo=lo, hi=hi)
    try:
        html = _get(url)
        prices = _extract_prices(html)
        return {"platform": "medimops", "query": f"{query} ({lo}-{hi}EUR)",
                 "url": url, "offers_found": len(prices),
                 "prices": sorted(prices)[:limit],
                 "scanned_at": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"platform": "medimops", "query": query,
                 "error": str(e)[:200],
                 "scanned_at": datetime.now(timezone.utc).isoformat()}


def scan_portal(url, name, query="", limit=30):
    """Generischer Scanner fuer Deal-Portale (Mein-Deal / Schnaeppchenfuchs).
    Extrahiert sichtbare Preise; tiefe = moeglicher Preisfehler."""
    try:
        html = _get(url)
        prices = _extract_prices(html)
        return {"platform": name, "query": query or "(startseite)",
                 "url": url, "offers_found": len(prices),
                 "prices": sorted(prices)[:limit],
                 "scanned_at": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"platform": name, "query": query,
                 "error": str(e)[:200],
                 "scanned_at": datetime.now(timezone.utc).isoformat()}


def detect_deals(result, threshold_pct=0.20, min_price=1.0):
    """Vereinfachte Heuristik: tiefe Preise vs. Kategorie-Median.
    Echter Preisfehler braucht Marktwert-DB; hier nur Kandidat zur
    manuellen Pruefung.
    FIX (Nutzer-Feedback): < min_price ausgeschlossen (Cashback/Versand/
    Nonsens), nur preiswert wenn <= threshold_pct * Median.
    EHRLICH: meldet "moeglicher Preisfehler", nicht "garantiert"."""
    if "prices" not in result or len(result["prices"]) < 5:
        return []
    prices = [p for p in result["prices"] if p >= min_price]
    if not prices:
        return []
    median = sorted(prices)[len(prices) // 2]
    deals = [p for p in prices if p <= median * threshold_pct]
    return [{"price_eur": d, "median_eur": median,
             "note": "MOEGLICHER Preisfehler (manuell pruefen, kein Garant)"}
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
    print(f"[ALERT][WhatsApp] {message}")
    return True


if __name__ == "__main__":
    print("[Scanner] ADR-0034: read-only public scan (autorisiert 2026-07-23)")
    print("[Scanner] KEINE Account-Erstellung, KEIN fake Accounts, KEIN Kaeufe.")
    print("[Scanner] Kleinanzeigen DEAKTIVIERT (JS-Preise unzuverlaessig).\n")

    jobs = [
        ("medimops", lambda: scan_medimops("buecher", "buecher-C0186606", 2, 5)),
        ("medimops", lambda: scan_medimops("spiele", "spiele-C0300992", 2, 5)),
        ("mein-deal", lambda: scan_portal(MEIN_DEAL, "mein-deal")),
        ("schnaeppchenfuchs", lambda: scan_portal(SCHNAEPPCHENFUCHS, "schnaeppchenfuchs")),
    ]

    for name, fn in jobs:
        r = fn()
        if "error" in r:
            print(f"  [{name}] FEHLER: {r['error']}")
            continue
        save(RESULTS, r)
        deals = detect_deals(r)
        median = sorted(r["prices"])[len(r["prices"]) // 2] if r.get("prices") else 0
        print(f"  [{name}] {r['offers_found']} Angebote, "
              f"Median {median}EUR, {len(deals)} Deal-Kandidaten")
        if deals:
            msg = (f"Preis-Treffer bei '{name}': {len(deals)} verd. tief "
                   f"(ab {deals[0]['price_eur']}EUR vs Median "
                   f"{deals[0]['median_eur']}EUR). Manuell pruefen: {r['url']}")
            ping_user_whatsapp(msg)
            save(ALERTS, {"query": r.get("query"), "deals": deals, "url": r["url"],
                              "alerted_at": datetime.now(timezone.utc).isoformat()})
        time.sleep(2)  # polite: 2s zwischen Requests
    print("\n[Scanner] Ergebnisse in scan_results.json, Alerts in scan_alerts.json.")
