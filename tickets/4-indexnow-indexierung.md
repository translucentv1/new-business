# Ticket 4 — IndexNow-Indexierung (autonomer Traffic-Hebel)

Typ: `wayfinder:task` (AFK — vollstaendig ohne Nutzer machbar)
Status: **CLOSED** (2026-08-04)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

Ticket 2 (Autonomer Traffic) kam zum Schluss: "Hermes kann OHNE Nutzer-Account
keinen Traffic erzeugen". Stimmt das ausnahmslos? Gibt es einen legalen,
kostenlosen Indexierungs-Hebel ganz OHNE Login/Account?

## Answer (MEASURED 2026-08-04)

**Nein, die Aussage war zu absolut.** Es gibt genau einen: **IndexNow**
(Bing/Yandex/Seznam/Naver) — kein Login, kein Provider-API-Key, kein Account,
ToS-konform. Google bleibt ausgeschlossen (`/ping` ist tot, Search Console
braucht Nutzer-Login) — das Teilurteil von Ticket 2 gilt nur fuer Google.

**Dabei ein echter Defekt gefunden (frueherer Claim GEGENBEWIESEN):**
Commit `b8f2840` ("seo: add IndexNow key + verification file") legte die
Key-Datei nach `docs/49bf6b5c07acd9038ee05981c1810baa.txt` — und zwar auf
Branch **master**. GitHub Pages liefert aber den **gh-pages-ROOT**.

MEASURED-Beleg der Fehlfunktion (vor dem Fix):
```
https://.../new-business/49bf6b5c07acd9038ee05981c1810baa.txt      -> HTTP 404
https://.../new-business/docs/49bf6b5c07acd9038ee05981c1810baa.txt -> HTTP 404
git ls-tree -r HEAD | grep 49bf6b5c   -> (leer, nicht auf gh-pages)
git branch --contains b8f2840         -> master
```
=> IndexNow war seit dem 24.07. **nie funktionsfaehig**. Der Claim
"IndexNow key added for Bing/Yandex indexing" war ASSUMED, nicht MEASURED.

**Fix + Beleg (nach Commit `034e395`):**
```
Key-Datei gh-pages-ROOT, 32 Bytes, kein Newline (xxd verifiziert)
GET key.txt  -> HTTP 200 body='49bf6b5c07acd9038ee05981c1810baa'
POST api.indexnow.org/indexnow  10 URLs   -> HTTP 202 Accepted
POST api.indexnow.org/indexnow  1205 URLs -> HTTP 200
[sitemap] 1205 URLs gelesen, 1205 im Scope (0 verworfen)
Geldseite enthalten: <loc>.../new-business/rtd.html</loc>
```

**Scope-Regel beachtet:** Laut IndexNow-Spezifikation autorisiert eine
Key-Datei nur URLs unterhalb ihres eigenen Pfads. Key liegt live unter
`/new-business/` — genau unser URL-Raum. `/dl/` wird vom Skript gefiltert
(robots.txt disallow, ADR-0013).

## Assets
- `scripts/indexnow_submit.py` (`--check` = nur Key-Pruefung, `--limit N`, sonst voll)
- `49bf6b5c07acd9038ee05981c1810baa.txt` (gh-pages-ROOT, oeffentlich by design)

## Was das NICHT beweist
202/200 heisst **angenommen**, nicht **indexiert**. Ob Bing die 1205 URLs
tatsaechlich aufnimmt, ist erst in Tagen messbar → Folgeticket 5.
