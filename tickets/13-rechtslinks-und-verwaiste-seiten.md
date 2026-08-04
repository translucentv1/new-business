# Ticket 13 — Rechts-Footer vollständig + verwaiste Traffic-Seiten publizieren

Typ: `wayfinder:task` (AFK) · Status: **GESCHLOSSEN 2026-08-04**

## Question

Trägt **jede ausgelieferte** Seite die Pflicht-Rechtslinks — und erreicht überhaupt
jede gebaute Seite die Live-Site? Bisher wurde beides nur für den **Kaufpfad**
(`rtd.html`/`thanks.html`) gemessen, nie für die 33 SEO-Landingpages, auf denen ein
echter Besucher zuerst landet.

## Befund (MEASURED 2026-08-04)

**Defekt A — 2 Seiten waren gebaut, aber nie live.**
Ein Traffic-Tick erzeugte um 18:25 Uhr `blog/hochzeitsrede-schreiben-lassen.html`
und `blog/pitch-deck-erstellen-lassen.html` samt Sitemap-/Index-/Interlink-Eintrag,
committete aber nichts. 4 h später:

```
hochzeitsrede-schreiben-lassen -> HTTP 404
pitch-deck-erstellen-lassen    -> HTTP 404
git ls-tree origin/gh-pages blog/ | grep -E 'hochzeitsrede|pitch-deck'  -> NICHT im origin-Tree
```

Ursache: `scripts/traffic_engine.py` enthält **keinen einzigen git-Aufruf**
(`grep -nE "git |commit|push|subprocess"` → 0 Treffer). Die Publizierung hängt
vollständig am aufrufenden Agenten. Bleibt der Commit aus, ist die Arbeit tot —
still, ohne Fehlermeldung. Gleiche Defektklasse wie die IndexNow-Branch-Falle:
**„gebaut" ist nicht „live"**, nur diesmal auf dem Traffic-Pfad.

**Defekt B — der Datenschutz-Link fehlte auf 33 von 38 Seiten.**
`datenschutz.html` existiert seit Ticket 6 und ist live (HTTP 200), aber
„existiert" ist nicht „von jeder Seite erreichbar". Art. 13 DSGVO / § 5 DDG
verlangen ständige Verfügbarkeit — und ein SEO-Besucher landet auf einer
Blogseite, nicht auf der Startseite.

```
== Rechtslink-Audit (lokaler Baum) ==
geprueft        = 38 Seiten
unvollstaendig  = 33
  datenschutz.html     fehlt auf 33 Seiten
ERGEBNIS: LEGAL_LINKS_UNVOLLSTAENDIG   (echter rc=1)
```

Impressum und AGB waren überall vorhanden — genau **eine** der drei Pflichtseiten
fehlte, weshalb es bei Stichproben nie auffiel. Root-Cause ist das Footer-Template
in `traffic_engine.py:190`, das nur Impressum + AGB kennt: jede neu generierte
Seite hätte den Defekt erneut mitgebracht.

## Fix

- `scripts/request_delivery/legal_link_audit.py` (NEU) — prüft alle Root- und
  Blogseiten, nimmt Rechtsseiten/Redirects/Stubs begründet aus.
  `--selftest` mit Fault Injection: **9/9**, inklusive Nachweis, dass der Prüfer
  rot werden *kann* (Map-Notiz „Prüfer prüfen") und dass `rc` zwischen 1 und 0
  wechselt (Map-Notiz „Exit-Code-Falle").
- `scripts/request_delivery/add_datenschutz_link.py` (NEU) — Einmal-Reparatur.
  Ersetzt **nur** den exakt passenden Footer-Block; Seiten ohne dieses Muster
  werden gemeldet statt blind angefasst (2 gemeldet: die Datenschutzseite selbst
  und der Google-Verify-Stub — beide korrekt ausgenommen).
- `scripts/traffic_engine.py:190` — Footer-Template um Datenschutz ergänzt
  (Root-Cause, sonst kommt der Defekt beim nächsten Traffic-Tick zurück).
- Die verwaisten Traffic-Seiten mitpubliziert.

## Ergebnis (MEASURED nach Push)

- Audit lokal: `LEGAL_LINKS_OK`, unvollstaendig = 0 (vorher 33).
- Live-Stichprobe: siehe Resolution-Kommentar im Handoff — beide zuvor
  404-Seiten liefern HTTP 200, gepatchte Seiten liefern den Datenschutz-Link
  im ausgelieferten Body aus.
- `verify_rtd_chain.py` → `KETTE_OK` (3 LIVE-Links unverändert,
  399/799/1499 cent = 3,99/7,99/14,99 EUR).
- `auto_fulfill.py --selftest` → grün inkl. Tier-Fault-Injection.

## Ehrliche Grenze

Der Audit prüft **Anwesenheit eines Links**, nicht dessen Rechtsgültigkeit. Die
Postanschrift in `impressum.html` bleibt Platzhalter (USER-Blocker Nr. 1) — mit
Datenschutz-Link auf jeder Seite ist der Kaufpfad zumutbarer, aber nicht
abmahnsicher. Der Link ist notwendig, nicht hinreichend.

`traffic_engine.py` publiziert weiterhin **nicht** selbst. Das ist bewusst nicht
mitgefixt: ein Generator, der ungefragt auf `gh-pages` pusht, ist gefährlicher als
einer, der es lässt. Stattdessen ist der Prüfer jetzt da, der den Zustand aufdeckt.
