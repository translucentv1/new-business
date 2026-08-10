# Ticket 29 — Rechtslink-Prüfer sehen 61 von 1287 Seiten (AFK, unblockiert)

Status: GESCHLOSSEN (2026-08-10, RTD-Tick)
Typ: task (Defekt auf dem Traffic-/Rechtspfad)
Gefunden: 2026-08-10 (RTD-Tick)

## Antwort (MEASURED 2026-08-10)

Ursache bestaetigt: beide Pruefer leiteten ihre Zielmenge aus einer hartkodierten
Glob-Liste (`"*.html"`, `"blog/*.html"`) ab. `seo/`, `t/`, `docs/` und die
numerischen Produktverzeichnisse lagen ausserhalb jedes Globs und wurden nie
geprueft — die Pruefer meldeten `LEGAL_LINKS_OK` ueber **61** Seiten, waehrend
der Baum 1287 HTML-Dateien hatte.

Behoben:
1. `legal_targets.py` (NEU) — EINE rekursive Ableitungsregel, von beiden
   Pruefern importiert. Ausnahmen explizit begruendet (Rechtsseiten selbst,
   Redirects, Stubs).
2. Deckungsabgleich gegen `git ls-tree`: Drift wird rot bzw. unmessbar,
   nicht gruen.
3. Backfill: `<!-- LEGAL:v1 -->`-Sentinel-Block auf 1201 Seiten.
4. `traffic_engine.py` mitgefixt, sonst waechst der Defekt nach (Ticket 13).

Belege (alle in diesem Tick selbst ausgefuehrt, nicht vom Vortick uebernommen):

    legal_link_audit.py --selftest      -> SELFTEST_OK
    verify_ticket13_live.py --selftest  -> 34/34 SELFTEST_OK
    _mutation_probe_t29.py              -> MUTATION_PROBE_OK 28/28
                                           (sha256 legal_targets.py d4db00256205ce23)
    legal_link_audit.py (Baum)          -> 1258 geprueft, 29 ausgenommen,
                                           0 unvollstaendig, LEGAL_LINKS_OK
    _t29_rueckbau_probe.py              -> RUECKBAU_OK 1210/1210

Prueflaeche der Audits: **61 -> 1258 Seiten**.

### Rueckbau-Beweis fuer den Massen-Patch (Merkregel Ticket 20)

`evidence/_t29_rueckbau_probe.py` (NEU, unabhaengig vom Backfill-Skript):
entfernt aus jeder geaenderten Datei die Sentinel-Bloecke und vergleicht
sha256 gegen `git show HEAD:<datei>`. Ergebnis: 1210/1210 byte-genau
rekonstruierbar, **0 Fremdaenderung** — der Patch auf 1200+ Dateien hat
nachweislich nichts ausser dem Rechts-Footer angefasst.

Zwei Falsch-Rot-Lagen der Sonde selbst wurden dabei ausgemessen und behoben
(nicht wegargumentiert):
- `core.autocrlf=true` -> Arbeitsstand CRLF, `git show` LF. Roher Byte-
  Vergleich meldete 704/1210 als veraendert. Jetzt LF-normalisiert, die
  reine Zeilenende-Drift wird SEPARAT ausgewiesen (713 Dateien).
- Der ENRICH-Block steht auf eigener Zeile; ohne Mitnahme des vorangehenden
  Umbruchs wich der Rueckbau um genau ein `\n` ab -> 9/9 Falsch-Rot.

## Befund (MEASURED 2026-08-10)

Warum melden `legal_link_audit.py` (Baum) und `verify_ticket13_live.py` (LIVE)
`LEGAL_LINKS_OK` / `LIVE_OK`, während 90 % der ausgelieferten Seiten keinen
Impressum-, Datenschutz- und AGB-Link tragen — und wie wird die Zielmenge so
abgeleitet, dass sie mit dem Baum mitwächst?

## Befund (MEASURED 2026-08-10)

Beide Prüfer leiten ihre Zielmenge aus **derselben hartkodierten Glob-Liste** ab:

    for pat in ("*.html", "blog/*.html"):        # legal_link_audit.py:47
    for pat in ("*.html", "blog/*.html"):        # verify_ticket13_live.py:67

Das ist genau die **eingefrorene Stichprobe** aus Ticket 17 — nur eine Ebene
höher: nicht die Seitenliste war hartkodiert, sondern die **Verzeichnisliste**.
Der Baum ist seitdem um zwei ganze Verzeichnisbäume gewachsen, die kein Glob
erfasst.

Vollzählig über `git ls-tree -r HEAD` (1287 HTML-Dateien):

| Gruppe | Seiten | ohne vollständige Rechtslinks |
|---|---|---|
| `seo/` | 693 | **693** |
| `t/` | 468 | **468** |
| `dl/` | 24 | 24 (bezahlte Kundenware) |
| `docs/` | 24 | 24 |
| numerische Produktseiten (`98/`, `1260/`, …) | 14 | **14** |
| `blog/` | 51 | 0 |
| root | 5 | 0 |
| **Summe** | **1282** | **1225** |

Live gegengemessen (Statuscode *und* Body, Merkregel Ticket 20):

    seo/a-tale-of-two-cities/analyse/   HTTP 200  3858 B  impressum=0 datenschutz=0 agb=0  noindex=0
    t/adhs-wochenplaner/adhs-aachen/    HTTP 200  1738 B  impressum=0 datenschutz=0 agb=0  noindex=1

## Warum das teuer ist

- **`seo/` stellt 693 der 764 Sitemap-URLs (90,7 %)** — das sind exakt die
  Seiten, auf denen ein Suchbesucher landen *soll*, und sie sind an IndexNow
  eingereicht. Der ganze Traffic-Hebel zeigt auf Seiten ohne Impressum.
- § 5 DDG verlangt das Impressum „leicht erkennbar, unmittelbar erreichbar und
  ständig verfügbar" — nicht nur auf der Startseite. Art. 13 DSGVO ebenso.
  Genau die Begründung, mit der Ticket 13 die 33 Blogseiten gefixt hat.
- Die 14 numerischen Verzeichnisse sind **Produkt-Landingpages mit Kaufbutton**.
- Ticket 13 hat die Klasse „Datenschutz fehlt auf 33 Seiten" geschlossen und
  dabei den Prüfer gebaut, der sie künftig fangen sollte. Der Prüfer wuchs
  jedoch nicht mit dem Baum → dieselbe Lücke, 37-fach größer, unentdeckt.

## Vorgehen

1. Ableitungsregel in **ein** Modul (`legal_targets.py`), von beiden Prüfern
   importiert (Merkregel Ticket 17: zwei Prüfer, dieselbe Menge, dieselbe Regel).
   Rekursiv über den Baum, nicht per Glob-Liste.
2. Ausnahmen **begründet und explizit**: Rechtsseiten selbst, Redirects, Stubs,
   `dl/` (bezahlte Kundenware, noindex, nicht Teil des Webangebots).
3. **Deckungsabgleich** gegen `git ls-tree` (Merkregel Ticket 18: eine Prüfzahl
   ist kein Deckungsbeweis) — Drift muss rot/unmessbar werden, nicht grün.
4. Selftest: eine Seite in einem **neu entstandenen Unterverzeichnis** ohne
   Links MUSS rot sein. Alt-Stand-Probe: HEAD-Fassung gegen dieselbe Lage
   ausführen (nicht argumentieren) — erwartet `rc=0` „war BLIND".
5. Backfill der fehlenden Rechtslinks mit **Integritätssonde** (Merkregel
   Ticket 20: Massen-Patch auf 1200 Dateien braucht einen Rückbau-Beweis).
6. Generator mitfixen, sonst wächst der Defekt nach (Merkregel Ticket 13).

## Nicht vergessen

- `evidence/_t29_probe*.py` gehören **nicht** zu diesem Ticket, sondern zum
  parallelen SEO-Tick (Doorway-Deindex, Commit `6dd6238`). Namensgleichheit
  ist Zufall.
- `t/` ist seit `6dd6238` `noindex,follow` — bleibt aber öffentlich abrufbar,
  die Impressumspflicht entfällt dadurch **nicht**.
