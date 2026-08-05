# Ticket 16 — Kann der Torwaechter des Geldpfads rot werden?

**Typ:** `wayfinder:task` (AFK)
**Status:** GESCHLOSSEN 2026-08-05 — Antwort: NEIN, er konnte es nicht. Jetzt kann er es.
**Eltern:** wayfinder_map.md
**Blockiert durch:** nichts (Ticket 15 geschlossen)

## Question

`verify_rtd_chain.py` entscheidet mit `KETTE_OK`, ob der Geldpfad intakt ist —
jeder Tick zitiert dieses Wort als Beleg. Das Skript hat aber **keinen
`--selftest`** (MEASURED 2026-08-05, Ticket 15): niemand hat je gezeigt, dass es
einen kaputten Kaufpfad ueberhaupt **bemerkt**. Wuerde es rot, wenn ein Link
deaktiviert waere, der Preis auf 0 stuende, das Pflichtfeld `anfrage` fehlte
oder der Redirect auf eine tote Domain zeigte?

Gleiche Klasse wie Ticket 14 (Sitemap-Pruefer) und Ticket 15 (Besucher-Zaehler):
ein Pruefer, der nie rot werden kann, winkt einen kaputten Geldpfad durch.

## Warum das zaehlt

`KETTE_OK` ist die Aussage, auf die sich seit Wochen jeder Statusbericht
stuetzt. Sie deckt die **einzige Einnahmequelle** ab. Solange der Pruefer
ungeprueft ist, ist „der Kaufpfad ist intakt" streng genommen ASSUMED.

## Antwort (MEASURED 2026-08-05)

### 1. Zwei echte Defekte gefunden — nicht nur ein fehlender Test

**A) Blinder Gruen-Fall: 0 Links auf der Kaufseite ergaben `KETTE_OK`.**
Die alte `main()` startete mit `ok = True` und setzte `ok` ausschliesslich
*innerhalb* der Schleife ueber die gefundenen Links. Findet der Regex keinen
einzigen `buy.stripe.com`-Link (Verkaufsseite kaputt, Links versehentlich
geloescht, Markup umgebaut), laeuft die Schleife **null Mal** — und das Skript
meldet `KETTE_OK` fuer eine Kaufseite ohne Kaufmoeglichkeit.

Nicht theoretisch, sondern **am Alt-Stand ausgefuehrt** (`_mutation_probe_t16.py`
Teil A holt `ad891dc:scripts/request_delivery/verify_rtd_chain.py` per `git show`
und faehrt dessen echte `main()` gegen eine rtd.html ohne Links):

```
[OK ] Alt-Stand (ad891dc) mit 0 Links: rc=0, sagt KETTE_OK -> war BLIND
        | [1] rtd.html LIVE-Links gefunden: 0
        | [2] Stripe-Status je Link:
        | ERGEBNIS: KETTE_OK
```

**B) Schritt [3] „Hash-Paritaet" hat nie etwas gemessen.**
Der Abschnitt berechnete den Python-Hash und druckte dann den Satz
`-> Paritaet gegeben, da beide SHA-256/Lower-Hex/[:16] nutzen.` — eine
**Behauptung ueber `thanks.html`, ohne `thanks.html` auch nur zu oeffnen**.
Haette jemand das JS auf `slice(0,15)` oder SHA-1 geaendert, haette der
Torwaechter weiter „Paritaet gegeben" gedruckt, und der zahlende Kunde waere
auf eine 404 gepollt: `auto_fulfill` schreibt `dl/rtd/<python-hash>.html`,
der Browser fragt `dl/rtd/<js-hash>.html`.

### 2. Fix

- **Rot bei 0 Links** und zusaetzlich bei **Link-Anzahl != Preis-Optionen**
  (Soll-Zahl aus der Datei selbst abgeleitet: jede `<option value=…>`-Preisstufe
  braucht ihren Link — verliert ein Tier seinen Link, faellt das jetzt auf).
- **[3] misst wirklich:** die drei JS-Zeilen werden aus der ausgelieferten
  `thanks.html` **extrahiert und in node ausgefuehrt** (node v24.18.0 vorhanden),
  das Ergebnis mit `dl/rtd/{sid_hash(sid)}.html` verglichen. Kein Nachbau des
  Algorithmus — der echte Dateiinhalt laeuft.
- **Pagination** bei `payment_links` (Ticket-15-Defektklasse; ohne
  `has_more`-Auswertung waere ein Link ab Nr. 101 unsichtbar → Fehlalarm).
- **Drittes Ergebniswort `KETTE_UNGEPRUEFT` (rc=2)** fuer „nicht messbar"
  (z.B. node fehlt). Wichtig: eine fehlende Messmoeglichkeit darf weder als
  gruen durchgehen noch als Defekt-Claim ueber den Geldpfad auftreten.
- `amt > 0` zusaetzlich gegen `bool` abgesichert (`True` ist in Python ein int).
- `[4] dl/rtd`-Zaehlung ausdruecklich als **Information** markiert — sie war nie
  ein Gruen-Kriterium, las sich mit „(Fulfillment-Ziel vorhanden)" aber wie eines.

### 3. Beleg

`python scripts/request_delivery/verify_rtd_chain.py --selftest` → **16/16 SELFTEST_OK**.
Alle Rot-Faelle laufen durch die **echte** `main()` (injiziert werden nur
`get_key`/`stripe_get`/`read_text`/`run_node`) und werden zusaetzlich gegen
`Traceback` gefiltert — ein Absturz zaehlt nicht als Erkennung:

```
[OK ] gesund -> KETTE_OK, rc=0            [OK ] 0 Links auf rtd.html wird rot
[OK ] active=False wird rot               [OK ] Link-Anzahl != Preis-Optionen wird rot
[OK ] livemode=False wird rot             [OK ] Hash-Paritaet (slice 15) wird rot
[OK ] Preis 0 wird rot                    [OK ] Hash-Paritaet (SHA-1) wird rot
[OK ] fehlender Preis wird rot            [OK ] fehlende JS-Hashzeile wird rot
[OK ] fehlendes Pflichtfeld wird rot      [OK ] node fehlt -> KETTE_UNGEPRUEFT, rc=2
[OK ] falscher Redirect wird rot          [OK ] Pagination holt Seite 2 -> KETTE_OK
[OK ] verschwundener Link wird rot        [OK ] nach allen Rot-Faellen wieder KETTE_OK
```

`python scripts/request_delivery/_mutation_probe_t16.py` → **MUTATION_PROBE_OK**:
Alt-Stand-Probe gruen (siehe oben) plus **4/4 Mutanten rot** (leere Linkliste
durchwinken, Preis-Pruefung entschaerfen, Paritaet nur behaupten,
`livemode/active` ignorieren), kein `Traceback`, Datei per sha256
(`779737056bf8…`) bitgenau wiederhergestellt, rc-Wechsel 0→1→0 belegt.

Echter Lauf gegen LIVE-Stripe **nach** dem Umbau — die 3 LIVE-Links wurden
dabei nie angefasst (nur GET):

```
[1] rtd.html LIVE-Links gefunden: 3 (Preis-Optionen: 3)
[2] livemode=True active=True preis=399/799/1499 cent = 3.99/7.99/14.99 EUR
    fields=['anfrage']  redirect=…/thanks.html?sid={CHECKOUT_SESSION_ID} -> OK
[3] python -> dl/rtd/c4058a6e2eaf7e0c.html
    js     -> dl/rtd/c4058a6e2eaf7e0c.html   [OK]
ERGEBNIS: KETTE_OK
```

Lint (Hausstandard aus Ticket 15: `uvx ruff`, nur eigener Code): 9 → 4 Findings.
Die 4 verbliebenen sind Alt-Bestand bzw. bewusst (`re.M` wie im uebrigen Repo,
blindes `except` in der originalen line_items-Abfrage).

## Ehrliche Grenzen

- Der Selftest prueft gegen **injizierte** Stripe-Antworten. Dass die echte API
  bei einem echten Defekt genau diese Felder liefert, ist aus der Feldstruktur
  der Live-Antwort abgeleitet, nicht durch Kaputtmachen eines LIVE-Links bewiesen
  — und soll es auch nicht werden (einzige Einnahmequelle).
- Die Pagination ueber Seitengrenzen ist mit injizierten Seiten belegt; real
  existieren < 100 Payment Links, dort ist sie unbeobachtbar (wie Ticket 15).
- node fuehrt die JS-Zeilen aus, **nicht** der Browser. Getestet ist damit die
  Hash-Rechnung, nicht `fetch`/DOM in `thanks.html`.
- `KETTE_OK` sagt weiterhin nichts ueber Verkaufstext, Conversion oder ob
  ueberhaupt jemand die Seite sieht.

## Danach noch offen

`verify_ticket13_live.py` hat als **letztes** Verifikationsskript keinen
Selftest — geringere Tragweite (Rechtslinks, nicht Geldpfad), aber dieselbe
Klasse. → **Ticket 17**.
