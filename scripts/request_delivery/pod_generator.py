"""
POD Design Generator (ADR-0035 / GELD_STACKING #2).

Takes a book title / theme and produces:
  1. A print-ready design brief (text prompt for image gen)
  2. A Shirtee product payload (REST, no SDK) — creates a product on Shirtee
     when SHIRTEE_API_KEY is present; otherwise returns a DEMO payload so the
     pipeline is exercisable without credentials.

Shirtee API reference (public): https://api.shirtee.com  (REST, Bearer token)
Product creation: POST /v1/product   (simplified; adapt to live spec)

NO hardcoded keys. Key comes from env SHIRTEE_API_KEY only.
"""
import os
import json
import urllib.request
import urllib.error

SHIRTEE_BASE = "https://api.shirtee.com/v1"
API_KEY = os.environ.get("SHIRTEE_API_KEY")


def design_brief(title: str, theme: str = "") -> dict:
    """Return a design brief (prompt + specs) for a POD product."""
    clean = title.strip()
    prompt = (
        f"Minimalist book-themed t-shirt design for '{clean}'. "
        f"Typography-focused, elegant, monochrome or 2-tone, "
        f"centered title text, subtle decorative element. "
        f"No copyrighted logos. Theme: {theme or 'literature'}."
    )
    return {
        "title": clean,
        "theme": theme,
        "image_prompt": prompt,
        "specs": {
            "product": "tshirt-classic",
            "colors": ["black", "white", "navy"],
            "print_area": "front-center",
            "mockup": True,
        },
        "price_eur": 19.99,
    }


def create_shirtee_product(brief: dict) -> tuple[str, bool]:
    """
    Create a Shirtee product from a brief.
    Returns (url_or_payload, demo_flag).
    DEMO if no API key (no network call).
    """
    if not API_KEY:
        demo = {
            "demo": True,
            "note": "No SHIRTEE_API_KEY set — DEMO payload. Add key to create real product.",
            "product": {
                "name": brief["title"],
                "design_prompt": brief["image_prompt"],
                "price": brief["price_eur"],
            },
        }
        return json.dumps(demo, ensure_ascii=False), True

    payload = {
        "name": brief["title"],
        "description": brief["image_prompt"],
        "products": [{
            "productType": brief["specs"]["product"],
            "colors": brief["specs"]["colors"],
        }],
        "price": int(brief["price_eur"] * 100),
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{SHIRTEE_BASE}/product",
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        return data.get("url") or json.dumps(data, ensure_ascii=False), False
    except urllib.error.HTTPError as e:
        return f"SHIRTEE_ERR:{e.read().decode()[:200]}", False
    except Exception as e:
        return f"SHIRTEE_CONN_ERR:{e}", False


def generate(title: str, theme: str = "") -> dict:
    """Full pipeline: brief -> (product_url, demo)."""
    brief = design_brief(title, theme)
    url, demo = create_shirtee_product(brief)
    return {"brief": brief, "result": url, "demo": demo}


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "Alice's Adventures in Wonderland"
    th = sys.argv[2] if len(sys.argv) > 2 else "classic literature"
    out = generate(t, th)
    print(json.dumps(out, ensure_ascii=False, indent=2))
