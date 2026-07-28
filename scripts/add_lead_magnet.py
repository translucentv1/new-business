#!/usr/bin/env python3
"""Inject a Free-Lead-Magnet CTA box into every book landing page (index.html),
idempotently. Mirrors the existing RTD crosslink approach so it never conflicts
with the page generator. Run: python3 scripts/add_lead_magnet.py
"""
import os, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTA = ('<p id="lead-magnet" style="margin-top:1.5em;padding-top:1em;'
       'border-top:1px solid #eee;font-size:.9rem">'
       'Gratis KI-Schreiber &rarr; <a href="/new-business/lead_magnet.html">'
       'Texte &amp; Briefe sofort generieren</a>, oder ein '
       '<a href="/new-business/rtd.html">individuelles Deliverable anfragen</a>.</p>')

MARKER = 'id="lead-magnet"'
pages = glob.glob(os.path.join(ROOT, '**', 'index.html'), recursive=True)

added = 0
for p in pages:
    html = open(p, encoding='utf-8').read()
    if MARKER in html:
        continue
    # Insert before </body> if present, else append.
    if '</body>' in html:
        html = html.replace('</body>', CTA + '\n</body>', 1)
    else:
        html = html + '\n' + CTA
    open(p, 'w', encoding='utf-8').write(html)
    added += 1

print(f"DONE: {added} Seiten mit Lead-Magnet-CTA ergaenzt (von {len(pages)} gesamt).")
