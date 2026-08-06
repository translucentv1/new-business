# Ticket 21 — .epub-Kundenware ist per meta robots nicht schuetzbar

Typ: grilling (HITL) · Status: OFFEN · unblockiert · Prioritaet: niedrig

## Frage

14 `.epub`-Dateien unter `/dl/` sind bezahlte Kundenware, liegen live unter
HTTP 200 und koennen **kein** `meta robots` tragen (Binaerformat). Der
Origin-`robots.txt` ist 404 (siehe Ticket 20, RFC 9309 §2.3), also greift auch
`Disallow: /dl/` nicht. Was — wenn ueberhaupt — soll dagegen getan werden?

## Ausgangslage (MEASURED 2026-08-06)

    https://translucentv1.github.io/robots.txt   -> HTTP 404
    dl/**/*.epub im origin/gh-pages-Tree         -> 14
    Stichprobe live: tales-of-folk-and-fairies.epub
      -> HTTP 200, content_type application/epub+zip
    /dl/ in der LIVE-Sitemap                     -> 0 Treffer
    IndexNow-Einreichung filtert /dl/ heraus     -> ja (Scope-Filter)

Entlastend: die URLs enthalten einen 16-stelligen Hash und sind nirgends
verlinkt, weder in Sitemap noch IndexNow. Ein Crawler muesste sie raten.
Belastend: "nicht verlinkt" ist kein Schutz, sondern Obskuritaet — und
Suchmaschinen finden URLs auch ueber Referrer, Toolbars und Mail-Scanner.

## Optionen (noch nicht entschieden — deshalb HITL)

1. **Nichts tun, ehrlich dokumentieren.** Hash-URLs, 0 Verlinkung, 0 Sales
   bisher. Kosten: 0. Risiko: eine geratene/geleakte URL ist dauerhaft offen.
2. **User-Pages-Repo `translucentv1.github.io` anlegen** mit einem echten
   Origin-`robots.txt`. Schliesst die Luecke fuer ALLE Pfade inkl. .epub auf
   einen Schlag. Kosten: ein neues oeffentliches Repo im Nutzer-Account;
   Nebenwirkung: `translucentv1.github.io` liefert dann Inhalt. **Greift in
   den GitHub-Account des Nutzers ein -> nicht eigenmaechtig.**
3. **Hoster mit `X-Robots-Tag`-Header** (GitHub Pages kann keine Header
   setzen). Waere die saubere Loesung, bedeutet aber Umzug der Auslieferung.
4. **Auslieferung hinter einen echten Gate** (signierte URLs, Ablauf). Groesster
   Umbau, braucht einen Server — steht dem "kein Server"-Prinzip entgegen.

## Warum das nicht der Cron entscheidet

Option 2 legt ein Repo im Account des Nutzers an und veraendert, was unter
seiner Nutzer-Domain ausgeliefert wird. Option 3 und 4 verlassen die
serverlose Architektur. Beides sind Scoping-Entscheidungen, keine Messungen.

## Nicht vergessen

Falls Option 2 gewaehlt wird: danach `dl_noindex_audit.py` bleibt trotzdem
noetig — ein Origin-`robots.txt` steuert **Crawling**, `meta robots` steuert
**Indexierung**. Eine bereits indexierte Seite verschwindet durch ein
nachtraegliches `Disallow` gerade NICHT (der Crawler darf sie dann nicht mehr
lesen und sieht das `noindex` nicht mehr). Beides gehoert nebeneinander.
