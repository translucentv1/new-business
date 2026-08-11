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

STAND 2026-08-05 (Tick 3, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja.
legal_link_audit LEGAL_LINKS_OK (40 Seiten, 0 unvollstaendig). rtd/thanks/index/
agb/datenschutz/impressum/sitemap HTTP 200.

TICKET 16 ERLEDIGT + GESCHLOSSEN — der Torwaechter des Geldpfads war blind.
>>> ZWEI ECHTE DEFEKTE, nicht nur ein fehlender Test <<<
A) LEERE-SCHLEIFE-FALLE: verify_rtd_chain.py startete mit ok=True und setzte ok
   NUR innerhalb der Link-Schleife. Bei 0 gefundenen buy.stripe.com-Links lief
   sie null Mal -> "KETTE_OK" fuer eine Kaufseite OHNE Kaufmoeglichkeit.
   AM ALT-STAND AUSGEFUEHRT (nicht argumentiert): _mutation_probe_t16.py holt
   ad891dc per `git show`, faehrt dessen echte main() gegen eine linklose
   rtd.html -> rc=0, "KETTE_OK -> war BLIND".
B) BEHAUPTUNGS-ETAPPE: Schritt [3] "Hash-Paritaet" hat thanks.html NIE geoeffnet.
   Es druckte nur den Satz "-> Paritaet gegeben, da beide SHA-256/[:16] nutzen".
   Ein slice(0,15) oder SHA-1 im JS haette den ZAHLENDEN Kunden auf eine 404
   gepollt (auto_fulfill schreibt <python-hash>.html, Browser fragt <js-hash>),
   waehrend der Pruefer gruen bleibt.
FIX: [3] extrahiert die 3 JS-Zeilen aus der ausgelieferten thanks.html und
FUEHRT SIE IN NODE AUS (v24.18.0 vorhanden) statt den Algorithmus nachzubauen;
0 Links und "Link-Anzahl != Preis-Optionen" sind jetzt rot (Soll-Zahl aus der
Datei selbst: eine <option value=> pro Link); Pagination bei payment_links
(Ticket-15-Klasse); NEUES drittes Ergebniswort KETTE_UNGEPRUEFT (rc=2) fuer
"nicht messbar" (z.B. node fehlt) — weder gruen noch Defekt-Claim.
MEASURED: --selftest 16/16 SELFTEST_OK (alle Rot-Faelle durch die ECHTE main(),
gegen 'Traceback' gefiltert), _mutation_probe_t16.py MUTATION_PROBE_OK
(Alt-Stand-Probe + 4/4 Mutanten rot, sha256-genaue Wiederherstellung,
rc-Wechsel 0->1->0). Echter LIVE-Lauf danach: KETTE_OK, Hash-Paritaet erstmals
GEMESSEN (js und python -> dl/rtd/c4058a6e2eaf7e0c.html). Die 3 LIVE-Links
wurden nur gelesen, nie veraendert. Lint (uvx ruff, nur eigener Code): 9 -> 4
Findings, Rest Alt-Bestand/bewusst.

MERKREGELN (neu):
- Leere Eingabe MUSS rot sein. Jeder Pruefer mit ok=True + Schleife ist
  verdaechtig; Soll-Menge wenn moeglich aus der Quelle selbst ableiten.
- Pruef-Output nach Saetzen absuchen, die eine BEGRUENDUNG statt eines MESSWERTS
  enthalten ("da", "entspricht", "ist damit") — das sind Behauptungs-Etappen.
- "nicht messbar" braucht ein eigenes Ergebniswort, sonst wird es als gruen
  oder als Defekt fehlgelesen.

TICKET 17 NEU (OFFEN, AFK, unblockiert, NIEDRIGE Prioritaet):
verify_ticket13_live.py ist das LETZTE Verifikationsskript ohne --selftest
(Rechtslinks, nicht Geldpfad). Vorgehen in tickets/17-verify-ticket13-live-
selftest.md. Nur nehmen, wenn nichts mit hoeherem Informationswert offen ist.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit). Ticket 3 = USER-KYC, Ticket 5 = ab 2026-08-07 (Zeitsperre
faellt uebermorgen), Ticket 8 = 2 USER-Blocker, Ticket 10 = HITL, Ticket 17 =
optional. Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus
ausdruecklich NICHT erwuenscht.

STAND 2026-08-05 (Tick 4, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK (42 Seiten, 0 unvollstaendig).
verify_rtd_chain KETTE_OK (399/799/1499 cent, Feld 'anfrage', Redirect ok,
Hash-Paritaet real gemessen). rtd/thanks/index/agb/datenschutz/impressum/sitemap
HTTP 200.

TICKET 17 ERLEDIGT + GESCHLOSSEN (Commit 3383e8f, 0 unpushed, im origin-Tree).
>>> ZWEI ECHTE DEFEKTE, nicht nur ein fehlender Test <<<
A) EINGEFRORENE STICHPROBE: verify_ticket13_live.py prueste live nur 7 hart-
   kodierte Seiten, waehrend legal_link_audit im Baum 42 kennt -> 35 Seiten nie
   live geprueft. Da traffic_engine.py laufend neue Landingpages erzeugt, waere
   JEDE kuenftige Traffic-Seite am Live-Check vorbeigelaufen. Ausgerechnet das
   Skript gegen die Teil-Vollstaendigkeits-Falle war selbst eine Stichprobe.
B) EIN PFLICHTLINK STATT DREI: NEEDLE = "datenschutz.html" -> Impressum und AGB
   wurden im ausgelieferten Body NIE gesucht, obwohl das Skript genau dafuer da ist.
AM ALT-STAND AUSGEFUEHRT (nicht argumentiert), _mutation_probe_t17.py:
   A1 Alt-Stand 68946f0 + 404 auf blog/arbeitszeugnis-... -> rc=0 "LIVE_OK -> BLIND"
   A2 Alt-Stand + index.html live OHNE Impressum-Link      -> rc=0 "LIVE_OK -> BLIND"
   Neue Fassung gegen dieselbe Auslieferung: rc=1 LIVE_DEFEKT, Seite benannt.
FIX: Zielmenge wird aus dem Baum ABGELEITET (gleiche Exempt-Regel wie das Audit,
sonst driften die zwei Pruefer), alle 3 Pflichtlinks, Soft-404 (HTTP 200 mit
"Page not found" im Body) ist rot, leere Zielmenge NICHT gruen, drittes
Ergebniswort LIVE_UNGEPRUEFT (rc=2) fuer Netzfehler -- echter Defekt schlaegt
Unmessbarkeit. urllib.error explizit importiert (ging vorher nur zufaellig).
MEASURED: --selftest 18/18 SELFTEST_OK, MUTATION_PROBE_OK (4/4 Mutanten rot,
sha256-genaue Wiederherstellung, rc-Wechsel 0->1->0), echter Live-Lauf LIVE_OK
ueber 47 Seiten in 1,2 s (8 Threads), unabhaengige Gegenmessung 42/42 Seiten
live HTTP 200 MIT allen 3 Rechtslinks.

>>> TICKET-PRAEMISSE FALSIFIZIERT <<<
Ticket 17 hiess "der LETZTE Pruefer ohne Selftest". Vollzaehlig gegrept stimmt
das nicht: scripts/verify.py nennt sich selbst "kanonische Verifikation",
laeuft mit 56 Checks gruen (MEASURED: 56 ok, 0 fail, rc=0) und hat KEINEN
--selftest. Dritter Fall derselben Klasse (Ticket 14 -> 15 -> 17).
-> TICKET 18 NEU (OFFEN, AFK, unblockiert, mittlere Prioritaet):
   tickets/18-verify-py-selftest.md

MERKREGELN (neu):
- Zielmengen aus der Quelle ABLEITEN, nie hartkodieren. Eine hartkodierte
  Pruefliste veraltet still, waehrend der Baum waechst.
- Zwei Pruefer, die dieselbe Menge meinen, muessen dieselbe Ableitungsregel
  benutzen, sonst driften sie auseinander.
- Pflicht-SETS vollzaehlig pruefen, nicht ein Merkmal daraus ("zu wenige
  Merkmale pro Seite" ist dieselbe Falle wie "zu wenige Seiten").
- Rot-Faelle gegen die EXAKTE Diagnosezeile assertieren, nicht gegen ein
  Stichwort -- sonst besteht der Test auch bei Rot aus dem falschen Grund.
- Grep ueber alle Skripte reicht nicht: jeden Treffer einordnen in stehendes
  Tor (braucht Selftest) vs Ad-hoc-Sonde (braucht keinen).

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + NEU `python scripts/request_delivery/verify_ticket13_live.py`,
laeuft jetzt in 1,2 s und deckt alle Seiten ab). Dann Ticket 18 abarbeiten.
Ticket 3 = USER-KYC, Ticket 5 = ab 2026-08-07 (Zeitsperre faellt uebermorgen),
Ticket 8 = 2 USER-Blocker, Ticket 10 = HITL.
Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus NICHT erwuenscht.

STAND 2026-08-05 (Tick 5, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK (44 Seiten, 0 unvollstaendig).
verify_ticket13_live LIVE_OK (49 Seiten vollzaehlig). verify_rtd_chain KETTE_OK
(399/799/1499 cent, Feld 'anfrage', Redirect ok, Hash-Paritaet real gemessen).
rtd/thanks/index/agb/datenschutz/impressum/sitemap HTTP 200.

TICKET 18 ERLEDIGT + GESCHLOSSEN (Commit d5e0f79, im origin/gh-pages-Tree,
0 unpushed). Der Tick startete mit UNCOMMITTETER Arbeit aus dem Vortick
(verify.py modifiziert + 2 untracked Dateien) - alle Claims wurden NEU
ausgefuehrt, nicht uebernommen.
>>> DREI ECHTE DEFEKTE, nicht nur ein fehlender Test <<<
Alle drei AM ALT-STAND AUSGEFUEHRT (_mutation_probe_t18.py holt HEAD:scripts/
verify.py per `git show` und faehrt dessen echte main()):
A1) STILLE SCHRUMPFUNG (schwerster Befund): der Deckungs-Check der Blogseiten
    sah nur te.KEYWORDS[0] an. KEYWORDS von 37 auf 1 gekuerzt -> rc=0,
    "20 ok, 0 fail" -> GRUEN, obwohl 36 Seiten gar nicht mehr geprueft wurden.
    "56 ok" war damit nie eine feste Pruefflaeche, sondern eine tree-abhaengige
    Zahl, in der ein Deckungsverlust wie ein bestandener Lauf aussieht.
A2) NETZAUSFALL ALS DEFEKT-CLAIM: --live kannte kein drittes Ergebniswort und
    druckte bei totem Netz "FAIL  live: ..." -> Defekt-Vorwurf gegen eine
    gesunde Seite. Ausgerechnet im breitesten Pruefer fehlte die Konvention
    aus Ticket 16/17.
A3) ERGEBNISLISTEN OHNE RESET: zwei main()-Laeufe im selben Prozess -> 58 ->
    116 ok. EHRLICH: produktiv wird main() einmal gerufen -> LATENT, haette
    aber jede Harness um dieses Tor still verfaelscht.
FIX: --selftest mit Fault Injection durch die ECHTE main() (scripts/
_verify_selftest.py), Deckung ueber ALLE Keywords, leere Keyword-Liste ist rot
(Alt-Stand lief dort in IndexError), drittes Ergebniswort VERIFY_UNGEPRUEFT
(rc=2) mit Vorrang fuer echte Defekte, Reset pro Lauf, und GELTUNGSBEREICH wird
gedruckt ("lokaler Baum (kein Netz)" vs "+ LIVE-Auslieferung") - vorher las sich
ein Baum-Gruen wie ein Live-Gruen.
MEASURED: 30/30 SELFTEST_OK. MUTATION_PROBE_OK 11/11 (3 Alt-Stand-Proben +
5/5 Mutanten rot mit exakter Diagnosezeile, sha256-genau wiederhergestellt
a6b7e8cdaf122005, rc-Wechsel 0->1->0). Echte Laeufe: 65 ok offline / 72 ok live,
0 fail, 0 ungeprueft. Der Mutant "check() kann nicht mehr rot werden" erzeugt
20 Rot-Meldungen -> 20 Checks sind nachweislich rot-faehig.

>>> "56 ok"-CLAIM KORRIGIERT <<<
Die Zahl ist tree-abhaengig (heute 65 offline / 72 live) und war NIE ein
Deckungsbeweis. In wayfinder_map.md gepurged. Dated Tick-Logs in docs/
(ai_ceo_report.md, fiverr_gig.md) bleiben stehen - das waren zum jeweiligen
Datum korrekte Messungen, keine falschen Behauptungen.

TICKET 19 NEU (OFFEN, AFK, unblockiert, HOHE Prioritaet) = naechster Tick:
tickets/19-indexnow-submit-selftest.md
Vollzaehlig ueber ALLE 43 Skripte gegrept (nicht aus der Erinnerung): 30 ohne
--selftest, davon drucken nur 3 ein Ergebniswort. Zwei davon sind Ad-hoc-Sonden
(measure_tier_diff.py = Einmalmessung Ticket 12, probe_consent_collection.py =
Einmalprobe Ticket 7) -> brauchen keinen. Bleibt indexnow_submit.py als das
LETZTE stehende Tor ohne Selftest. Es druckt SUBMIT_OK und ist der EINZIGE
autonome Traffic-Hebel - und genau dieser Pfad war schon einmal 11 Tage tot,
waehrend alles gruen aussah (Ticket 4).
EHRLICHER AUSGANGSBEFUND (Code-Lektuere, KEIN Test): die Struktur liest sich
defensiv - http() faengt HTTPError UND Netzfehler, check_key_live() vergleicht
den Body exakt, main() hat getrennte Zweige KEY_NICHT_LIVE/KEINE_URLS/
SUBMIT_403/SUBMIT_FEHLER. Gleiche Lage wie sitemap_healthcheck.py vor Ticket 14:
inhaltlich vermutlich korrekt, aber unbewiesen. Nicht zu viel erwarten.
Wahrscheinlichster Schwachpunkt: all() ueber MEHRERE Batches (gemischte Codes).
WICHTIG: Selftest darf KEINE echte Einreichung ausloesen (nur injizierte
Antworten). Ticket 19 VOR Ticket 5 fahren - ist der Einreicher blind, misst
Ticket 5 am 07.08. eine Wirkung ohne Ursache.

MERKREGELN (neu):
- Eine Pruef-ZAHL ist kein Deckungsbeweis. "N ok" waechst und schrumpft mit dem
  Baum; ein Pruefer muss die VOLLSTAENDIGKEIT seiner Zielmenge behaupten und rot
  werden, wenn sie schrumpft - sonst sieht weniger Pruefen aus wie Bestehen.
- Geltungsbereich IMMER drucken (Baum vs Auslieferung). Sonst liest sich ein
  Baum-Gruen wie ein Live-Gruen - dieselbe Verwechslung wie die Branch-Falle.
- Uncommittete Arbeit aus einem Vortick ist ein ASSUMED-Claim: neu ausfuehren,
  nicht uebernehmen. (Hier hat sie gehalten - aber gemessen, nicht geglaubt.)

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live). Dann TICKET 19 abarbeiten.
Ticket 3 = USER-KYC, Ticket 5 = ab 2026-08-07 (nach Ticket 19!), Ticket 8 =
2 USER-Blocker, Ticket 10 = HITL. Solange BESUCHER=0: "warte, beobachte Sales".
Aktionismus ausdruecklich NICHT erwuenscht.

STAND 2026-08-05 (Tick 6, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja.
legal_link_audit LEGAL_LINKS_OK (44 Seiten). verify_ticket13_live LIVE_OK
(49 Seiten). verify_rtd_chain KETTE_OK (Hash-Paritaet real gemessen).
rtd/thanks/index/sitemap/agb/datenschutz/impressum + IndexNow-Key HTTP 200.

TICKET 19 ERLEDIGT + GESCHLOSSEN (Commit 6d1e79d, gepusht, 0 unpushed, alle
4 Dateien im origin/gh-pages-Tree).
>>> FUENF ECHTE DEFEKTE, alle AM ALT-STAND AUSGEFUEHRT <<<
(_mutation_probe_t19.py holt HEAD per `git show` und faehrt dessen echte main())
A1 URL lokal gelistet, live nicht vorhanden -> SUBMIT_OK rc=0: der Einreicher
   haette eine 404-URL bei Bing gemeldet (genau das entwertet einen IndexNow-Key).
A2 lokale Sitemap 3 -> 1 URL geschrumpft -> SUBMIT_OK (stille Schrumpfung).
A3 Netz/DNS tot -> "KEY_NICHT_LIVE": Defekt-Vorwurf gegen die eigene, live
   kerngesunde Key-Datei (HTTP 200 gemessen).
A4 codes=[500,403] -> "SUBMIT_403 (kein URL-Fehler)": der echte 500er wurde
   vom 403 MASKIERT.
A5 Netzfehler beim Senden -> "SUBMIT_FEHLER" statt "unmessbar".
>>> TICKET-HYPOTHESE WIDERLEGT <<< Vermutet war all() ueber mehrere Batches als
wahrscheinlichster Schwachpunkt. Am Alt-Stand ausgefuehrt: [200,500] wird
KORREKT rot. Der Batch-Pfad war gesund, die Loecher lagen woanders.
FIX: drittes Ergebniswort INDEXNOW_UNGEPRUEFT (rc=2), 403 auf rc=3 (kein
Aufrufer hing an rc=2 - vollzaehlig gegrept), Reihenfolge echter Defekt >
unmessbar > 403 > OK, Geltungsbereich-Pruefung gegen die LIVE-Sitemap
(INDEXNOW_DRIFT rc=1 OHNE Einreichung; --allow-drift reicht nur die
Schnittmenge ein), leere Code-Liste rot, vollzaehlig=ja/nein im Output.

>>> DER SCHWERSTE BEFUND KAM VOM ECHTEN LAUF, NICHT VOM SELFTEST <<<
Erster Live-Lauf nach dem Fix: "INDEXNOW_DRIFT lokal=1220 live=3" gegen eine
kerngesunde Site (curl sitemap.xml | grep -c "<loc>" = 1220 live UND lokal).
Ursache: http() kuerzt JEDEN Body auf 400 Zeichen -> die Live-Sitemap kam als
3 URLs an. Der Selftest war 106/106 gruen, weil die ATTRAPPE UNGEKUERZT
lieferte - grosszuegiger als die Realitaet. Behoben an beiden Enden:
http(..., maxlen=None) fuer Dokumente, FakeNet kuerzt jetzt nach derselben
Regel; neuer 60-URL-Fall; Mutant M7 stellt genau diesen Defekt wieder her.
Vollzaehlig nachgegrept: alle uebrigen [:N]-Kuerzungen im Repo betreffen
FEHLERMELDUNGEN, keine geparsten Dokumente -> Klasse ist eingegrenzt.
Zwei Schwaechen im eigenen frischen Selftest selbst gefunden und behoben:
Substring-Vergleich ("SUBMIT_OK" matcht auch "SUBMIT_OK_TEILMENGE") -> jetzt
exaktes erstes Token; und eine tautologische Zeile t(x or True, ...) entfernt.

MEASURED: 106/106 SELFTEST_OK | MUTATION_PROBE_OK 29/29 (5 Alt-Stand-Proben +
Gegenprobe der neuen Fassung + 7/7 Mutanten rot ohne Traceback, sha256-genaue
Wiederherstellung, rc-Wechsel 0->1->0) | echter Lauf SUBMIT_OK: key HTTP 200
(Body==Key), lokal 1220 == live 1220, drift 0, vollzaehlig=ja, 1220 URLs ->
HTTP 200 | verify.py VERIFY_OK (66 ok, 0 fail). Selftest loest KEINE echte
Einreichung aus (Attrappe protokolliert jeden Aufruf).
WIE IMMER: 200 = ANGENOMMEN, NICHT INDEXIERT.

MERKREGELN (neu):
- ATTRAPPEN-FALLE: eine Attrappe, die grosszuegiger ist als die echte Funktion,
  macht den Selftest blind. Attrappen muessen den VERTRAG nachbilden - inkl.
  Kuerzung, Timeouts, Fehlerformen. Und: einen echten Lauf NIE durch einen
  gruenen Selftest ersetzen.
- Ergebniswoerter mit gemeinsamem Praefix exakt vergleichen (erstes Token der
  ERGEBNIS-Zeile), nie per `in` - "SUBMIT_OK" matcht "SUBMIT_OK_TEILMENGE".
- Selbstgeschriebene Checks auf Tautologien absuchen (`t(x or True, ...)`
  zaehlt in die Quote, kann aber nie rot werden).

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live). AB 2026-08-07: TICKET 5 (Bing-
Trefferzahl) - die Zeitsperre faellt dann, und die Vorbedingung ist jetzt
erfuellt (der Einreicher ist nachweislich rot-faehig und hat 1220/1220 URLs
gegen die LIVE-Auslieferung eingereicht). Ticket 3 = USER-KYC, Ticket 8 =
2 USER-Blocker, Ticket 10 = HITL. Kein unblockiertes AFK-Ticket mit
Informationswert mehr offen -> bis zum 07.08.: "warte, beobachte Sales".
Aktionismus ausdruecklich NICHT erwuenscht.

STAND 2026-08-06 (Tick, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK (46 Seiten, 0 unvollstaendig).
verify_ticket13_live LIVE_OK (51 Seiten). verify_rtd_chain KETTE_OK (Hash-Paritaet
real gemessen). verify.py VERIFY_OK (68 ok, 0 fail). rtd/thanks/index/agb/
datenschutz/impressum/sitemap HTTP 200.

Der Tick startete mit UNCOMMITTETER Arbeit aus dem Vortick (verify_publish_leg.py
modifiziert + _mutation_probe_t20.py + _probe_indexability.py untracked). Nach
Merkregel neu AUSGEFUEHRT statt uebernommen - sie hat gehalten.

TICKET 20 NEU + GESCHLOSSEN (Commit c931e44, 0 unpushed, im origin/gh-pages-Tree).
>>> ERSTMALS KEIN PRUEFER, SONDERN DIE WARE SELBST WAR DEFEKT <<<
A) DER SCHUTZ LAG AM FALSCHEN ORT (Branch-Fallen-Klasse, 2. Fall):
   https://translucentv1.github.io/robots.txt              -> HTTP 404
   https://translucentv1.github.io/new-business/robots.txt -> HTTP 200
                                                   (mit "Disallow: /dl/")
   Ein Crawler liest robots.txt NUR am Origin. Primaerquelle frisch abgerufen
   (rfc-editor.org HTTP 200), NICHT aus dem Gedaechtnis: RFC 9309 §2.3 "MUST be
   accessible in a file named '/robots.txt' ... in the top-level path of the
   service"; §2.3.1.3: 4xx = "Unavailable" -> "the crawler MAY access any
   resources". => ADR-0013 war seit Bestehen wirkungslos.
B) DAMIT IST meta robots DER EINZIGE SCHUTZ - UND ER FEHLTE FAST UEBERALL:
   24 dl-HTML-Deliverables, davon 1 mit noindex -> 23 OFFEN. LIVE gegengemessen:
   HTTP 200 robots=[KEIN] fuer frankenstein.html (436 KB), wuthering-heights.html
   (683 KB), emma.html (923 KB), einkommensteuer-ausfuellhilfe.html - vollstaendige
   BEZAHLTE Produkte, indexierbar ausgeliefert.
   Warum nie aufgefallen: die eine gepruefte Stelle (auto_fulfill-Template fuer
   rtd) TRUG das noindex -> Teil-Vollstaendigkeits-Falle zum VIERTEN Mal
   (T13 Rechtslinks -> T15 Werkzeugkiste -> T17 Stichprobe -> jetzt die Ware).
FIX: verify_publish_leg.py prueft jetzt den LIVE ausgelieferten BODY (vorher nur
Statuscodes). NEU scripts/request_delivery/dl_noindex_audit.py = stehendes Tor
(Zielmenge aus dem Baum abgeleitet, --live misst die Auslieferung, --fix patcht
nur am exakten charset-Anker und MELDET Abweicher statt zu raten, drittes
Ergebniswort DL_UNGEPRUEFT rc=2, leere Zielmenge NICHT gruen).
MEASURED: verify_publish_leg --selftest 12/12 | _mutation_probe_t20.py
MUTATION_PROBE_OK 3/3 (Produktivcode mutiert, sha256-genau restauriert) | echter
Publish-Lauf PUBLISH_LEG_OK mit "LIVE meta robots = noindex,nofollow", GET+HEAD
200 nach 31 s | dl_noindex_audit --selftest 16/16 | vor dem Fix
DL_NOINDEX_DEFEKT (23 offen, rc=1) | nach Push DL_NOINDEX_OK gegen die
LIVE-Auslieferung (24/24, rc=0) | KETTE_OK + VERIFY_OK ohne Regression.
INTEGRITAETSSONDE (weil bezahlte Ware massenhaft gepatcht wurde):
_probe_patch_integrity_t20.py zieht den Tag wieder ab und vergleicht gegen den
alten Blob -> PATCH_INTEGRITAET_OK 23/23, Inhalt unveraendert (Delta exakt
+50 B bzw. +47 B = nur der Tag).

TICKET 21 NEU (OFFEN, HITL): 14 .epub-Dateien unter /dl/ sind binaer und koennen
KEIN meta robots tragen. Entlastend MEASURED: 16-stellige Hash-URLs, 0 Treffer in
der Live-Sitemap, IndexNow filtert /dl/ heraus. Die wirksamste Option (User-Pages-
Repo translucentv1.github.io mit echtem Origin-robots.txt) legt ein Repo im
GitHub-Account des Nutzers an -> KEIN Cron-Tick entscheidet das eigenmaechtig.

MERKREGELN (neu):
- Ein Schutz gilt nur dort, wo der Konsument ihn liest. Bei jedem Schutz zuerst
  fragen: WER liest ihn und VON WO? - und genau dort messen. Eine Datei am
  falschen Ort liefert HTTP 200 und schuetzt trotzdem nichts.
- Statuscode != Inhalt. GET/HEAD 200 beweist DASS etwas ausgeliefert wird, nie WAS.
- Massen-Patches auf bezahlte Ware brauchen eine Integritaetssonde (Tag wieder
  abziehen, gegen alten Blob vergleichen). "Skript lief fehlerfrei" ist kein Beleg.
- Eigentor als Warnung: die erste Korruptionspruefung war selbst kaputt
  (grep -c ... || echo 0 haengt bei Count 0 eine zweite Null an) und meldete 23
  falsche Treffer. Eine Pruefung, die ALLES rot meldet, ist genauso verdaechtig
  wie eine, die alles gruen meldet.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live) UND NEU
`python scripts/request_delivery/dl_noindex_audit.py --live` (rc=1 = bezahlte
Ware indexierbar) - nach jedem Fulfillment sinnvoll.
TICKET 5 IST NOCH GESPERRT — der vorige Tick hat sich um einen Tag vertan:
er lief am 2026-08-06 und schrieb "AB HEUTE FREI ... Zeitsperre 2026-08-07 ist
gefallen". Die Sperre lautet "nicht vor 2026-08-07" (tickets/5-...md Z. 4+36),
faellt also erst MORGEN. Vorbedingung ist erfuellt (Einreicher rot-faehig,
1220/1220 URLs live eingereicht) - die Zeit ist es nicht.
Ticket 3 = USER-KYC, Ticket 8 = 2 USER-Blocker, Ticket 10 = HITL, Ticket 21 = HITL.
Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus NICHT erwuenscht.

STAND 2026-08-06 (Tick 4, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK. verify_ticket13_live
LIVE_OK (55 Seiten). dl_noindex_audit --live DL_NOINDEX_OK (24/24).
verify_rtd_chain KETTE_OK. verify.py VERIFY_OK (72 ok, 0 fail).
rtd/thanks/index/agb/datenschutz/impressum/sitemap HTTP 200.

Der Tick startete mit UNCOMMITTETER Arbeit (cron_health_audit.py, 586 Zeilen,
untracked). Nach Merkregel NEU AUSGEFUEHRT statt uebernommen - sie hat
gehalten, war aber unvollstaendig (siehe unten).

TICKET 24 ERLEDIGT + GESCHLOSSEN (Commit aad9c22, gepusht, 0 unpushed, alle
Dateien im origin/gh-pages-Tree).
>>> DER BEFUND WAR NICHT DER FEHLENDE TEST, SONDERN WER DAS TOR OEFFNET <<<
cron_health_audit.py war fertig und gruen - aber es waere nur gelaufen, wenn
ein AGENTEN-Tick daran denkt. Genau diese Bauform ist in Ticket 22 gestorben
(143 Laeufe tot). Der aufrufende Tick-Job 87a15fe059fc steht bei 27 completed
/ 22 failed. Ein Audit "wenn jemand daran denkt" ist derselbe Fehler eine
Ebene hoeher.
FIX: Etappe [3] in cron_auto_fulfill.py -> das Tor laeuft jetzt ALLE 30 MIN
unbeaufsichtigt und OHNE Inferenz-Call mit. hrc==1 -> RTD_FULFILL_DEFEKT
(Job wird in executions.db rot), hrc sonst !=0 -> UNGEPRUEFT (nie ein
Defekt-Claim gegen den Geldpfad).
BEINAHE-REGRESSION IM EIGENEN UMBAU: der Defekt-Zweig steht VOR dem
Sale-Zweig -> ein Cron-Health-Defekt haette die "*** ERSTER SALE ***"-Meldung
VERSCHLUCKT. Banner jetzt immer vor der Verzweigung; Mutant F3 stellt den
Fehler wieder her und faellt.
MEASURED: cron_health_audit --selftest 25/25 | cron_auto_fulfill --selftest
14/14 -> 21/21 | _mutation_probe_t24.py MUTATION_PROBE_OK 17/17 mit 11 roten
Mutanten in 2 Produktivdateien (exakte Diagnosezeile, kein Traceback, beide
sha256-genau restauriert a34ecbbc1ecc2aff / e99a326a6ffafa67, rc-Wechsel
0->1->0) | echter Lauf cron_health_audit CRON_HEALTH_OK (14 Jobs / 6 enabled,
1 Geldpfad-Traeger, 30-min-Takt, 168 Laeufe / 23 completed) | echter Lauf
cron_auto_fulfill RTD_FULFILL_OK mit [3] CRON_HEALTH_OK | ECHTER JOB-LAUF
`hermes cron run bfb63346d942` -> "Ran now: succeeded", DB completed
(Bilanz 24 completed / 144 failed / 1 unknown), Ausgabedatei
2026-08-06_20-44-29.md enthaelt "Mode: no_agent (script)",
"[3] Cron-Gesundheit (Ticket 24)" und "CRON_HEALTH_OK".
EIGENTOR IN DER SONDE (selbst gefunden): der Traceback-Filter durfte NICHT
auf das blosse Wort "Traceback" pruefen - der Selftest hat ein Pruef-LABEL
"kein Traceback im Gruen-Fall", wodurch der kerngesunde Baseline-Lauf als
abgestuerzt gemeldet wurde. Jetzt gegen die echte Kopfzeile
"Traceback (most recent call last)". Gleiche Klasse wie die Praefix-Falle
aus Ticket 19.
MESSFALLE: `python x.py | tail` gibt in $? den rc von TAIL zurueck, nicht den
des Skripts. Ab jetzt: `python x.py > datei 2>&1; echo $?`.

TICKET 25 NEU (OFFEN, AFK): Selbstbezug - stirbt bfb63346d942 selbst, laeuft
auch sein Audit nicht. Zu klaeren, ob ein zweiter unabhaengiger
--no-agent-Job wirklich unabhaengige Ausfallmodi abdeckt (messen, nicht
argumentieren) oder ob der Agenten-Tick bewusst der aeussere Ring bleibt.
Entlastend: die Stagnations-Erkennung ist rot-faehig (Mutant M5).

MERKREGELN (neu):
- Ein stehendes Tor ist erst dann stehend, wenn es OHNE Agenten laeuft. Ein
  Pruefskript, das nur ein Tick aufruft, erbt dessen Ausfallwahrscheinlichkeit.
  Frage bei jedem Tor: wer ruft es auf, wenn niemand hinsieht?
- Nebenmessungen duerfen das Hauptsignal nicht verschlucken. Beim Einhaengen
  einer neuen Pruefung in einen bestehenden Entscheidungsbaum pruefen, welche
  Ausgabe dadurch unerreichbar wird.
- rc niemals hinter einer Pipe messen ($? = rc des letzten Pipe-Glieds).

Naechster Tick: Pflichtteil (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live). AB 2026-08-07 faellt die Zeitsperre
von TICKET 5 (Bing-Trefferzahl) - heute war 2026-08-06, also weiterhin
gesperrt. Ticket 3 = USER-KYC, Ticket 8 = 2 USER-Blocker, Ticket 10 = HITL,
Ticket 21 = HITL, Ticket 23 = HITL, Ticket 25 = AFK (offen).
Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus NICHT erwuenscht.

STAND 2026-08-08 (Tick, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK (52 Seiten).
verify_ticket13_live LIVE_OK (57 Seiten). dl_noindex_audit --live DL_NOINDEX_OK
(24/24). verify_rtd_chain KETTE_OK (399/799/1499 cent, Hash-Paritaet real
gemessen). rtd/thanks/index/agb/datenschutz/impressum/sitemap HTTP 200.

Der Tick startete mit UNCOMMITTETER Arbeit des Vorticks (cron_health_audit.py
+378 Z., cron_auto_fulfill.py +122 Z., _mutation_probe_t25.py untracked). Nach
Merkregel NEU AUSGEFUEHRT statt uebernommen - sie hat gehalten.

TICKET 25 ERLEDIGT + GESCHLOSSEN.
>>> DER BEFUND WAR NICHT DER SELBSTBEZUG, SONDERN EIN LATCH <<<
Das Audit beurteilte den Geldpfad-Traeger am Job-Exit 'completed' - an genau
der Groesse, die es durch sein eigenes rc SELBST bestimmt. Ein rotes rc macht
den naechsten Lauf failed, das Alter des letzten Erfolgs waechst, das Audit
bleibt rot. AM ALT-STAND AUSGEFUEHRT (echte jobs.json + executions.db):
rc=1 "letzter Erfolg vor 1031 min" gegen eine KERNGESUNDE Pipeline; neue
Fassung mit denselben Daten rc=0; bei wirklich stummer Pipeline weiter rc=1.
Kriterien jetzt: [A] letzter Lauf-VERSUCH + [B] Pipeline-Heartbeat (Etappe
[2b] in cron_auto_fulfill, geschrieben VOR dem Urteil, nur bei sauberer
Pipeline). 'completed' wird nur noch als [INFO - kein Kriterium] gedruckt.
AUSFALLMODI GEMESSEN (executions.db, nicht argumentiert):
  A job-lokal: 151 Fehl-Laeufe des Traegers, im selben Fenster 470 completed
    ANDERER Jobs -> propagiert nicht -> zweiter Ring hilft.
  B stille Abwesenheit: letzte DB-Zeile eines toten Jobs ist 'completed' -
    Tod hinterlaesst eine GRUENE Zeile -> nur ein Dritter sieht das.
  C Scheduler/Rechner tot: 06:42:32-13:31:10 = 409 min, 0 Laeufe IRGENDEINES
    Jobs -> gemeinsam, NICHT abgedeckt, ehrlich benannt (braeuchte einen
    Waechter ausserhalb dieses Rechners; nicht Gegenstand von T25).
ENTSCHEIDUNG: zweiter Ring JA. Neu 5e99ad47470f, kind=interval 30 min,
no_agent, deliver=local, Loader $HERMES_HOME/scripts/rtd_health_watchdog.py
-> Repo-Skript (keine zweite Kopie). Direkt in cron/jobs.json geschrieben
(Backup jobs.json.bak_t25_20260808_133913) - die CLI verstuemmelt deutsche
Prompts und erzeugt kind=once.
MEASURED: cron_health_audit --selftest 37/37 | cron_auto_fulfill --selftest
27/27 (inkl. "PRODUKTIV-Heartbeat unangetastet") | _mutation_probe_t25.py
MUTATION_PROBE_OK 21/21 (11 rote Mutanten in 2 Produktivdateien, exakte
Diagnosezeile, kein Traceback, beide sha256-genau restauriert, rc 0->1->0) |
echter Job-Lauf `hermes cron run 5e99ad47470f` -> "Ran now: succeeded",
DB completed, Ausgabedatei mit "Waechter (2. Ring, Ticket 25): 1" (die Ringe
sehen einander) und korrekt WAECHTER_UNGEPRUEFT bei exit 0 (kein Falsch-Rot) |
danach cron_auto_fulfill live RTD_FULFILL_OK mit [3] CRON_HEALTH_OK | echter
Traegerlauf `hermes cron run bfb63346d942` -> completed 13:41:58 mit
RTD_FULFILL_OK in der Ausgabedatei.
>>> NEBENBEFUND MIT BISS (Fremdbefund aus executions.db) <<<
Der Probe-Ring des Vorticks (34410d148c1f) war als kind=once angelegt, feuerte
0 mal und riss den Traeger ZWEIMAL mit ins Rot: 05:41 CRON_HEALTH_DEFEKT
("0 Laeufe protokolliert") -> RTD_FULFILL_DEFEKT, 06:11 "Intervall nicht
ableitbar (once)" -> RTD_FULFILL_UNGEPRUEFT. Ein Waechter, der nie lief, ist
fuer das Audit ununterscheidbar von einem toten -> der neue Ring wurde sofort
nach dem Anlegen einmal gefeuert.

TICKET 27 NEU (OFFEN, Frontier): DEFEKT (rc=1) und UNGEPRUEFT (rc=2) landen im
einzigen Signalkanal beide als status='failed' (heute beide Faelle real, 05:41
und 06:11). Die Konvention "unmessbar ist kein Defekt-Claim" (T16/17/18/19)
endet am Prozessrand. Der Waechter-Loader loest denselben Fall bereits
ENTGEGENGESETZT (rc=2 -> exit 0) - mindestens eines der Bauteile irrt.
Zielkonflikt: exit 0 laesst einen dauerhaft unmessbaren Geldpfad gruen
aussehen; exit !=0 erzeugt Falsch-Rot bei jeder Nachtabschaltung (die Klasse,
an der Ticket 22 starb). tickets/27-signalkanal-defekt-vs-unmessbar.md

MERKREGELN (neu):
- LATCH: ein Pruefer darf nie an einer Groesse urteilen, die er selbst setzt.
  Testfrage: "veraendert mein eigenes Ergebnis den naechsten Messwert?" - wenn
  ja, ist Gruen unerreichbar geworden, sobald es einmal rot war.
- Kriterien, die einander die Luecke decken, sind NICHT redundant: [A]
  (Lauf-Versuch) haette heute gelogen, weil zwei Jobs >10 min in 'claimed' mit
  started_at=None standen (Pool vom Agenten-Job belegt) - nur [B] wird da alt.
- Einen frisch angelegten Cron-Job SOFORT einmal feuern. "Existiert, hat aber
  nie gefeuert" ist fuer jedes Audit dasselbe Zeichen wie "tot".
- Cron-Jobs mit deutschem Prompt direkt in jobs.json schreiben (Backup!) - die
  CLI erzeugt aus "in 30m" ein kind=once statt eines Intervalls.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live + dl_noindex_audit --live). Dann
TICKET 27 abarbeiten (einziges unblockiertes AFK-Ticket mit Informationswert).
Ticket 3 = USER-KYC, Ticket 8 = 2 USER-Blocker, Ticket 10/21/23 = HITL,
Ticket 26 = zeitgesperrt bis 2026-08-18.
Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus NICHT erwuenscht.

STAND 2026-08-10 (Tick, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK. verify_ticket13_live
LIVE_OK (61 Seiten). dl_noindex_audit --live DL_NOINDEX_OK (24/24).
verify_rtd_chain KETTE_OK (Hash-Paritaet real in node ausgefuehrt).
rtd/thanks/index/agb/datenschutz/impressum/sitemap HTTP 200.

TICKET 27 ERLEDIGT + GESCHLOSSEN, TICKET 28 NEU.
Der Tick startete wieder mit UNCOMMITTETER Vortick-Arbeit (cron_auto_fulfill
+59 Z., cron_health_audit +236 Z., 2 untrackte Sonden). Nach Merkregel NEU
AUSGEFUEHRT statt uebernommen — und diesmal hat sie NICHT gehalten:
>>> DIE ERBSCHAFT WAR EIN FALSCH-GRUEN-GENERATOR <<<
cron_health_audit --selftest war ROT (50/57). Der Vortick hatte eine WACH-UHR
(wach_minuten(): nur belegbare Scheduler-Wachzeit statt Wanduhr-Alter gegen die
Toleranz) eingebaut, um Falsch-Rot nach Nachtabschaltung zu beseitigen. Vier
der sieben roten Faelle waren FALSCH-GRUEN AUF DEM GELDPFAD:
  - Heartbeat 1031 min alt, Job feuert alle 30 min      -> rc=0 (Lieferung tot)
  - nur der Geldpfad schweigt 900 min, anderer laeuft   -> rc=0
  - wirklich stummer zweiter Traeger                    -> maskiert
  - Geisterzeilen fremder job_ids als Wach-Alibi        -> rc=0
Zwei Ursachen: Entwurf (Wach-Summe aus FREMDEN Laeufen, bei duenner Beleglage
klein -> "wenig Wachzeit" fiel in den GRUEN-Zweig statt in "unmessbar") und
Verdrahtung (main() reichte bekannte_ids NIE an check_traeger durch -> die
Geisterzeilen-Sperre lief produktiv gar nicht mit; Funktion da, Aufrufer setzt
sie nicht — dieselbe Klasse wie der nie aufgerufene Signal-Decoder).
Wach-Uhr chirurgisch VERWORFEN, Nebenring-Trennung (gruen) BEHALTEN.
ENTSCHEIDUNGEN Ticket 27: (Haupt) exit != 0 bei UNGEPRUEFT BLEIBT — teuer war
nicht der Exitcode, sondern die Unlesbarkeit; der Decoder loest das. LIVE
gemessen an 214 Traegerlaeufen: 136x RUNNER-ABBRUCH Spend-Guard (Skript lief
NIE), 7x DEFEKT (exit 1), 2x Modell fehlt, 2x Scheduler-Neustart, 1x DNS/Netz,
1x unmessbar (exit 2), 1x laeuft/haengt -> von 150 nicht-completed sind nur
7 echte Defekte. (Neben B) Nebenring bekommt eigenen Signalwert rc=4
(CRON_HEALTH_NEBENRING_DEFEKT / RTD_FULFILL_NEBENRING_DEFEKT), getrennt nach
BETROFFENEM statt Schweregrad; Rangfolge Geldpfad > Nebenring > unmessbar > OK,
SALE-Banner steht davor.
MEASURED: health --selftest 57/57 | fulfill --selftest 38/38 |
_mutation_probe_t27c.py MUTATION_PROBE_OK 36/36 (rote Mutanten in 2 Produktiv-
dateien, exakte Diagnosezeile, kein Absturz, sha256-genau restauriert
97f8922fa7f1 / 5e24130fcfd4, rc 0->1->0) | LIVE cron_auto_fulfill
RTD_FULFILL_OK mit [3] CRON_HEALTH_OK.
NEBENBEFUND (echt, nicht synthetisch): der erste Live-Lauf des Audits meldete
CRON_HEALTH_DEFEKT — Stillstand 784 min (Rechner nachts aus), Heartbeat aber
793 min alt; die T25-Regel verlangt Deckung auf die Minute, 8 min Differenz
genuegten fuer den Defekt-Claim gegen eine kerngesunde Lieferung. Gegenprobe:
Traeger einmal echt laufen lassen -> [2b] frischer Heartbeat -> CRON_HEALTH_OK.
Also TRANSIENT und SELBSTHEILEND, KEIN Latch. -> TICKET 28
(tickets/28-falschrot-nach-abschaltung.md), inkl. Kandidat "verpasste
Gelegenheiten statt Zeit zaehlen" und dem Fallstrick DB-Zeile claimed mit
started_at=NULL (Lauf, der nie startete, kann nichts melden).

MERKREGELN (neu):
- Eine Erbschaft ist erst geprueft, wenn ihr eigener Selftest LAEUFT. Zweimal
  hat die Merkregel gehalten ("hat gehalten"), diesmal nicht — genau dafuer
  existiert sie. Nie den gruenen Ausgang des Vorticks glauben.
- Wer Falsch-Rot bekaempft, baut leicht Falsch-Gruen. Jeden Entlastungs-Zweig
  ("das erklaert das Schweigen") daraufhin pruefen, ob er in GRUEN oder in
  UNMESSBAR muendet. Entlastung ist kein Messwert.
- Neuer Parameter mit Default = stiller Ausfall: nach jedem `def f(..., x=None)`
  pruefen, ob der PRODUKTIVE Aufrufer x wirklich setzt.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live + dl_noindex_audit --live). Dann
TICKET 28 abarbeiten (einziges unblockiertes AFK-Ticket mit Informationswert;
Messlatte: alle 57 Selftest-Faelle bleiben gruen, die 4 Falsch-Gruen-Lagen als
benannte Faelle aufnehmen). Ticket 3 = USER-KYC, Ticket 8 = 2 USER-Blocker,
Ticket 10/21/23 = HITL, Ticket 26 = zeitgesperrt bis 2026-08-18.
Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus NICHT erwuenscht.

STAND 2026-08-10 (Tick 2, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK. verify_ticket13_live
LIVE_OK (61 Seiten). dl_noindex_audit --live DL_NOINDEX_OK (24/24).
verify_rtd_chain KETTE_OK. verify.py VERIFY_OK (78 ok, 0 fail).
rtd/thanks/index/agb/datenschutz/impressum/sitemap HTTP 200.

TICKET 28 ERLEDIGT + GESCHLOSSEN. Der Tick startete wieder mit UNCOMMITTETER
Vortick-Arbeit (cron_health_audit +204 Z., _mutation_probe_t28.py untracked).
Nach Merkregel NEU AUSGEFUEHRT statt uebernommen - diesmal hat sie GEHALTEN
(anders als beim Vortick, wo sie ein Falsch-Gruen-Generator war).
ANTWORT: nicht die ZEIT zaehlen, sondern die VERPASSTEN GELEGENHEITEN - und das
Ergebnis heisst nicht GRUEN, sondern UNMESSBAR. Kriterium [B]: >=1 eigener Lauf
seit dem Heartbeat WIRKLICH GESTARTET (started_at gesetzt) ohne zu melden ->
DEFEKT; 0 gestartete Laeufe -> kein Defekt-Claim, aber auch kein Gruen, sondern
CRON_HEALTH_UNGEPRUEFT (rc=2) mit benannter Begruendung. Genau dort ist die
Wach-Uhr gestorben: sie liess entlastetes Schweigen in GRUEN muenden.
Dazu kein Dauerfreibrief (>1440 min stumm = DEFEKT) + 60 s Karenz gegen Jitter.
Der Fallstrick war real: letzte DB-Zeile 'claimed' mit started_at=NULL - ein Lauf,
der NIE startete und per Konstruktion nichts melden konnte.
MEASURED: Alt-Stand (HEAD) gegen die konservierte Lage 784/793/9 min -> rc=1
CRON_HEALTH_DEFEKT (Falsch-Rot AUSGEFUEHRT, nicht behauptet); neue Fassung
dieselbe Lage -> rc=2 mit Begruendung | Selftest 67/67 | _mutation_probe_t28.py
MUTATION_PROBE_OK 22/22 (6 rote Mutanten, sha256-genau restauriert
13ab250e05eff98f, rc 0->1->0) | echte Laeufe CRON_HEALTH_OK + RTD_FULFILL_OK
(mit [2b] frischem Heartbeat) | Regression VERIFY_OK 78 ok, KETTE_OK,
cron_auto_fulfill --selftest 38/38.

>>> ZWEI EIGENE GEGENPRUEFUNGEN, die der Vortick NICHT geliefert hatte <<<
1. STILLE SCHRUMPFUNG (Ticket-18-Klasse): "67/67" allein beweist nichts - 57->67
   koennte alte Faelle GELOESCHT haben. Labels beider Fassungen verglichen:
   alle 57 HEAD-Faelle namentlich vorhanden, +10 neu, 0 verschwunden.
2. ATTRAPPEN-FALLE (Ticket-19-Klasse): der Selftest baut seine eigene SQLite.
   Gegen die ECHTE executions.db gemessen: Spalten job_id/status/claimed_at/
   started_at/finished_at/error existieren, 1001 Zeilen, 2 ohne started_at ->
   die Attrappe bildet das reale Schema ab, der Produktiv-SQL passt.

>>> TICKET-PRAEMISSE FALSIFIZIERT <<<
Ticket 28 sagte, der 2. Ring (rtd_health_watchdog.py) loese denselben Fall
ENTGEGENGESETZT (rc=2 -> exit 0). Stimmt seit Ticket 27 nicht mehr; der Text war
aus der T27-Beschreibung uebernommen statt gemessen. MEASURED an einer KOPIE
(Produktion unangetastet) mit Audit-Attrappe rc=2:
  "ERGEBNIS: WAECHTER_UNGEPRUEFT (Audit rc=2, kein Defekt-Claim)" exit 3
Beide Ringe teilen die Konvention also laengst. Echter Waechterlauf: WAECHTER_OK.

EHRLICHE GRENZE (nicht wegdiskutiert): bei dauerhaft stummem Scheduler bleibt
UNGEPRUEFT das richtige Wort - Gruen ist dort NICHT das Ziel. Ausfallmodus C aus
Ticket 25 (Rechner/Scheduler tot) braucht einen Waechter AUSSERHALB dieses
Rechners und ist weiter offen. Der Exitcode bleibt !=0, der Job sieht in
executions.db weiter 'failed' aus - lesbar gemacht hat das der T27-Decoder,
beseitigt ist es nicht.

MERKREGELN (neu):
- Eine gewachsene Testzahl ist kein Deckungsbeweis. 57 -> 67 kann 10 neue Faelle
  heissen oder 20 neue und 10 geloeschte. Fall-LABELS beider Fassungen
  vergleichen, nie die Summen.
- Zwei Merkregeln pruefen dasselbe Objekt von verschiedenen Seiten: die Attrappe
  muss das reale SCHEMA abbilden (nicht nur den Vertrag) - gegen die echte
  Datenquelle gegenmessen, nicht gegen die Vorstellung davon.
- Eine Ticket-Beschreibung ist ein ASSUMED-Claim, auch wenn sie aus dem
  Vorgaenger-Ticket stammt. Vor dem Beantworten den "Nicht vergessen"-Abschnitt
  am IST-Stand nachmessen - hier war er seit einem Ticket ueberholt.
- Zahlen in Kommentaren datieren. "hat 219 Zeilen" liest sich als Dauerzustand,
  die DB waechst aber (heute 222) - datierte Momentaufnahme schreiben.
- Fremde Ringe/Skripte NIE in der Produktion mutieren, um einen Zweig zu messen:
  Kopie anlegen, Kopie zeigen lassen auf eine Attrappe.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live + dl_noindex_audit --live).
KEIN unblockiertes AFK-Ticket mit Informationswert mehr offen: Ticket 3 =
USER-KYC, Ticket 8 = 2 USER-Blocker, Ticket 10/21/23 = HITL, Ticket 26 =
zeitgesperrt bis 2026-08-18. Also: "warte, beobachte Sales".
Aktionismus ausdruecklich NICHT erwuenscht.

STAND 2026-08-11 (Tick, MEASURED): auto_fulfill sessions=2 (roh) paid=0 neu=0.
funnel_check BESUCHER=0 / API-PROBE=0 / EIGENTEST=2, vollzaehlig=ja -> weiterhin
KEIN echter Traffic. legal_link_audit LEGAL_LINKS_OK (1260 Seiten, 0 unvollst.).
verify_ticket13_live LIVE_OK (1265 Seiten vollzaehlig). dl_noindex_audit --live
DL_NOINDEX_OK (24/24). verify_rtd_chain KETTE_OK (399/799/1499 cent, Feld
'anfrage', Redirect ok, Hash-Paritaet real in node ausgefuehrt).
cron_health_audit CRON_HEALTH_OK. verify.py VERIFY_OK (80 ok, 0 fail).
rtd/thanks/index/agb/datenschutz/impressum/sitemap HTTP 200.

>>> TICKET 23 GESCHLOSSEN — PRAEMISSE FALSIFIZIERT, KEIN HITL <<<
Das Ticket hiess "WhatsApp-Bridge tot" und war deshalb als HITL gefuehrt
(Fix angeblich nur per Gateway-Neustart aus frischer Shell). BEIDES FALSCH:
- Im selben gateway-stdio.log mit 98 jidDecode-Fehlern stehen 9 ERFOLGREICHE
  Zustellungen (Job 3e7e333151b0 -> whatsapp:...@lid), die letzten unmittelbar
  vor dem Tick. Eine tote Bridge stellt nicht 8x hintereinander zu.
- Echte Ursache, vollzaehlig ueber ALLE 15 Jobs klassifiziert: 4 Jobs haben
  deliver='origin' aber origin=None -> der Scheduler faellt auf den "home
  channel" zurueck und sendet woertlich an whatsapp:self -> jidDecode('self')
  ist undefined -> Bridge antwortet korrekt HTTP 500.
  Betroffen: bfb63346d942 (GELDPFAD, traegt "ERSTER SALE"), 87a15fe059fc
  (RTD-Builder = diese Tick-Berichte), 8c7afca842ac, a564ec4d11ea.
  => Der lauteste Kanal des Systems war stumm. Der erste Sale waere nur in
  sales.log sichtbar gewesen.
NEU scripts/request_delivery/fix_cron_delivery_origin.py: uebertraegt den
origin-Block eines NACHWEISLICH zustellenden Jobs auf die kaputten. Default
--dry-run, Backup vor dem Schreiben, Gegenlesen danach (Job-Anzahl unveraendert,
Rest-Kaputt=0), Rollback bei Abweichung, Adresse zur Laufzeit aus jobs.json
(kein Credential im Code, Ausgabe gekuerzt).
MEASURED (derselbe Job, derselbe Kanal, vorher/nachher):
  21:56 / 22:27 / 22:58  ERROR bfb63346d942: WhatsApp bridge error (500) jidDecode
  --- Fix 23:58:28 FIX_OK, Backup jobs.json.bak-t23-20260810-235828 (27394 B) ---
  23:58:50               INFO  bfb63346d942: delivered to whatsapp:...@lid
Danach FIX_NICHTS_ZU_TUN / ZUSTELL_OK (15 Jobs vollzaehlig), VERIFY_OK 80 ok.

MERKREGELN (neu):
- Immer auch nach dem ERFOLGSFALL greppen. Fehlerzeilen zaehlen misst die
  Fehlerhaeufigkeit, nicht die Verfuegbarkeit. Ein einziger Erfolg im selben
  Zeitfenster macht aus "Komponente kaputt" ein "Aufrufer kaputt" — und aus
  einem HITL-Blocker einen AFK-Fix.
- Fehlermeldungen benennen den Empfaenger: "delivery to whatsapp:self failed"
  stand 5 Tage woertlich da; gelesen wurde nur der 500er dahinter.
- Ein selbst genulltes Feld ist kein Messwert: last_delivery_error=None setzt
  der Fix selbst, und ein Lauf OHNE Zustellversuch sieht identisch aus. Nur die
  positive Zeile "delivered to ..." zaehlt.
- Erfolg und Misserfolg landen in VERSCHIEDENEN Logs. `hermes cron run` laeuft
  im CLI-Prozess (schreibt agent.log), der Scheduler im Gateway
  (gateway-stdio.log bekam 0 neue Zeilen). Nach jedem Eingriff alle frisch
  geaenderten Logs einsammeln: find logs -mmin -15.

TICKET 30 NEU (OFFEN, AFK, unblockiert, HOHE Prioritaet) = naechster Tick:
tickets/30-zustellbarkeit-ungewacht.md. Ticket 23 hat einen ZUSTAND repariert,
nicht die EIGENSCHAFT — nichts hindert einen neu angelegten Job daran, wieder
mit origin=None zu entstehen. Der Defekt macht KEINEN Job 'failed' und ist damit
fuer alle bestehenden Tore unsichtbar (cron_health_audit prueft, ob der Geldpfad
LAEUFT, nicht ob sein Ergebnis ANKOMMT). Vorgehen im Ticket: _probe_t23_
inventory.py zu cron_delivery_audit.py ausbauen (Zielmenge abgeleitet, leere
Menge nicht gruen, DELIVERY_UNGEPRUEFT rc=2), --selftest mit Fault Injection +
exakter Diagnosezeile, Mutationsprobe, dann als Etappe in cron_auto_fulfill.py
einhaengen OHNE das SALE-Banner hinter eine Verzweigung zu schieben.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live + dl_noindex_audit --live), dann
TICKET 30. Ticket 3 = USER-KYC, Ticket 8 = 2 USER-Blocker, Ticket 10/21 = HITL,
Ticket 26 = zeitgesperrt bis 2026-08-18.
Solange BESUCHER=0: "warte, beobachte Sales". Aktionismus NICHT erwuenscht.

STAND 2026-08-11 (Tick 3, MEASURED): Der Prompt-Tail listete TICKET 30 weiterhin
als "naechster Tick" offen — es war aber bereits geschlossen (Commit e702c344,
"Ticket 30 geschlossen + publiziert": Cron-Meldeweg-Waechter DELIVERY_OK live
verifiziert). Dieser Tick hat den Abschluss NEU vermessen statt uebernommen
(Merkregel: Vortick-Arbeit ist ein ASSUMED-Claim, neu ausfuehren).

TICKET 30 VERIFIZIERT (nicht nur behauptet):
- cron_delivery_audit.py --selftest 46/46 SELFTEST_OK (rc=0).
- cron_delivery_audit.py REAL -> DELIVERY_OK: 7 enabled Jobs + Fallback alle
  aufloesbar zu whatsapp:<len=18 pre=8511> (Adressen redigiert, kein Credential
  im Log); .env via hermes_cli.env_loader geladen; cron.scheduler (produktiv)
  importiert; 15 Jobs gelesen.
- Etappe [4] in cron_auto_fulfill.py integriert + im ECHTEN Lauf gefeuert:
  cron_auto_fulfill REAL -> [4] DELIVERY_OK, CRON_HEALTH_OK, RTD_FULFILL_OK.
  Damit ist der Ticket-23-Defekt (deliver='origin' ohne origin -> whatsapp:self
  HTTP 500) als EIGENSCHAFT gewacht, nicht nur als Zustand repariert.
- Zwei der einst kaputten Jobs (5e99ad47470f = 2. Ring, bae39ea51a60 =
  AI-CEO "ERSTER SALE") liefern jetzt sauber an -> Fix haelt.

PFLICHTTEIL (vollzaehlig, alle rc=0):
auto_fulfill REAL: sessions=2 (roh, inkl. Eigentests) paid=0 neu=0 -> keine
neuen Sales. funnel_check REAL: BESUCHER=0 / API-PROBE=0 / EIGENTEST=2,
vollzaehlig=ja. legal_link_audit LEGAL_LINKS_OK (0 unvollstaendig).
verify_ticket13_live LIVE_OK (1266 Seiten vollzaehlig live geprueft).
dl_noindex_audit --live DL_NOINDEX_OK (24/24). cron_health_audit --selftest
67/67. verify.py VERIFY_OK (81 ok, 0 fail). funnel_check --selftest 13/13.
auto_fulfill --selftest OK. cron_auto_fulfill --selftest 38/38. Live-Check
(canonische Domain translucentv1.github.io/new-business/): rtd/thanks/index/
agb/datenschutz/impressum/sitemap/robots.txt ALLE HTTP 200.

Naechster Tick: Pflichtteil fahren (auto_fulfill + funnel_check + Live-Check +
legal_link_audit + verify_ticket13_live + dl_noindex_audit --live).
KEIN unblockiertes AFK-Ticket mit Informationswert mehr offen: Ticket 3 =
USER-KYC, Ticket 8 = 2 USER-Blocker, Ticket 10/21 = HITL, Ticket 26 =
zeitgesperrt bis 2026-08-18. Also: "warte, beobachte Sales".
Aktionismus ausdruecklich NICHT erwuenscht.
