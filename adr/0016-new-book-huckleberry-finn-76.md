# ADR-0016: Neues PD-Buch "Adventures of Huckleberry Finn" (Gutenberg 76)

**Status:** implemented, live (2026-07-18, Nachtschicht-Durchgang)
**Vorgänger:** ADR-0013 (Download-Gate), ADR-0014/0015 (Bücher 98/1260)
**Workflow:** GRILL -> SPEC (implizit) -> TICKETS (TB-16) -> IMPLEMENT

## Kontext / GRILL (selbst, autonom)
Ziel der Nachtschicht: erster Sale. Alle Bausteine (TB-8..12,14,15) sind done;
einziger offener Punkt TB-13 (korruptes 25913, USER-Entscheidung). Neue
Initiative nur via GRILL erlaubt.

- **Bringt das messbar einen Sale näher?** Indirekt: mehr indexierte
  Long-Tail-Landingpages = mehr SEO-Oberfläche (einzig erlaubter Traffic-Kanal).
  Nicht sofort messbar, aber der einzige autonome Hebel auf Traffic-Seite.
- **Beleg (MEASURED)?** Buch 76 = "Adventures of Huckleberry Finn", Mark Twain,
  Gutenberg #76; **41.931 Downloads / 30 Tage** (gutenberg.org, 2026-07-18) ->
  hohe Nachfrage, starkes Long-Tail-Keyword. PD in USA.
- **Ehrliches Loch?** 0 Sales bei 10 Büchern -> Inventarzahl ist evtl. nicht der
  Flaschenhals (eher Ranking-Zeit). Trotzdem sanktioniert (Handoff: "mehr
  PD-Bücher" explizit erlaubt) und folgt bewährtem TB-14/15-Pfad.
- **Hard Stop?** NEIN. Kein Account/Key neu; Stripe-Key lokal vorhanden
  (ADR-0013), Link wurde eigenständig via API angelegt. Kein Geld/Social/OAuth.

## Entscheidung
Buch 76 als 11. Produkt aufnehmen: download -> clean -> preview -> deliverable
-> Stripe-Link -> publish -> live-check. Exakt bewährter Pipeline-Pfad.

**Abgelehnt:** Sherlock Holmes (Gutenberg 1661, 84.878 DL/30d, noch höhere
Nachfrage). Grund: `scripts/pd_processor.py::CHAPTER_RE` matcht NUR
chapter/kapitel/book/buch/teil/part — Sherlock-Kapitel stehen als "ADVENTURE I.
…", würden als **1 Kapitel** parsen und vom Publish wie das korrupte 25913
geskipt werden. Pipeline-Limit, eigener Ticket wert (CHAPTER_RE erweitern),
hier nicht autonom gefixt (Scope-Creep + braucht Regressionstest).

## MEASURED-Ergebnis (dieser Durchgang)
- Download: `corpus/76/text.txt` = 622.460 Bytes (Gutenberg 76, utf-8).
- `pd_processor.build_product('76')`: 85 Kapitel, 570.864 Zeichen.
- QA-Gate: `[Illustration]`=nein, `gutenberg-tm`/`project gutenberg`=nein,
  Kapitelzahl=85 (plausibel). OK.
- Stripe-Link (nur 76, bestehende 10 unberührt): `buy.stripe.com/3cIfZhgo9ePp5sSeNB6c00a`
  (in `stripe_links.json` gemerged, 11 Links gesamt).
- `publish_site.py`: gh-pages-Commit `2858c4a`, 5 Dateien (76/index.html neu,
  deliverable neu, index/sitemap/MAP geändert).
- LIVE (curl, nach CDN-Propagation):
  - `https://translucentv1.github.io/new-business/76/` -> HTTP 200, 5.339 B,
    enthält `buy.stripe.com/3cIfZhgo9ePp5sSeNB6c00a`.
  - `…/dl/e019a41d799c142b/adventures-of-huckleberry-finn.html` -> 610.466 B
    echter Inhalt.
  - `git ls-tree origin/gh-pages` bestätigt beide Blobs im veröffentlichten Branch.
- Tests: `test_download_gate.py` (11 Seiten/10 Deliverables, Skip 25913) und
  `test_pd_processor.py` (ALL TESTS PASS) grün.

## Risiko (offen, USER)
`25913` (korruptes Ovid-Bundle) ist weiterhin LIVE + kauffähig, weil ein stale
`docs/25913/index.html` lokal existiert und re-published wird. Schlimmer als
nur "korrupt": 25913 hat **kein Deliverable** -> Kauf -> 404-Download =
Geld-ohne-Ware (Refund-Risiko). TB-13 = USER-Entscheidung ("nur vermerken").
Autonom NICHT gelöscht (Hard Stop "Daten löschen" + reservierte Entscheidung).
USER muss: Bundle reparieren ODER `docs/25913/` + 25913-Stripe-Link entfernen.

## Out of Scope
- `CHAPTER_RE` für "ADVENTURE"/generische Kapitel (eigener Ticket + Test).
- 25913-Reparatur / -Entfernung (TB-13, USER).
- EPUB-Deliverable, interne Verlinkung (weitere Initiativen, grün signalisiert).
