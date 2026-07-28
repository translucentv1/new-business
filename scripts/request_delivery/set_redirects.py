#!/usr/bin/env python3
"""Setzt after_completion-Redirect der 3 RTD-Payment-Links auf
thanks.html?sid={CHECKOUT_SESSION_ID}, damit thanks.html das Deliverable
(dl/rtd/<sha256(sid)[:16]>.html, erzeugt von auto_fulfill.py) pollen kann."""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app  # noqa: E402

KEY = app.get_stripe_key()
TARGET = ("https://translucentv1.github.io/new-business/"
          "thanks.html?sid={CHECKOUT_SESSION_ID}")
RTD_LINKS = [
    "plink_1TxygrFajs0YddhPBMdosc9V",  # Basis 3,99
    "plink_1TxygsFajs0YddhPQTAK2ZmU",  # Standard 7,99
    "plink_1TxyguFajs0YddhPZoXdN5av",  # Premium 14,99
]

for pl in RTD_LINKS:
    data = urllib.parse.urlencode({
        "after_completion[type]": "redirect",
        "after_completion[redirect][url]": TARGET,
    }).encode()
    req = urllib.request.Request(
        "https://api.stripe.com/v1/payment_links/" + pl, data=data,
        headers={"Authorization": "Bearer " + KEY})
    r = json.load(urllib.request.urlopen(req, timeout=30))
    print(pl, "->", r["after_completion"]["redirect"]["url"])
