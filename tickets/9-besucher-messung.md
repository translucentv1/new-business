# Ticket 9 — Gibt es ein account-freies Instrument, das Besucher misst?

Typ: `wayfinder:research` (AFK)
Status: **CLOSED** (2026-08-04)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

Das Map fuehrt „0 Visitors auf 1300 Seiten" als **harten Fakt** und leitet daraus
die gesamte Strategie ab („Hebel = Traffic"). Zugleich warten drei Fog-Patches
(Keywords, Conversion, Micro-Preis) ausdruecklich auf „Besucher > 0".

Frage: **Womit** wurde „0 Visitors" eigentlich gemessen — und existiert ueberhaupt
ein Instrument, das Besucher sichtbar machen wuerde, ohne Account, ohne Cookies
und ohne die gerade gebaute Datenschutzerklaerung zu entwerten?

## Befund 1 — der „harte Fakt" war ASSUMED

MEASURED gegen die Live-Seite:

```
curl -s .../rtd.html | grep -oiE '(src|href)="https?://[^"]+"' | sort -u
  -> href="https://translucentv1.github.io/new-business/rtd.html"   (nur self)
curl -s .../thanks.html | ... -> (leer)
Analytics-Marker (analytics|gtag|plausible|matomo|goatcounter|beacon|counter): 0
```

Auf dem Kaufpfad liegt **keine einzige** Fremdressource und kein Zaehler.
Es gab also nie ein Instrument. „0 Visitors" war nicht gemessen, sondern
**die Abwesenheit einer Messung** — logisch nicht unterscheidbar von
„Besucher da, aber keiner kauft". Das Map hat eine Nicht-Messung als Fakt gefuehrt.

## Befund 2 — ein Instrument existiert bereits, ungenutzt

Hypothese: Legt das blosse Oeffnen eines Stripe Payment Links schon eine
`checkout.session` an? Dann waere die Session-Liste ein kostenloser Zaehler.

Zwei Messungen, gleicher Link (`buy.stripe.com/fZudR9fk59v5g7wfRF6c00T`, Basis 3,99 €):

| Zugriff | Ergebnis |
|---|---|
| `curl` GET (ohne JS), 12:59:33Z, HTTP 200, 535843 B | `sessions_total=1` — **keine** neue Session |
| echter Browser (JS bootet), 13:00:08Z | `sessions_total=2` — **neue Session**, `payment_link=plink_1TzrLTFajs0YddhPHUo9v1Ak`, `399 eur`, `unpaid` |

**Antwort: JA.** Ein echter Browser-Aufruf erzeugt sofort eine Session — vor
jeder Eingabe, vor jeder Zahlung. Ein Bot/curl-Aufruf ohne JS nicht.
Nebenbefund: die Kaufseite selbst wurde damit erstmals **im echten Browser**
verifiziert (Titel „RTD Basis (Request-to-Delivery)", 3,99 €, Pflichtfeld
„Deine Anfrage", Karte/Klarna/Amazon Pay/EPS) — bisher war sie nur per API geprueft.

## Trennscharfes Merkmal (wichtig gegen Fehlalarme)

```
session.payment_link = "plink_..."  -> echter Browser hat die Kaufseite geoeffnet
session.payment_link = None         -> von uns per API erzeugte Probe (Ticket 7)
```

Dieser Tick begann mit `sessions=1` (vorher immer 0) — das sah nach dem ersten
Besucher aus. Es war die eigene Ticket-7-Probe (`payment_link=None`, Feld
`widerruf`). **Ohne dieses Merkmal waere daraus ein falscher „erster Traffic"-
Claim geworden.**

## Ergebnis / Artefakt

- `scripts/request_delivery/funnel_check.py` (NEU) — zaehlt BESUCHER / API-PROBE /
  EIGENTEST getrennt, rechnet Conversion, kann eigene Tests per `--expire-own`
  schliessen. Eigene Session-Ids in `funnel_own_sessions.json`.
- `scripts/request_delivery/inspect_sessions.py` (NEU) — Rohansicht aller Sessions.
- `auto_fulfill.py`: Ausgabe praezisiert zu `sessions=N (roh, inkl. Eigentests)`,
  damit kein spaeterer Tick die Zahl als Traffic liest. Logik unveraendert,
  `--selftest` gruen, Live-Lauf gruen.

Erster Lauf (MEASURED 2026-08-04):

```
sessions_roh = 2 | BESUCHER = 0 | API-PROBE = 0 | EIGENTEST = 2 | bezahlt = 0
Conversion = n/a (kein einziger Browser hat die Kaufseite geoeffnet)
```

**Damit ist „niemand erreicht den Kaufbutton" erstmals belegt statt vermutet.**

## Grenzen (ehrlich)

- Gezaehlt wird die Stufe **„Kaufseite geoeffnet"**, nicht Seitenaufrufe auf
  `rtd.html`. Wer rtd.html liest und nicht klickt, bleibt unsichtbar → Ticket 10.
- Die **Retention** der Stripe-Session-Liste ist UNGEMESSEN. Der Zaehler ist ein
  Live-Signal, kein Archiv. Wer Historie will, muss pro Tick protokollieren.
- Kosten: 0 €, kein Account, keine Cookies, keine neue Fremdressource auf der
  Seite → `datenschutz.html` bleibt korrekt (Stripe ist als Zahlungsdienstleister
  ohnehin schon Teil der Kette).
