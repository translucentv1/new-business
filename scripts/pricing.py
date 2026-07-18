"""Zentrale Preis-/Gebühren-Konstanten (ADR-0006).
MEASURED gumroad.com/pricing 2026-07-18: Direktverkauf 10% + $0.50 fix pro Transaktion.
Merchant of Record -> USt von Gumroad gehandhabt (nicht hier modelliert).
"""

# Startpreis in Cent (USD). ADR-0006: $3,99 fest.
PD_PRICE_CENTS_DEFAULT = 399

# Gumroad-Direktverkauf-Gebühr (MEASURED).
GUMROAD_PCT = 0.10          # 10%
GUMROAD_FIXED_CENTS = 50    # $0.50 fix


def net_cents(price_cents: int) -> int:
    """Netto-Erlös nach Gumroad-Direktgebühr (10% + 50c). Free ($0) = 0 Gebühr."""
    if price_cents <= 0:
        return 0
    fee = round(price_cents * GUMROAD_PCT) + GUMROAD_FIXED_CENTS
    return max(0, price_cents - fee)


def net_margin_pct(price_cents: int) -> float:
    """Netto-Marge als Anteil (0..1)."""
    if price_cents <= 0:
        return 0.0
    return net_cents(price_cents) / price_cents


def get_price_cents() -> int:
    """Preis aus Env (PD_PRICE_CENTS) oder Default 399."""
    import os
    try:
        return int(os.environ.get("PD_PRICE_CENTS", PD_PRICE_CENTS_DEFAULT))
    except ValueError:
        return PD_PRICE_CENTS_DEFAULT
