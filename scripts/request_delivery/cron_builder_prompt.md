Baue autonom am Request-to-Delivery-Feature in scripts/request_delivery/.

STAND 2026-07-28: Schritte 1-3 (Webhook-HMAC, index/rtd-Landingpage, Impressum/AGB)
sind gebaut + live (HTTP 200 MEASURED). Delivery-Kette ohne Server steht:
  Kunde zahlt (rtd.html -> LIVE Payment Link, Pflichtfeld "anfrage")
  -> Stripe-Redirect auf thanks.html?sid={CHECKOUT_SESSION_ID}
  -> thanks.html pollt dl/rtd/<sha256(sid)[:16]>.html (JS==Python-Hash MEASURED)
  -> auto_fulfill.py (pro Tick ausfuehren!) pollt paid sessions, generiert via
     Ollama qwen2.5:3b ($0), schreibt dl/rtd/<hash>.html, committet + pusht,
     loggt in sales.log.

STAND 2026-08-03 (Tick-Verifikation, MEASURED): auto_fulfill.py gelaufen ->
sessions=0/paid=0/neu=0 -> keine Sales. rtd.html & thanks.html HTTP 200 (live,
thanks.html body 2658 B). Fulfillment-Kette BEWIESEN: Ollama qwen2.5:3b vorhanden,
gen_deliverable liefert 629 B echten DE-Text (err=None); auto_fulfill --selftest OK
(Temp-File aufgeraeumt). Cross-Linking rtd.html: ALLE 14 Buch-Landingpages + 25
Blogseiten + Startseite verlinken bereits -> Schritt "Traffic Blog-Links" ERLEDIGT.
Verbleibend USER-Blocker: EMAIL_* (Mail-Versand), Impressum/AGB-Platzhalter
[DEIN NAME]; Fiverr=USER-KYC. KEIN DEMO-Modus (LIVE-Key + Ollama aktiv).

STAND 2026-08-03 (Tick): auto_fulfill 0 Sales (LIVE). Kette MEASURED verifiziert
inkl. Preise: Basis 3,99 / Standard 7,99 / Premium 14,99 EUR (alle livemode/active,
Feld "anfrage", Redirect OK). verify_rtd_chain.py um Preis-Check (amount>0 via
line_items-Sub-Endpoint) gehaertet + gepusht (84a9d1c). "Kein-Preis"-Hypothese
fuer 0 Sales WIDERLEGT -> 0 Sales = Traffic/Conversion-Luecke, kein Defekt.

Pflicht pro Tick:
1. python scripts/request_delivery/auto_fulfill.py  (Sale-Check + Fulfillment).
   Bei Sale: GROSS "ERSTER SALE" melden.
2. Live-Check rtd.html/thanks.html (curl 200) an kanonischer Domain:
   https://translucentv1.github.io/new-business/  (WICHTIG: philippgro.github.io
   liefert 404 — nur die echte Repo-Owner-Domain translucentv1 ist live!).

Kanonische Live-Domain (MEASURED 2026-08-03): translucentv1.github.io/new-business/

Naechste sinnvolle Schritte (einen pro Tick):
1. E-Mail-Zustellung nachruesten sobald EMAIL_* in hermes/.env gesetzt (USER-Blocker;
   dann in auto_fulfill.fulfill_session Mail mit Deliverable-URL an customer email).
2. Traffic: rtd.html von weiteren Blogseiten verlinken / Gig-Kanaele (Fiverr = USER-KYC).
3. Impressum/AGB-Platzhalter [DEIN NAME] etc. = USER-Blocker vor breitem Launch.

STAND 2026-08-03 (Tick 2, MEASURED): auto_fulfill 0 Sales (LIVE). verify_rtd_chain.py
-> KETTE_OK (3 LIVE-Links active, 3,99/7,99/14,99 EUR, Feld 'anfrage', Redirect auf
translucentv1.github.io/.../thanks.html, Hash-Paritaet OK, dl/rtd-Ziel vorhanden).
Kanonische Live-Domain = translucentv1.github.io (philippgro.github.io = 404, nur
Repo-Owner-Domain live). rtd.html/thanks.html HTTP 200 (rtd.html 5309 B). Feature
vollstaendig + MEASURED live. 0 Sales = Traffic/Conversion-Luecke, KEIN Defekt.
Offen (USER-Blocker): EMAIL_* (Mail-Versand), Impressum/AGB-Platzhalter [DEIN NAME];
Fiverr-Gig = USER-KYC. Naechster autonomer Schritt: keiner sinnvoll ueberlebensfaehig
-> "warte, beobachte Sales" (Idle OK, Aktionismus nicht).

STAND 2026-08-04 (Tick, MEASURED): auto_fulfill 0 Sales (sessions=0/paid=0/neu=0,
LIVE). verify_rtd_chain.py -> KETTE_OK (3 LIVE-Links, 3,99/7,99/14,99 EUR, Feld
'anfrage', Redirect OK, Hash-Paritaet). rtd/thanks/index/sitemap HTTP 200.
DEFEKT GEFUNDEN + BEHOBEN (frueherer Claim GEGENBEWIESEN): Commit b8f2840
"IndexNow key added" legte die Key-Datei auf Branch *master* unter docs/ —
GitHub Pages liefert aber den *gh-pages-ROOT*. Beide Key-URLs live HTTP 404,
`git ls-tree -r HEAD` leer => IndexNow war seit 24.07. NIE funktionsfaehig.
Fix (Commit 034e395): Key-Datei im gh-pages-ROOT (32 B, kein Newline) ->
live HTTP 200; neues scripts/indexnow_submit.py (Scope-Filter, /dl/ raus,
echte Statusausgabe). Submit MEASURED: 10 URLs -> HTTP 202, 1205 URLs -> HTTP 200.
rtd.html ist in der Sitemap enthalten. WICHTIG: 202/200 = angenommen, NICHT
indexiert — Wirkungsnachweis erst ab 2026-08-07 (tickets/5-bing-indexierung-
verifizieren.md).
MERKREGEL: publish_site.py existiert NICHT mehr (nur .pyc/.log) -> mit
`git add/commit/push origin gh-pages` publizieren. Pages-Rebuild dauert
~30-45 s (MEASURED: 404, 404, dann 200).

Naechster Tick: Ticket 6 abarbeiten (datenschutz.html bauen + agb.html
ent-templatisieren mit den ECHTEN Daten aus impressum.html). Die Postanschrift
bleibt USER-Blocker — NICHT erfinden, nur an EINER Stelle offen lassen.

STAND 2026-08-04 (Tick 3, MEASURED): auto_fulfill 0 Sales (sessions=0/paid=0/neu=0).
TICKET 6 ERLEDIGT + GESCHLOSSEN (Commit 4b6f598, live verifiziert):
- datenschutz.html NEU gebaut -> war HTTP 404, ist jetzt HTTP 200 (6257 B).
  Art. 13 DSGVO, Verantwortlicher per VERWEIS aufs Impressum (Adresse existiert
  dadurch genau 1x im Repo). Faktenbasis frisch gemessen: kein Set-Cookie,
  keine Third-Party-Ressourcen auf rtd/thanks.
- agb.html ent-templatisiert: Name/Email/Datum/Lieferfrist/USt gefuellt,
  noindex -> index,follow (live geprueft). Warnkasten NICHT entfernt, sondern
  ehrlich umgeschrieben: nennt jetzt nur noch die fehlende Anschrift.
- AGB §5 GEGEN frueheren Text korrigiert: Zustimmung nach §356 Abs.5 BGB wird
  NICHT eingeholt -> 14-taegiges Widerrufsrecht bleibt bestehen. Kein
  Erloeschen mehr behaupten. Technische Einholung = NEU Ticket 7.
- AGB §3 Lieferfrist 24 h / max 5 Werktage = DECISION (gestuetzt auf 2h-Cron),
  KEINE Messung. gig.html sagte schon 24 h -> jetzt konsistent.
- 2 Befunde, die im Ticket fehlten: Adress-Platzhalter stand in 6 Live-Seiten
  (nicht 2) -> rtd/gig/lead_magnet/ki-text-service zeigen jetzt aufs Impressum.
  scripts/request_delivery/index.html war eine LIVE erreichbare Altkopie der
  Verkaufsseite mit [DEIN NAME]/[STRASSE]/[EMAIL] -> jetzt noindex-Redirect.
- Platzhalter live nur noch in impressum.html (Z. 20-21) = EINZIGER USER-Blocker.
- sitemap.xml 1207 -> 1210 URLs (impressum/agb/datenschutz ergaenzt, XML ok),
  IndexNow 1210 URLs -> HTTP 200 (angenommen, NICHT indexiert).
- verify_rtd_chain.py KETTE_OK, 3 LIVE-Links unveraendert (399/799/1499 cent).

Naechster Tick: Ticket 7 (tickets/7-widerruf-zustimmung-checkout.md) —
Stripe consent_collection an einem PAYMENT LINK pruefen (gegen die API belegen,
nicht aus Checkout-Session-Analogie schliessen). VORSICHT: fasst die einzige
Einnahmequelle an — Ist-Zustand der Links sichern, danach verify_rtd_chain.py.
AGB §5 erst umstellen, wenn Zustimmung wirklich eingeholt UND auslesbar ist.
Ticket 5 (Bing-Trefferzahl) weiterhin erst ab 2026-08-07.

STAND 2026-08-04 (Tick 2, MEASURED): auto_fulfill 0 Sales (sessions=0/paid=0/neu=0).
rtd/thanks/index/sitemap/impressum/agb HTTP 200. Sitemap-Healthcheck NEU
(scripts/sitemap_healthcheck.py): ALLE 1207 Sitemap-URLs live HTTP 200, 0 Defekte,
0 duenne Seiten -> IndexNow-Einreichung ging gegen eine gesunde Sitemap.

>>> PREIS-CLAIM KORRIGIERT (100x-Fehler, repo-weit gepurged) <<<
Die echten Preise sind 3,99 / 7,99 / 14,99 EUR — NICHT 399/799/1499 EUR.
Ursache: verify_rtd_chain.py druckte Stripes `price.unit_amount` roh; das Feld ist
in CENT. Fruehere Ticks lasen "amount=399 eur" als "399 EUR". Gegenbeweis: rtd.html
selbst listet `<option value="3.99">Basis – 3,99 €`, app.py hat
`PRICE_DEFAULT = 399  # cents (3,99 EUR)`. verify_rtd_chain.py gehaertet -> gibt
jetzt "preis=399 cent = 3.99 EUR" aus (MEASURED gegen LIVE-Stripe).
KONSEQUENZ: Das ist ein Micro-Produkt (~4-15 EUR), kein Premium-Angebot. Jede
Umsatzrechnung und Conversion-Erwartung frueherer Ticks war um Faktor 100 falsch.

DEFEKTE AUF DEM KAUFPFAD GEFUNDEN (Ticket 6, offen):
- datenschutz.html existiert NIRGENDS (live 404, nicht lokal, nicht in git) —
  DSGVO Art. 13 Pflichtseite fehlt, obwohl Stripe-Checkout personenbezogene Daten
  erhebt.
- agb.html ist LIVE und von rtd.html verlinkt, zeigt aber sichtbar
  "[TEMPLATE — NICHT VERÖFFENTLICHUNGSREIF]" + Platzhalter [DEIN VOLLER NAME],
  [EMAIL], [STRASSE HAUSNUMMER], [PLZ ORT], [DATUM], [LIEFERFRIST] und traegt
  <meta name="robots" content="noindex">.
- impressum.html hat ECHTE Daten (Philipp Behnisch, Mail, Telefon), aber
  Adress-Platzhalter [Straße Hausnummer]/[PLZ Ort].
- agb.html §5: Widerrufs-Zustimmung per Checkbox ist gefordert, aber technisch
  NICHT umgesetzt -> Kunde koennte nach Lieferung widerrufen.
Kein externes Tracking/keine Cookies auf dem Kaufpfad (MEASURED: keine
Third-Party-Scripts in rtd/thanks, kein Set-Cookie von GitHub Pages).

Naechster Tick: Ticket 6 abarbeiten (datenschutz.html bauen + agb.html
ent-templatisieren mit den ECHTEN Daten aus impressum.html). Die Postanschrift
bleibt USER-Blocker — NICHT erfinden, nur an EINER Stelle offen lassen.

Belegpflicht: MEASURED (HTTP-Test, Dateiinhalt, keine erfundenen Keys).
Stopp wenn Live-Stripe-Key fehlt und nur DEMO moeglich ist.

STAND 2026-08-04 (Tick 5, MEASURED): auto_fulfill 0 Sales. rtd/thanks/index/agb/
datenschutz/impressum/sitemap HTTP 200.
TICKET 9 NEU + GESCHLOSSEN — Besucher-Messung. Zwei Befunde:
1. Der Tick startete mit `sessions=1` (vorher immer 0). Das sah nach dem ersten
   Besucher aus, war aber die EIGENE Ticket-7-Probe (payment_link=None, Feld
   'widerruf'). Beinahe-Fehlalarm.
2. Der Map-Claim "Harter Fakt: 0 Visitors" war ASSUMED. MEASURED: auf rtd.html/
   thanks.html liegt KEINE Fremdressource und KEIN Zaehler (0 Analytics-Marker)
   -> es gab nie ein Instrument. "Keine Messung" wurde als "kein Besucher" gelesen.
NEUES INSTRUMENT (gratis, gefunden statt gebaut): ein ECHTER Browser legt beim
Oeffnen eines Payment Links sofort eine checkout.session an.
  curl (ohne JS) 12:59:33Z -> HTTP 200, KEINE neue Session
  Browser         13:00:08Z -> Session, payment_link=plink_1TzrLTFajs0YddhPHUo9v1Ak
Trennmerkmal: payment_link="plink_..." = echter Browser | None = eigene API-Probe.
-> scripts/request_delivery/funnel_check.py (NEU): BESUCHER/API-PROBE/EIGENTEST
   getrennt + Conversion + --expire-own. Eigene Ids in funnel_own_sessions.json.
-> scripts/request_delivery/inspect_sessions.py (NEU): Rohansicht.
-> auto_fulfill.py: nur die Ausgabe praezisiert ("sessions=N (roh, inkl.
   Eigentests)"), Logik unveraendert; --selftest gruen, Live-Lauf gruen.
Erste echte Zahl: BESUCHER=0, bezahlt=0 -> "niemand erreicht den Kaufbutton" ist
jetzt BELEGT statt vermutet. Eigene Testsession per --expire-own geschlossen.
Nebenbefund: Kaufseite erstmals im ECHTEN Browser verifiziert (3,99 €,
Pflichtfeld "Deine Anfrage", Karte/Klarna/Amazon Pay/EPS) — bisher nur per API.
TICKET 10 NEU (OPEN, HITL): Sollen Seitenaufrufe auf rtd.html gemessen werden?
Nur damit laesst sich "niemand sieht die Seite" von "sieht sie, klickt nicht"
unterscheiden — beide fuehren zu ENTGEGENGESETZTEN Schritten. Jede Option kostet
Account + DSGVO-Nachzug auf dem Kaufpfad; "gar nicht messen" ist bei 3,99 € eine
ernsthafte Antwort. KEIN Tick baut hier eigenmaechtig Analytics ein.

Naechster Tick: Pflichtteil fahren (auto_fulfill + Live-Check) UND NEU
`python scripts/request_delivery/funnel_check.py` — das ist ab jetzt die einzige
gueltige Traffic-Aussage. Ticket 3 = USER-KYC, Ticket 5 = ab 2026-08-07,
Ticket 8 = 2 USER-Blocker, Ticket 10 = HITL. Solange BESUCHER=0 bleibt:
"warte, beobachte Sales". Aktionismus ausdruecklich NICHT erwuenscht.

Kurzer deutscher Statusbericht am Ende: was/Beleg/naechster Schritt.

STAND 2026-08-04 (Tick 4, MEASURED): auto_fulfill 0 Sales (sessions=0/paid=0/
neu=0, LIVE). rtd/thanks/agb/datenschutz/impressum HTTP 200.
TICKET 7 ERLEDIGT + GESCHLOSSEN (Commit 2d31c8c, live verifiziert):
- Gegen die LIVE-Stripe-API gemessen (probe_consent_collection.py, NEU):
  `consent_collection[terms_of_service]` IST am Payment Link unterstuetzt.
  Stripe lehnt NICHT als "unknown parameter" ab, sondern: "You cannot collect
  consent to your terms of service unless a URL is set in the Stripe Dashboard".
- ToS-URL per API setzen: UNMOEGLICH. POST /v1/accounts/<eigene id> ->
  "You cannot use this method on your own account: you may only use it on
  connected accounts." GET /v1/account enthaelt kein Feld mit "terms".
  => USER-Blocker, ~2 Min im Dashboard (Settings > Public details).
- AFK-Ersatzweg gemessen: Payment Link MIT dropdown-Pflichtfeld wird von der
  API angenommen; Wert ist als session.custom_fields[].dropdown.value lesbar
  (echte LIVE-Session angelegt + per /expire geschlossen, Probe-Links
  deaktiviert, "aktive Probe-Links uebrig: []").
- >>> ZITATFEHLER GEGENBEWIESEN, repo-weit gepurged <<<
  Fuer digitale Inhalte OHNE koerperlichen Datentraeger gilt § 356 **Abs. 6**
  BGB, NICHT Abs. 5 (Abs. 5 = Dienstleistungen). Primaerquelle
  gesetze-im-internet.de (HTTP 200), nicht aus dem Gedaechtnis zitiert.
  Abs. 6 Nr. 2 verlangt KUMULATIV a) Beginn der Erfuellung, b) Zustimmung,
  c) Kenntnisbestaetigung UND d) Bestaetigung nach § 312f auf dauerhaftem
  Datentraeger. d) = E-Mail = EMAIL_*-Blocker => der Waiver ist heute
  unerreichbar, EGAL welche Checkbox im Checkout steht.
- ENTSCHEIDUNG: die 3 LIVE-Links bleiben UNVERAENDERT. Ein Pflichtfeld mehr
  erzeugt heute nur Checkout-Reibung ohne Rechtswirkung. Stattdessen die
  auslesende Seite gebaut: auto_fulfill.extract_consent()/waiver_effective(),
  Protokoll in fulfilled_live.json UND sales.log; --selftest deckt alle 3
  realen Session-Formen ab (gruen).
- agb.html § 5 korrigiert: nennt jetzt alle vier Voraussetzungen + § 312f und
  sagt offen, dass zwei fehlen. LIVE verifiziert (HTTP 200, "356 Abs. 6 Nr. 2
  BGB" im ausgelieferten Body, 5393 B).
- verify_rtd_chain.py NACH allen Eingriffen: KETTE_OK (3 Links livemode/active,
  399/799/1499 cent = 3,99/7,99/14,99 EUR, Feld 'anfrage', Redirect ok).
  Ist-Zustand vorher gesichert: plinks_backup_2026-08-04.json (gitignored).
- Ticket 8 NEU (blockiert, NICHT auf der Frontier): Waiver scharfstellen, sobald
  ToS-URL + EMAIL_* stehen — und auch dann erst, wenn echte Sale-Daten das
  Widerrufsrisiko beziffern.

Naechster Tick: KEIN unblockiertes Ticket mit Informationswert offen.
Ticket 3 = USER-KYC, Ticket 5 = zeitgesperrt bis 2026-08-07, Ticket 8 =
2 USER-Blocker. Also: Pflichtteil (auto_fulfill + Live-Check) fahren und
"warte, beobachte Sales" melden. Aktionismus (Preise/Links/Content ohne
Messgrundlage anfassen) ist ausdruecklich NICHT erwuenscht.

Kurzer deutscher Statusbericht am Ende: was/Beleg/naechster Schritt.

STAND 2026-08-04 (Tick 6, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
ACHTUNG Beinahe-Fehlalarm #2: sessions stieg 0 -> 2. funnel_check.py sagt aber
BESUCHER=0 / API-PROBE=0 / EIGENTEST=2 -> beide Sessions sind eigene Proben
(Ticket 7 + Ticket 9). Ohne funnel_check waere daraus ein falscher
"erster Traffic"-Claim geworden. rtd/thanks/index/agb/datenschutz/impressum/
sitemap HTTP 200. verify_rtd_chain.py -> KETTE_OK (3 LIVE-Links, 399/799/1499
cent = 3,99/7,99/14,99 EUR, Feld 'anfrage', Redirect ok, Hash-Paritaet).

TICKET 11 NEU + GESCHLOSSEN — die LETZTE ungemessene Etappe des Geldpfads.
Befund: dass ein erzeugtes Deliverable wirklich live landet, war ASSUMED.
Beleg dafuer: dl/rtd/ war lokal UND im Git-Tree leer -> diesen Weg hat noch nie
eine Datei genommen. Der bisherige "Kette bewiesen"-Claim stuetzte sich auf
auto_fulfill --selftest, das mit push=False laeuft und GENAU diese Etappe
ueberspringt. Gleiche Defektklasse wie die IndexNow-Branch-Falle (11 Tage),
aber zwischen "Kunde hat bezahlt" und "Kunde bekommt Ware".
NEU: scripts/request_delivery/verify_publish_leg.py — Canary durch die ECHTEN
Produktivfunktionen (write_page/git_publish), kein Stripe-Call, keine
sales.log-Zeile, kein State, raeumt sich selbst auf.
MEASURED: 404 vor Push (Altstand ausgeschlossen) -> git_publish=True ->
unpushed=0 -> Datei im origin/gh-pages-Tree -> LIVE GET 200 nach 31s ->
LIVE HEAD 200 -> nach Cleanup wieder 404. ERGEBNIS: PUBLISH_LEG_OK.
WICHTIG: HEAD wird separat gemessen, weil thanks.html mit
fetch(...,{method:'HEAD'}) pollt — ein reiner GET-Test beweist den Kundenpfad
NICHT. Nebenbefunde: dl/rtd ist nicht gitignored (check-ignore rc=1),
gh-pages trackt origin/gh-pages (git push ohne Args zielt korrekt),
Pages-Rebuild = 31 s (Auf- und Abbau je gemessen) -> wait_live(18x10s) hat
reichlich Reserve.
=> Der Geldpfad ist jetzt auf GANZER Laenge gemessen. Beim ersten echten Sale
liegt keine ungemessene Etappe mehr im Weg.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check).
KEIN unblockiertes Ticket mit Informationswert offen: Ticket 3 = USER-KYC,
Ticket 5 = ab 2026-08-07, Ticket 8 = 2 USER-Blocker, Ticket 10 = HITL.
Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus ausdruecklich NICHT
erwuenscht.

STAND 2026-08-04 (Tick 7, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2 -> beide Sessions sind die
eigenen Proben aus Ticket 7+9, KEIN echter Traffic. rtd/thanks/index/agb/
datenschutz/impressum/sitemap HTTP 200. verify_rtd_chain -> KETTE_OK
(399/799/1499 cent), auto_fulfill --selftest gruen inkl. Tier-Fault-Injection.

TICKET 13 NEU + GESCHLOSSEN (Commit 832c69c, live verifiziert). Erstmals wurden
die TRAFFIC-Seiten so streng geprueft wie der Kaufpfad -> zwei Defekte:
A) VERWAISTE SEITEN: ein Traffic-Tick erzeugte 18:25 blog/hochzeitsrede-
   schreiben-lassen.html + blog/pitch-deck-erstellen-lassen.html samt Sitemap/
   Index/Interlink, committete aber NICHTS. 4 h spaeter live HTTP 404 und nicht
   im origin/gh-pages-Tree. Ursache: traffic_engine.py enthaelt KEINEN einzigen
   git-Aufruf -> Publizierung haengt komplett am aufrufenden Agenten.
B) DATENSCHUTZ-LINK fehlte auf 33 von 38 Seiten. Impressum + AGB waren ueberall
   vorhanden -> jede Stichprobe sah gruen aus. Art. 13 DSGVO verlangt staendige
   Verfuegbarkeit, und ein SEO-Besucher landet auf einer BLOGSEITE, nie auf der
   Startseite. Root-Cause: Footer-Template traffic_engine.py:190 -> waere bei
   jedem kuenftigen Traffic-Tick neu entstanden (Generator mitgefixt).
NEU scripts/request_delivery/legal_link_audit.py (--selftest 9/9, Fault Injection,
rc-Wechsel 1->0 belegt), add_datenschutz_link.py (patcht nur exaktes Muster,
meldet Abweichler statt blind einzufuegen), verify_ticket13_live.py.
MEASURED: Audit 33 unvollstaendig -> 0 (LEGAL_LINKS_OK). LIVE_OK: beide 404-Seiten
jetzt HTTP 200 (2390 B / 2560 B), Datenschutz-Link in 7 von 7 live abgerufenen
Bodies, Kaufpfad unveraendert 200. IndexNow 1214 URLs -> HTTP 200 (angenommen,
NICHT indexiert). Sitemap 1212 -> 1214 URLs.

MERKREGEL (dritter Fall derselben Klasse nach IndexNow-Branch und Publish-Etappe):
"gebaut" ist NIE "live". Nach jedem Traffic-Tick `git status` UND `curl` gegen die
neue URL. Und: Pflicht-Sets (Impressum/AGB/Datenschutz) nie stichprobenartig
pruefen — Teilvollstaendigkeit sieht aus wie Vollstaendigkeit.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check) UND
NEU `python scripts/request_delivery/legal_link_audit.py` (rc=1 = Defekt). Falls
ein Traffic-Tick gelaufen ist: `git status` pruefen, verwaiste Seiten publizieren.
Ticket 3 = USER-KYC, Ticket 5 = ab 2026-08-07, Ticket 8 = 2 USER-Blocker,
Ticket 10 = HITL. Solange BESUCHER=0: "warte, beobachte Sales".

STAND 2026-08-05 (Tick, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2 -> weiterhin KEIN echter
Traffic. legal_link_audit -> LEGAL_LINKS_OK (40 Seiten, 0 unvollstaendig).
verify_rtd_chain -> KETTE_OK (399/799/1499 cent, Feld 'anfrage', Redirect ok).
Traffic-Tick von heute (277830f) sauber publiziert: beide neuen Landingpages
live 200 + in der Sitemap, Datenschutz-/rtd-Link je vorhanden -> die
"Generator-publiziert-nicht"-Falle hat gegriffen. git clean, 0 unpushed.

TICKET 14 NEU + GESCHLOSSEN (Commit gepusht, im origin/gh-pages-Tree).
>>> NEUE FALLE: FETTES 404 <<<
Die 404-Seite von GitHub Pages ist 9379 B gross - FETTER als jede echte
Landingpage (2390-3683 B MEASURED). Zwei geratene URLs lieferten je 9379 B und
sahen nach gesunden Seiten aus, waren aber 404. KONSEQUENZ: `curl | wc -c` ist
als "ist live"-Beleg WERTLOS, und jede "duenne Seite = kaputt"-Heuristik zeigt
falsch herum. Ab sofort nur noch `curl -o /dev/null -w '%{http_code}'`.
Befund: sitemap_healthcheck.py war das EINZIGE Verifikationsskript ohne
--selftest -> sein "1207 URLs, 0 Defekte" vom 04.08. war streng genommen
ASSUMED (niemand hatte gezeigt, dass es einen Defekt ueberhaupt bemerkt).
Inhaltlich war es korrekt (prueft echte Statuscodes via HTTPError), aber das
war Code-Lektuere, kein Test.
Fix: --selftest mit Fault Injection durch die ECHTE main() (injizierte Sitemap,
Produktivpfad) -> 13/13 SELFTEST_OK, rc-Wechsel 1->0 belegt, Rot-Faelle
zusaetzlich auf 'Traceback' gefiltert (Exit-Code-Falle), DUENN-Zweig und
Netzfehler(-1) mitgetestet.
Vollzaehliger Lauf mit dem nun vertrauenswuerdigen Instrument:
1216/1216 HTTP 200, NICHT_200=0, VERDAECHTIG_KLEIN=0, SITEMAP_OK (21,8 s).
Sitemap lokal = live = 1216, 0 Drift.
IndexNow danach: Key-Datei HTTP 200 (Body == Dateiname), 1216 URLs -> HTTP 200,
SUBMIT_OK. Wie immer: ANGENOMMEN, NICHT indexiert.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit). NEU verfuegbar: `python scripts/sitemap_healthcheck.py
--selftest` (13/13) und der Vollauf (~22 s) - nach jedem Traffic-Tick sinnvoll,
sonst nicht noetig. Ticket 3 = USER-KYC, Ticket 5 = ab 2026-08-07 (dann faellt
die Zeitsperre! Bing-Trefferzahl messen), Ticket 8 = 2 USER-Blocker,
Ticket 10 = HITL. Solange BESUCHER=0: "warte, beobachte Sales".
Aktionismus ausdruecklich NICHT erwuenscht.



STAND 2026-08-05 (Tick 2, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, jetzt zusaetzlich
"vollzaehlig=ja". legal_link_audit LEGAL_LINKS_OK (40 Seiten). verify_rtd_chain
KETTE_OK (399/799/1499 cent). rtd/thanks/index/agb/datenschutz/impressum/
sitemap HTTP 200.

TICKET 15 NEU + GESCHLOSSEN — der Besucher-Zaehler war selbst ungeprueft.
>>> CLAIM AUS TICKET 14 GEGENBEWIESEN <<<
Ticket 14 sagte, sitemap_healthcheck.py sei das EINZIGE Verifikationsskript ohne
--selftest. Vollzaehlig ueber alle 38 Skripte gegrept: es fehlten AUCH
funnel_check.py, verify_rtd_chain.py und verify_ticket13_live.py. Dieselbe
Teil-Vollstaendigkeits-Falle wie Ticket 13, diesmal auf die eigene Werkzeugkiste.
Brisanz: funnel_check.py hat in seiner ganzen Lebenszeit NUR die Zahl 0
ausgegeben. Niemand hatte gezeigt, dass es hochzaehlen KANN — bei verdrehtem
classify() saehe die Ausgabe identisch aus und der erste echte Besucher (=
Signal fuer den ersten Sale) waere unbemerkt durchgerutscht.
ECHTER DEFEKT gefunden (nicht nur fehlender Test): main() las
`checkout/sessions?limit=100` und ignorierte Stripes `has_more` (MEASURED: Feld
existiert, aktuell False). Ab Session 101 haette der einzige Traffic-Zaehler
still zu wenig gemeldet — also genau dann scharf geworden, wenn endlich Traffic
da ist. Dritter Befund: payment_status=None haette die Detailausgabe mit
TypeError abgeraeumt.
FIX: Pagination via starting_after (fetch_all_sessions), ehrliche Untergrenze
statt falscher Zahl (vollzaehlig=NEIN + rc=3, wenn has_more nicht abreisst),
str() um payment_status, und --selftest mit Fault Injection durch die ECHTE
main() (kein Reimplementat, nur die Stripe-Antwort wird injiziert).
MEASURED: 13/13 SELFTEST_OK. Rot-Probe _mutation_probe_t15.py mutiert den
PRODUKTIVCODE: 3/3 Mutanten rot, kein Traceback, Datei sha256-genau
wiederhergestellt, rc-Wechsel 0->1->0 -> MUTATION_PROBE_OK. Mutant 1 ist der
heute real gefundene Pagination-Defekt: der neue Test haette ihn gefangen.
=> BESUCHER=0 ist ab jetzt eine GEMESSENE Null, keine unbelegte.
Ehrliche Grenze: die Ticket-9-Praemisse "echter Browser => Session mit
payment_link" beruht weiter auf EINER Stichprobe -> der Zaehler ist eine
UNTERGRENZE der Besucher, kein Vollzaehler.

TICKET 16 NEU (OFFEN, AFK, unblockiert) = naechster Tick:
verify_rtd_chain.py hat KEINEN --selftest, spricht aber mit "KETTE_OK" den
Geldpfad gesund. Dass es einen Defekt BEMERKT, ist unbewiesen. Vorgehen steht in
tickets/16-verify-rtd-chain-selftest.md (Rot-Faelle: Link inaktiv, livemode
False, Preis 0, Pflichtfeld weg, falscher Redirect, Hash-Bruch, 0 Links; alles
gegen injizierte Antworten — die 3 LIVE-Links NICHT anfassen).

MERKREGEL (Ungeprueft-Pruefer-Falle): Ein Zaehler, der immer nur denselben Wert
ausgibt, ist nie beim Zaehlen beobachtet worden. Und Vollstaendigkeits-Claims
ueber die eigene Werkzeugkiste per Grep ueber ALLE Skripte pruefen, nie aus der
Erinnerung.

Naechster Tick: Pflichtteil (auto_fulfill + funnel_check + Live-Check +
legal_link_audit) UND Ticket 16 abarbeiten. Ticket 3 = USER-KYC, Ticket 5 = ab
2026-08-07, Ticket 8 = 2 USER-Blocker, Ticket 10 = HITL.
