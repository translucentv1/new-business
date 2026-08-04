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

Kurzer deutscher Statusbericht am Ende: was/Beleg/naechster Schritt.
