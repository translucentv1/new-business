#!/usr/bin/env python3
"""Ticket 12 — MISST, ob die gekaufte Preisstufe die Lieferung veraendert.

Kein Stripe-Call, kein Push, kein State: ruft nur gen_deliverable() je Stufe
mit IDENTISCHER Anfrage auf und zaehlt Woerter. Vorher (2026-08-04) war das
Ergebnis fuer alle drei Stufen dasselbe (~290 Woerter), weil die Stufe die
Erzeugung gar nicht erreichte.

Bestanden = jede hoehere Stufe liefert nachweislich mehr als die darunter.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from gig_fulfill import gen_deliverable, TIER_SPEC  # noqa: E402

REQ = ("Schreibe eine Produktbeschreibung fuer einen ergonomischen Buerostuhl "
       "fuer meinen Onlineshop.")


def main():
    print("== Ticket 12: Tier-Differenzierung MESSEN ==")
    print(f"Anfrage (identisch fuer alle Stufen): {REQ}\n")
    res = {}
    for cents in (399, 799, 1499):
        spec = TIER_SPEC[cents]
        t0 = time.time()
        text, err = gen_deliverable(REQ, tier=cents)
        dt = time.time() - t0
        w = len((text or "").split())
        res[cents] = w
        print(f"{spec['name']:9s} {cents:5d} cent  ziel~{spec['words']:5d} "
              f"-> woerter={w:5d} bytes={len(text or ''):6d} "
              f"zeit={dt:5.0f}s err={err}")
        if err:
            print("FEHLGESCHLAGEN: Erzeugung lieferte einen Fehler.")
            return 1

    print()
    ok = res[399] < res[799] < res[1499]
    print(f"Basis {res[399]} < Standard {res[799]} < Premium {res[1499]} -> "
          f"{'DIFFERENZIERT' if ok else 'NICHT DIFFERENZIERT'}")
    print(f"Faktor Premium/Basis = {res[1499] / max(res[399], 1):.2f}x "
          f"(vor dem Fix: 1.00x, identischer Prompt)")
    print("TIER_DIFF_OK" if ok else "TIER_DIFF_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
