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
inkl. Preise: Basis 399 / Standard 799 / Premium 1499 EUR (alle livemode/active,
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
-> KETTE_OK (3 LIVE-Links active, 399/799/1499 EUR, Feld 'anfrage', Redirect auf
translucentv1.github.io/.../thanks.html, Hash-Paritaet OK, dl/rtd-Ziel vorhanden).
Kanonische Live-Domain = translucentv1.github.io (philippgro.github.io = 404, nur
Repo-Owner-Domain live). rtd.html/thanks.html HTTP 200 (rtd.html 5309 B). Feature
vollstaendig + MEASURED live. 0 Sales = Traffic/Conversion-Luecke, KEIN Defekt.
Offen (USER-Blocker): EMAIL_* (Mail-Versand), Impressum/AGB-Platzhalter [DEIN NAME];
Fiverr-Gig = USER-KYC. Naechster autonomer Schritt: keiner sinnvoll ueberlebensfaehig
-> "warte, beobachte Sales" (Idle OK, Aktionismus nicht).

Belegpflicht: MEASURED (HTTP-Test, Dateiinhalt, keine erfundenen Keys).
Stopp wenn Live-Stripe-Key fehlt und nur DEMO moeglich ist.

Kurzer deutscher Statusbericht am Ende: was/Beleg/naechster Schritt.
