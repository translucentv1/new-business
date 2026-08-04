# Ticket 14 — Sitemap-Healthcheck härten (Prüfer prüfen)

Typ: `wayfinder:task` (AFK) · Status: **GESCHLOSSEN 2026-08-05**

## Question

Ist der Claim „alle Sitemap-URLs live HTTP 200, 0 Defekte" belastbar — oder
stützt er sich auf einen Prüfer, der gar nicht rot werden kann?

## Auslöser (MEASURED 2026-08-05)

Beim Live-Check dieses Ticks wurden zwei URLs geraten, die es nicht gibt.
Beide antworteten mit **HTTP 404 bei 9379 B Body** — die 404-Seite von GitHub
Pages ist *fetter* als jede echte Landingpage (2390–3683 B gemessen).

```
blog/trauerrede-schreiben-lassen.html      -> 404   (9379 B)
blog/speisekarte-erstellen-lassen.html     -> 404   (9379 B)
blog/DIESE-SEITE-GIBT-ES-NICHT.html        -> 404   (9379 B)
```

Konsequenz: **jede Größen-Heuristik hält ein 404 für eine gesunde Seite.**
Ein `curl | wc -c` als „ist live"-Beleg ist wertlos; nur der Statuscode zählt.
(Die geratenen Namen waren mein Fehler — die echten Seiten heißen
`trauerrede-schreiben-ki.html` / `speisekarte-erstellen-lassen-ki.html` und
sind live 200. Der Fehlgriff hat aber die Falle freigelegt.)

## Befund

`scripts/sitemap_healthcheck.py` war das **einzige** Verifikationsskript im Repo
**ohne `--selftest`** — und verletzte damit die eigene Konvention aus den
Map-Notes („Ein Prüfer, der nie rot werden kann, winkt einen kaputten Geldpfad
durch"). Sein Ergebnis „1207 URLs, 0 Defekte" vom 2026-08-04 war deshalb streng
genommen **ASSUMED**: niemand hatte je gezeigt, dass das Skript einen Defekt
überhaupt bemerkt.

Inhaltlich war es in Ordnung (es liest `r.status` bzw. fängt `HTTPError`,
prüft also echte Statuscodes und nicht Body-Größen) — aber „ist in Ordnung"
war eine Code-Lektüre, kein Test.

## Antwort

Der Claim **hält**, ist jetzt aber belegt statt gelesen.

`--selftest` mit Fault Injection ergänzt, der die **echte** `main()` mit
injizierter Sitemap fährt (Produktivpfad, keine Nachbildung):

```
== sitemap_healthcheck --selftest (Fault Injection) ==
  [OK ] status() liefert 200 fuer eine existierende Seite  (code=200)
  [OK ] status() liefert 404 fuer eine fehlende Seite  (code=404)
  [OK ] 404 wird NICHT ueber die Body-Groesse erkannt  (200-body=5378B)
  [OK ] Fault Injection: 404 in der Sitemap -> rc=1  (rc=1)
  [OK ] Fault Injection: meldet 'DEFEKT 404'
  [OK ] Fault Injection: meldet SITEMAP_DEFEKT
  [OK ] Rot-Fall ist kein Absturz (kein Traceback)
  [OK ] Gesunde Sitemap -> rc=0 (rc-Wechsel 1->0 belegt)  (rc=0)
  [OK ] Gruen-Fall meldet SITEMAP_OK
  [OK ] Gruen-Fall ist kein Absturz (kein Traceback)
  [OK ] Duenne Seite (12 B) wird als DUENN gemeldet
  [OK ] Duenne Seite allein macht NICHT rot (nur Hinweis)  (rc=0)
  [OK ] Netzfehler (-1) zaehlt als NICHT_200 -> rc=1  (rc=1)
ERGEBNIS: 13/13 SELFTEST_OK
```

Gegen die Exit-Code-Falle: bei jedem Rot-Fall wird zusätzlich die erwartete
Meldung geprüft und auf `Traceback` gefiltert — `rc=1` allein könnte ein
Absturz sein.

Vollzähliger Lauf danach, mit dem nun vertrauenswürdigen Instrument:

```
urls_gefunden=1216
HTTP_200=1216  NICHT_200=0  VERDAECHTIG_KLEIN(<500B)=0
ERGEBNIS: SITEMAP_OK        (21,8 s, rc=0)
```

## Nebenbefunde

- Sitemap lokal = live = **1216 URLs**, 0 Drift. Die 2 Landingpages des
  Traffic-Ticks von heute (`trauerrede-schreiben-ki`,
  `speisekarte-erstellen-lassen-ki`) sind in der Live-Sitemap **und** live
  HTTP 200 (2943 B / 3420 B) — der Traffic-Tick hat sauber publiziert, die
  „Generator-publiziert-nicht"-Falle aus Ticket 13 hat also gegriffen.
- Alle 4 jüngsten Traffic-Seiten tragen Datenschutz-Link und `rtd.html`-Link
  (je 1x live im Body gezählt).
- IndexNow nach dem Healthcheck: Key-Datei HTTP 200 (Body == Dateiname),
  **1216 URLs → HTTP 200, `SUBMIT_OK`**. Wie immer: *angenommen*, **nicht**
  indexiert. Wirkungsnachweis bleibt Ticket 5 (ab 2026-08-07).
- Geldpfad unangetastet: `verify_rtd_chain.py` → `KETTE_OK`
  (399/799/1499 cent = 3,99/7,99/14,99 EUR, Feld `anfrage`, Redirect ok).

## Ehrliche Grenze

Geprüft ist **Erreichbarkeit**, nicht Qualität oder Indexierbarkeit. 1216 mal
HTTP 200 sagt nichts darüber, ob Bing die Seiten aufnimmt oder ob sie
Suchvolumen haben. Und `SITEMAP_OK` ist eine Momentaufnahme: der Lauf müsste
nach jedem Traffic-Tick wiederholt werden, um Aussagekraft zu behalten.

## Nachtrag: eigener Claim abgeschwächt (Mutationsprobe)

Unabhängige Ad-hoc-Verifikation gegen einen **hermetischen lokalen HTTP-Server**
(andere Mechanik als der Monkeypatch-Selftest): **15/15 ADHOC_OK** gegen den
Produktivcode. Zwei Mutanten belegen, dass die Probe rot werden kann:

| Mutant | Ergebnis |
|---|---|
| `bad` size-driven statt status-driven | 14/15 ADHOC_FAIL |
| zusätzlich echte Fehler-Body-Größe erhalten | 10/15 ADHOC_FAIL |

**Der erste Mutant hat einen Denkfehler in meinem eigenen Test freigelegt.**
Der Fall „fettes 404 wird trotzdem erkannt" bestand gegen Mutant 1 — aber aus
dem falschen Grund: der Produktivcode gibt im `except HTTPError`-Zweig
`size=0` zurück und liest den Fehler-Body nie. Eine Größen-Heuristik fängt ein
404 deshalb *zufällig mit*. Erst Mutant 2 (Fehler-Body-Größe erhalten) bringt
den Fall zum Kippen: `HTTP_200=1  NICHT_200=0` — das 9000-B-404 wird als
gesunde Seite gezählt.

**Konsequenz für die Formulierung oben:** `sitemap_healthcheck.py` war durch
die Fette-404-Falle nie gefährdet, weil es Fehler-Bodies verwirft. Sein Mangel
war ausschließlich das fehlende Negativ-Kontroll. Gefährlich bleibt die Falle
dort, wo ein Body wirklich gemessen wird — also beim manuellen
`curl <url> | wc -c`, genau wo sie mich erwischt hat. Diese Unterscheidung
fehlte in der ersten Fassung dieses Tickets.

