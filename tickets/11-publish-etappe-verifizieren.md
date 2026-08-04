# Ticket 11 — Landet ein erzeugtes Deliverable wirklich live?

Typ: `wayfinder:task` (**AFK**)
Status: **CLOSED** 2026-08-04 (MEASURED)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)
Verwandt: [Ticket 4 — IndexNow](4-indexnow-indexierung.md) (gleiche Defektklasse)

## Question

Die Zustellkette endet mit: `auto_fulfill` schreibt `dl/rtd/<hash>.html`,
committet, pusht — GitHub Pages liefert die Seite aus, `thanks.html` findet sie.

Die **letzte Etappe war nie gemessen**. Beleg dafuer: `dl/rtd/` war lokal leer
*und* im Git-Tree leer (`git ls-tree -r origin/gh-pages dl/rtd/` = 0 Eintraege).
Es hat also noch nie ein Deliverable diesen Weg genommen. Der bisherige
Wirksamkeitsnachweis war `auto_fulfill --selftest` — der laeuft aber mit
`push=False` und ueberspringt damit **genau** die fragliche Etappe.

Warum das gefaehrlich ist: Es ist dieselbe Defektklasse, die IndexNow 11 Tage
gekostet hat (Commit landete auf `master` unter `docs/`, Pages liefert aber den
`gh-pages`-ROOT). Nur sitzt dieser Defekt zwischen **„Kunde hat bezahlt"** und
**„Kunde bekommt Ware"** — er wuerde beim allerersten Sale zuschlagen: Geld
kassiert, Deliverable 404, Kunde pollt endlos.

Zusatzfrage: `thanks.html` pollt mit **HEAD**, nicht mit GET
(`fetch(url, {method:'HEAD'})`, Zeile 43). Ein reiner GET-Test wuerde den
Kundenpfad also **nicht** beweisen.

## Answer (MEASURED 2026-08-04)

**PUBLISH_LEG_OK** — die Etappe funktioniert. Neu:
`scripts/request_delivery/verify_publish_leg.py` fuehrt einen Canary durch die
**echten Produktivfunktionen** (`write_page`/`git_publish`), nicht durch eine
Nachbildung. Kein Stripe-Call, keine `sales.log`-Zeile, kein State-Eintrag.

```
branch            = gh-pages
geschrieben       = dl/rtd/f4a8db7f7ab8d7d0.html (1029 B)
vor dem Push      = HTTP 404 (404 erwartet)   <- Messung gegen Altstand abgesichert
git_publish()     = True | HEAD: a0b4b80
unpushed commits  = 0
im origin-Tree    = dl/rtd/f4a8db7f7ab8d7d0.html
LIVE GET          = HTTP 200 nach 31s
LIVE HEAD         = HTTP 200                  <- das pollt thanks.html
nach Cleanup      = HTTP 404 nach 31s
```

Vier Dinge, die dieser Test bewusst einzeln prueft (jedes war eine eigene
Ausfallmoeglichkeit):

1. **404 vor dem Push** — sonst misst man einen Altstand und haelt ihn fuer
   einen Erfolg.
2. **`origin/gh-pages..HEAD` = 0** — der Commit ist wirklich auf dem Remote,
   nicht nur lokal (die IndexNow-Falle war genau das).
3. **Datei im `origin/gh-pages`-Tree** — richtiger Branch *und* richtiger Pfad.
4. **HEAD getrennt von GET** — weil der Kunde ueber HEAD bedient wird.

Nebenbefunde (statisch geprueft, alle unauffaellig):
- `dl/rtd/` ist **nicht** gitignored (`git check-ignore` rc=1) — ein
  `.gitignore`-Eintrag haette `git add dl/rtd` still scheitern lassen.
- `gh-pages` trackt `origin/gh-pages`, d.h. `git push` ohne Argumente in
  `git_publish()` zielt korrekt.
- `ROOT`/`DL_DIR`/`SITE` in `auto_fulfill.py` zeigen auf Repo-Root,
  `dl/rtd` und `translucentv1.github.io/new-business`.

**Pages-Rebuild dauert ~31 s** (zweimal gemessen: Aufbau 31 s, Abbau 31 s).
Das deckt sich mit der Merkregel „~30-45 s" und bestaetigt, dass
`wait_live(tries=18, pause=10)` in `auto_fulfill.py` (bis zu 180 s) reichlich
Reserve hat.

## Konsequenz

Der Geldpfad ist jetzt auf **ganzer Laenge** gemessen: Kaufseite live →
Payment Link live/active mit echtem Preis → Redirect → Hash-Paritaet JS/Python
→ Generierung (Ollama) → **Publizierung (dieses Ticket)** → Abruf per HEAD.
Beim ersten echten Sale ist keine ungemessene Etappe mehr im Weg.

Was das Ticket **nicht** zeigt: dass jemand kauft. `BESUCHER = 0` bleibt
unveraendert — das ist eine Traffic-Frage (Ticket 3/5/10), kein Defekt.
