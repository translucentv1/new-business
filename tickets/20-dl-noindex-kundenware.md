# Ticket 20 — Indexier-Schutz der bezahlten Kundenware unter /dl/

Typ: task (AFK) · Status: GESCHLOSSEN 2026-08-06 · unblockiert

## Frage

Ist die ausgelieferte, BEZAHLTE Kundenware unter `/dl/` gegen Indexierung
geschuetzt? Bis hierher wurde am Geldpfad nur der STATUSCODE gemessen
(GET/HEAD 200), nie der ausgelieferte INHALT.

## Befund (MEASURED 2026-08-06)

### 1. Der Schutz, auf den sich das Repo verliess, existiert nicht

Der einzige robots.txt, den ein Crawler liest, ist der des ORIGINS:

    https://translucentv1.github.io/robots.txt              -> HTTP 404
    https://translucentv1.github.io/new-business/robots.txt -> HTTP 200
                                     (enthaelt "Disallow: /dl/")

Primaerquelle RFC 9309 (rfc-editor.org, HTTP 200, frisch abgerufen — nicht
aus dem Gedaechtnis zitiert):

- §2.3: *"The rules MUST be accessible in a file named '/robots.txt' (all
  lowercase) in the top-level path of the service."* URI-Form:
  `scheme:[//authority]/robots.txt`
- §2.3.1.3: 4xx = "Unavailable" -> *"the crawler MAY access any resources"*

=> Die Datei mit `Disallow: /dl/` liegt in einem UNTERVERZEICHNIS und wird von
keinem Crawler gelesen. ADR-0013 ("Download-Gate nicht crawlen") war seit
Bestehen wirkungslos. Gleiche Defektklasse wie die IndexNow-Branch-Falle:
die Datei existiert, aber am falschen Ort.

### 2. Damit ist `meta robots` der EINZIGE Schutz — und er fehlte fast ueberall

Zielmenge aus dem Baum abgeleitet (nicht hartkodiert), origin/gh-pages:

    dl-HTML-Dateien gesamt : 24
    davon mit noindex      :  1
    OHNE Schutz            : 23

LIVE gegengemessen (nicht nur im Baum), Stichprobe von 5:

    HTTP=200 robots=[noindex,nofollow]  tales-of-folk-and-fairies.html
    HTTP=200 robots=[KEIN]              frankenstein.html          (436 KB)
    HTTP=200 robots=[KEIN]              wuthering-heights.html     (683 KB)
    HTTP=200 robots=[KEIN]              emma.html                  (923 KB)
    HTTP=200 robots=[KEIN]              einkommensteuer-ausfuellhilfe.html

Das sind vollstaendige, bezahlte Produkte (Buchtexte, Steuer-Tools), live
ausgeliefert und indexierbar.

### 3. Warum es nie auffiel

`rtd.html`s eigene Auslieferung (auto_fulfill-Template) TRAEGT das noindex —
die eine gepruefte Stelle war gesund. Teil-Vollstaendigkeits-Falle, jetzt zum
vierten Mal (Ticket 13 Rechtslinks, Ticket 15 Werkzeugkiste, Ticket 17
Stichprobe, hier die Kundenware).

## Fix

- `verify_publish_leg.py` gehaertet: prueft jetzt zusaetzlich den LIVE
  ausgelieferten BODY auf `meta robots ... noindex`. Vorher nur Statuscodes.
- `dl_noindex_audit.py` NEU (stehendes Tor, mit `--selftest`): Zielmenge aus
  dem Baum abgeleitet, `--live` misst die Auslieferung, `--fix` patcht nur am
  exakten charset-Anker und MELDET Abweicher statt zu raten. Drittes
  Ergebniswort `DL_UNGEPRUEFT` (rc=2); leere Zielmenge ist NICHT gruen.
- 23 Deliverables gepatcht.

## Belege

    verify_publish_leg.py --selftest      12/12 SELFTEST OK
    _mutation_probe_t20.py                MUTATION_PROBE_OK 3/3 (Produktivcode
                                          mutiert, sha256-genau restauriert)
    verify_publish_leg.py (echter Lauf)   PUBLISH_LEG_OK, LIVE meta robots =
                                          noindex,nofollow, GET+HEAD 200 nach 31s
    dl_noindex_audit.py --selftest        16/16 SELFTEST_OK
    dl_noindex_audit.py (vor dem Fix)     DL_NOINDEX_DEFEKT, 23 offen, rc=1
    dl_noindex_audit.py --fix             23 gepatcht, 0 offen, rc=0
    _probe_patch_integrity_t20.py         PATCH_INTEGRITAET_OK 23/23
                                          (Inhalt unveraendert, nur Tag ergaenzt)
    dl_noindex_audit.py --live (nach Push) siehe Handoff

## Offener Rest -> Ticket 21

14 `.epub`-Dateien unter `/dl/` koennen KEIN `meta robots` tragen (binaer).
Sie bleiben crawlbar, solange der Origin kein `robots.txt` hat. Per meta ist
das nicht schliessbar — es braucht entweder ein User-Pages-Repo
`translucentv1.github.io` mit einem echten Origin-robots.txt oder einen
Hoster, der `X-Robots-Tag` setzen kann. Eigenes Ticket, eigener Grill.

## Merkregeln (neu)

- Ein Schutzmechanismus ist erst belegt, wenn er an dem ORT gemessen wurde, an
  dem der Konsument ihn liest. `robots.txt` liest der Crawler NUR am Origin —
  eine Kopie im Unterverzeichnis ist Dekoration.
- Statuscode != Inhalt. Ein Pruefer, der nur `%{http_code}` misst, sagt nichts
  darueber, WAS ausgeliefert wird.
- Bei Massen-Patches auf BEZAHLTE Ware immer eine Integritaetssonde: Tag wieder
  abziehen, gegen den alten Blob vergleichen. "Skript lief fehlerfrei" ist kein
  Beleg, dass der Inhalt unbeschaedigt ist.
