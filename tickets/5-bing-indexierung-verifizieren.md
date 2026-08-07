# Ticket 5 — Bing-Indexierung verifizieren (Wirkungsnachweis IndexNow)

Typ: `wayfinder:task` (AFK)
Status: **CLOSED 2026-08-07** — Zeitsperre gefallen, abgearbeitet
Blockiert durch: [Ticket 4 — IndexNow-Indexierung](4-indexnow-indexierung.md) (CLOSED)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

IndexNow hat die 1205 URLs am 2026-08-04 angenommen (HTTP 202/200 MEASURED).
**Angenommen ≠ indexiert.** Nimmt Bing die Seiten tatsaechlich in den Index —
und kommt daraus messbarer Traffic auf `rtd.html`?

## Antwort (2026-08-07, MEASURED)

**Nein — nicht indexiert, und 0 Traffic.** Wichtiger als das Ergebnis ist aber,
dass die im Ticket vorgeschriebene Messmethode **nicht durchfuehrbar** war und
beinahe eine Strategieentscheidung auf ein blindes Instrument gestuetzt haette.

### 1. Die vorgeschriebene Methode ist von hier aus BLIND

Das Ticket sagte: „Bing-Suche ohne Account abfragen und Treffer zaehlen.
0 Treffer = noch nicht indexiert." Genau das wurde versucht — mit einer
**Positivkontrolle** (`site:wikipedia.org`, zweifelsfrei indexiert). Alle drei
Wege liefern HTTP 200 und sehen nach einer Messung aus:

| Weg | Kontrolle `site:wikipedia.org` | Urteil |
|---|---|---|
| `bing.com/search` via curl | 74 933 B, **0** parsebare Treffer | blind (JS-Huelle) |
| `bing.com/search` im **echten Browser** | DOM: `b_algo=0`, `<li>=0`, `cite=0` | blind (Bot-Erkennung) |
| `bing.com/search?format=rss` | 10 Items — **alle auf amazon.fr** | schlimmer als blind |

Der RSS-Fall ist der gefaehrlichste: er liefert brav 10 Ergebnisse und
**ignoriert den `site:`-Operator komplett**. Fuer die eigene Domain lieferte er
ebenfalls 10 Items (Datenbank-Optimierungs-Blogs) — ein Tick ohne Kontrolle
haette daraus „indexiert!" gelesen. Die einzigen zwei `translucentv1`-Links
darin waren Bings **Selbstverweise** auf die Suchanfrage.

Ohne Positivkontrolle waere „0 Treffer" notiert und laut der
Entscheidungsregel dieses Tickets „IndexNow abschreiben" gefolgert worden.

### 2. Brauchbares Instrument gefunden (login-frei, 0 €)

`html.duckduckgo.com/html/` ist auswertbar. Laut DDGs eigener Hilfeseite
(**Primaerquelle frisch abgerufen, HTTP 200**, nicht aus dem Gedaechtnis):
„we have more traditional links and images in our search results too, which we
**largely source from Bing**". Also ein starker Proxy — `largely` ist aber
nicht `ausschliesslich`, das bleibt die ehrliche Grenze dieser Messung.

### 3. Die Messung

Konservierte Antworten von 2026-08-07, beide HTTP 200, durch die **echte**
`main()` von `bing_index_check.py` gefahren — reproduzierbar im Repo:
`python evidence/ticket5/replay.py` (ersetzt nur die Netzschicht, baut keinen
Parser nach; dekodiert mit `errors="replace"` exakt wie `real_fetch()`).

```
konserviert control   35160 B  sha256=892d31524fd72242  (34545 Zeichen nach Decode)
konserviert target     9611 B  sha256=37ade6a6f390ee2f  (9611 Zeichen nach Decode)
[ddg_html_replay] Kontrolle OK: 10 Treffer auf wikipedia.org (10 Ergebnis-URLs)
[ddg_html_replay] ZIEL: 0 Treffer auf translucentv1.github.io (explizite Leermeldung)
ERGEBNIS: BING_NICHT_INDEXIERT   (rc=1)
```

Die Leermeldung ist woertlich und unmissverstaendlich:
`<h1>No results found for <strong>site:translucentv1.github.io/new-business</strong></h1>`
(CSS-Klasse `result--no-result`). Das Instrument ist im selben Lauf beim
**Hochzaehlen beobachtet worden** (10 > 0) — die Null ist damit gemessen, nicht
unbelegt.

Traffic-Seite unveraendert: `funnel_check.py` meldet **BESUCHER = 0**
(vollzaehlig=ja) — es gibt keinen Suchtraffic, der ankommen koennte.

### 4. Neues stehendes Instrument

`scripts/request_delivery/bing_index_check.py`, gebaut nach den Merkregeln des
Maps:

- **Kontrolle zuerst.** Sieht die Kontrolle nichts, wird die Quelle verworfen —
  das Ergebnis ist dann `BING_UNGEPRUEFT`, **nie** „nicht indexiert".
- Drittes Ergebniswort: `BING_INDEXIERT` (rc=0) / `BING_NICHT_INDEXIERT` (rc=1) /
  `BING_UNGEPRUEFT` (rc=2).
- Leere Quellenliste ist **nicht** gruen (Leere-Schleife-Falle).
- Ergebniswort wird exakt verglichen, Rot-Faelle gegen die exakte Diagnosezeile.
- `--selftest` **18/18 SELFTEST_OK** mit Fault Injection durch die echte
  `main()`; der Kernfall („blinde Kontrolle darf niemals rc=1 ergeben") ist
  eigens getestet, ebenso die RSS-Fremdhost-Falle, HTTP 202, Netzfehler und
  „Ziel unverstanden".

Der echte Live-Lauf direkt nach den Sondierungen meldete korrekt
`BING_UNGEPRUEFT` (DDG antwortete nach den vielen Proben mit HTTP 202
`anomaly`) — das Instrument verweigert die Aussage, statt eine Null zu
erfinden. Genau so soll es sich verhalten.

## Entscheidung, die daran hing

Die Ticket-Regel lautet: „**nach ~14 Tagen** weiterhin 0 Treffer → IndexNow als
Hebel abschreiben". Die erste *wirksame* Einreichung war der 2026-08-04 (davor
lag der Key auf dem falschen Branch), die vollzaehlige 1220-URL-Einreichung der
2026-08-05. Heute ist **Tag 3**. Die Abschreib-Regel ist also **noch nicht
faellig** — 0 Treffer nach 3 Tagen ist der Normalfall, kein Befund.

→ Kein Strategiewechsel heute. Nachfolge-Ticket mit hartem Datum:
[Ticket 26 — IndexNow-Wirkung entscheiden](26-indexnow-wirkung-entscheiden.md),
faellig **2026-08-18**.

## Ehrliche Grenzen

- Gemessen ist der **DDG-Index**, nicht Bings Index direkt. Bing ist von dieser
  Umgebung aus nachweislich nicht messbar.
- Ein einzelner Messzeitpunkt. Der Zaehler ist eine **Untergrenze**.
- Ungeprueft blieb, ob die uebergeordnete Domain `translucentv1.github.io`
  ueberhaupt indexiert ist (Abfrage lief in den Ratelimit) — das trennt „unser
  Unterverzeichnis fehlt" von „die ganze github.io-Adresse fehlt" und gehoert
  in Ticket 26.
