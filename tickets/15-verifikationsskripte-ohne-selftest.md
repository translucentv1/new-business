# Ticket 15 — Der Besucher-Zaehler war selbst ungeprueft

**Typ:** `wayfinder:task` (AFK)
**Status:** GESCHLOSSEN 2026-08-05
**Eltern:** wayfinder_map.md

## Question

Ticket 14 behauptete am 2026-08-04, `sitemap_healthcheck.py` sei das **einzige**
Verifikationsskript ohne `--selftest`. Haelt dieser Vollstaendigkeits-Claim einer
vollzaehligen Pruefung stand — oder ist er ein weiterer Fall der
Teil-Vollstaendigkeits-Falle aus Ticket 13?

## Antwort (MEASURED 2026-08-05)

**Der Claim ist GEGENBEWIESEN.** Vollzaehlig ueber alle 38 Skripte in `scripts/`
und `scripts/request_delivery/` gegrept: nach Ticket 14 hatten **4** Skripte
einen Selftest (`sitemap_healthcheck`, `verify.py`, `auto_fulfill`,
`legal_link_audit`, `verify_publish_leg`), und mindestens **drei
Verifikationsskripte hatten keinen**:

| Skript | Selftest vor diesem Ticket | Rolle |
|---|---|---|
| `funnel_check.py` | NEIN | **die einzige gueltige Traffic-Aussage** |
| `verify_rtd_chain.py` | NEIN | Torwaechter des Geldpfads |
| `verify_ticket13_live.py` | NEIN | Live-Beleg Rechtslinks |

Ticket 14 hatte nur die eigene Nachbarschaft angesehen — exakt der Fehler, den
Ticket 13 als Teil-Vollstaendigkeits-Falle beschrieben hat.

### Warum ausgerechnet `funnel_check.py` zuerst

Es ist das Instrument, auf dem die **gesamte Strategie** ruht: die Aussage
„BESUCHER = 0" begruendet seit Ticket 9 jedes „warte, beobachte Sales".
Das Skript hat aber in seiner ganzen Lebenszeit **nur eine einzige Zahl
ausgegeben: 0**. Niemand hatte je gezeigt, dass es ueberhaupt *hochzaehlen
kann*. Waere `classify()` verdreht, saehe die Ausgabe **identisch** aus — und
der erste echte Besucher (und damit das Signal fuer den ersten Sale) waere
unbemerkt durchgerutscht. Ein Zaehler, der nie beim Zaehlen beobachtet wurde,
ist kein Messgeraet, sondern eine Behauptung.

### Zweiter Befund: stille Untererfassung (echter Defekt, nicht nur fehlender Test)

`main()` rief `checkout/sessions?limit=100` auf und las **nur die erste Seite**.
Stripe liefert `has_more` mit (MEASURED gegen die LIVE-API: Feld vorhanden,
aktuell `False`) — das Skript hat es **ignoriert**. Ab Session 101 haette der
Zaehler also dauerhaft zu wenig gemeldet, ohne das zu sagen. Heute noch harmlos
(2 Sessions), aber der Defekt waere genau dann scharf geworden, wenn endlich
Traffic da ist — also im ungeeignetsten Moment.

Dritter, kleinerer Befund: `payment_status=None` haette die Detailausgabe mit
einem `TypeError` abgeraeumt (Formatierung `{None:<8}`).

## Fix

- **Pagination** ueber `starting_after` bis `has_more` faellt (`fetch_all_sessions()`).
- **Ehrliche Untergrenze statt falscher Zahl**: reisst `has_more` nach
  `MAX_PAGES` nicht ab, meldet das Skript `vollzaehlig = NEIN (Untergrenze!)`
  und gibt `rc=3` — es gibt keine zu kleine Zahl mehr als Messwert aus.
- `str()` um `payment_status` (Crash weg).
- **`--selftest` mit Fault Injection durch die ECHTE `main()`** (Konvention aus
  `auto_fulfill.py` / Ticket 14): kein Reimplementat, injiziert wird nur die
  Stripe-Antwort.

## Belege (MEASURED)

```
python scripts/request_delivery/funnel_check.py --selftest
  -> 13/13 SELFTEST_OK  (rc=0)
```
Abgedeckt: leer, echter Browser, API-Probe, Eigentest-Vorrang, gemischt,
Conversion 1/2 = 50,0 %, `payment_status=None` ohne Crash, Pagination
(101 statt 100 + `starting_after` nachgewiesen), Dauer-`has_more` → rc=3,
Stripe-Fehler → rc=2 ohne erfundene Null, Mutation von `classify` wird
bemerkt, Kontrollprobe wieder gruen.

**Rot-Probe** (`_mutation_probe_t15.py`, mutiert den Produktivcode):
```
[BASIS ] unmutiert: rc=0 -> GRUEN
[OK ] Pagination ignorieren (der Defekt von heute): rc=1 rot=True kein_absturz=True erwarteter_fall_faellt=True
[OK ] Besucher als API-Probe verbuchen:             rc=1 rot=True kein_absturz=True erwarteter_fall_faellt=True
[OK ] Truncation-Guard entschaerfen:                rc=1 rot=True kein_absturz=True erwarteter_fall_faellt=True
[OK ] Datei bitgenau wiederhergestellt (sha256 74e8d93652ec...)
[OK ] rc-Wechsel belegt: 1 (mutiert) -> 0 (repariert)
ERGEBNIS: MUTATION_PROBE_OK
```
Wichtig: Mutation 1 ist **der heute real gefundene Defekt**. Der neue Selftest
haette ihn gefangen. Jede Rot-Probe prueft zusaetzlich auf `Traceback`
(Exit-Code-Falle: ein Absturz ist keine Erkennung).

**Live nach dem Eingriff:**
```
funnel_check (LIVE): sessions_roh=2  vollzaehlig=ja
                     BESUCHER=0 / API-PROBE=0 / EIGENTEST=2  rc=0
auto_fulfill --selftest : gruen (Consent, 3 Stufen, Fault Injection, Seite)
legal_link_audit        : LEGAL_LINKS_OK (40 Seiten, 0 unvollstaendig)
verify_rtd_chain        : KETTE_OK (399/799/1499 cent, Feld 'anfrage', Redirect ok)
rtd/thanks/index/agb/datenschutz/impressum/sitemap : HTTP 200
```
`BESUCHER = 0` ist damit erstmals eine **gemessene** Null: der Zaehler ist
nachweislich in der Lage, etwas anderes als 0 auszugeben, und meldet die
Zahl als vollzaehlig.

## Ehrliche Grenze

Bewiesen ist, dass der Zaehler **korrekt klassifiziert und vollzaehlig liest**.
**Nicht** bewiesen ist die Praemisse aus Ticket 9 selbst — dass jeder echte
Browser eine Session mit `payment_link` anlegt. Die beruht auf *einer* Messung
(1x curl, 1x Browser am 2026-08-04) und bleibt eine Stichprobe; ein Browser mit
blockiertem JS koennte unsichtbar bleiben. Der Zaehler ist deshalb weiterhin
eine **Untergrenze der Besucher**, kein Vollzaehler. Ebenfalls ungemessen
bleibt die Retention der Stripe-Session-Liste.

## Offen (Folgearbeit, NICHT in diesem Ticket erledigt)

`verify_rtd_chain.py` und `verify_ticket13_live.py` haben weiterhin keinen
`--selftest`. `verify_rtd_chain.py` ist der Torwaechter des Geldpfads und
damit der naechste Kandidat derselben Klasse.
