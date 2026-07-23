"""
Business #2: eBay Reselling/Arbitrage — OFFIZIELLE eBay Seller API (compliant).

WICHTIG (ADR-0032): NUR offizielle eBay-APIs nutzen. KEIN Kleinanzeigen-Bot
(Browser-Automatisierung = ToS-Verletzung = Hard-Stop). eBay Developer Program
ist kostenlos für Basisfunktionen und ToS-konform.

Status: SKELETON. Wartet auf eBay-Seller-Account + App-Tokens vom Nutzer.
Kein Netzwerk-Call ohne Credentials.

Nächste Schritte (Nutzer):
1. eBay Developer Account erstellen (developer.ebay.com)
2. App erstellen → Client-ID / Client-Secret + OAuth-Token
3. Tokens in .ebay_secrets (gitignored) ablegen
4. Dann: list_item(), sync_inventory(), check_orders() aktivieren
"""
import os
import json
import urllib.request
import urllib.parse
import base64

EBAY_API = "https://api.ebay.com"
TOKEN_URL = f"{EBAY_API}/identity/v1/oauth2/token"
SELL_URL = f"{EBAY_API}/sell/inventory/v1"

SECRETS_FILE = os.path.join(os.path.dirname(__file__), "..", ".ebay_secrets")


def _load_secrets():
    if not os.path.exists(SECRETS_FILE):
        return None
    data = {}
    for line in open(SECRETS_FILE, encoding="utf-8"):
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.strip().split("=", 1)
            data[k.strip()] = v.strip()
    return data


def get_app_token():
    """Holt App-Token via client_credentials (nur zum Testen der API)."""
    s = _load_secrets()
    if not s or not s.get("EBAY_CLIENT_ID") or not s.get("EBAY_CLIENT_SECRET"):
        return None
    cred = base64.b64encode(
        f"{s['EBAY_CLIENT_ID']}:{s['EBAY_CLIENT_SECRET']}".encode()
    ).decode()
    body = urllib.parse.urlencode(
        {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Authorization": f"Basic {cred}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read()).get("access_token")
    except Exception as e:
        print(f"[eBay] Token-Fehler: {e}")
        return None


def list_item(token, title, price_eur, description, category_id):
    """Erstellt ein Listing via offizielle Inventory API (compliant)."""
    if not token:
        print("[eBay] Kein Token — Account/Credentials fehlen (ADR-0032 Block).")
        return None
    item = {
        "availability": {"shipToLocationAvailability": {"quantity": 1}},
        "product": {
            "title": title,
            "description": description,
            "price": {"value": str(price_eur), "currency": "EUR"},
        },
        "condition": "NEW",
    }
    req = urllib.request.Request(
        f"{SELL_URL}/inventoryItem/{{sku}}",
        data=json.dumps(item).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=15)
        return "OK (skeleton — nicht ausgeführt ohne echten Account)"
    except Exception as e:
        print(f"[eBay] List-Fehler: {e}")
        return None


if __name__ == "__main__":
    tok = get_app_token()
    if tok:
        print("eBay API erreichbar, Token geholt (Länge", len(tok), ")")
        print("Skeleton bereit — warte auf vollständige Credentials + Nutzer-Freigabe.")
    else:
        print("KEIN eBay-Token: Account/Credentials fehlen. (Blockiert laut ADR-0032)")
