# Ticket 10 — Sollen Seitenaufrufe auf rtd.html gemessen werden?

Typ: `wayfinder:grilling` (**HITL** — nur mit dem Nutzer entscheidbar)
Status: **OPEN** — auf Frontier, aber **HITL**: ein Cron-Tick darf das NICHT
selbst beantworten.
Verwandt: [Ticket 9 — Besucher-Messung](9-besucher-messung.md) (CLOSED)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

Ticket 9 hat die Funnel-Stufe **„Kaufseite geoeffnet"** messbar gemacht (gratis,
ohne Account, ohne Cookies). Eine Stufe davor bleibt blind: **Seitenaufrufe auf
`rtd.html`**.

Lohnt es sich, diese Stufe ebenfalls zu messen?

Der Nutzen ist praezise benennbar: nur damit laesst sich
„**niemand sieht die Seite**" (= Traffic-Problem) von
„**Leute sehen sie, klicken aber nicht auf Kaufen**" (= Angebots-/Preis-/
Copy-Problem) unterscheiden. Solange BESUCHER = 0 ist, sind beide Diagnosen
gleich gut vereinbar mit den Daten — und sie fuehren zu **entgegengesetzten**
naechsten Schritten.

## Warum das nicht AFK entschieden werden kann

Jede bekannte Option kostet etwas, das nur der Nutzer vergeben kann:

1. **Third-Party-Analytics** (GoatCounter, Plausible, Cloudflare Web Analytics):
   braucht einen **Account auf den Namen des Nutzers** und macht die eben erst
   gebaute `datenschutz.html` unvollstaendig (neue Fremdressource auf dem
   Kaufpfad → Art. 13 DSGVO nachziehen, ggf. Auftragsverarbeitung).
2. **Eigener Zaehl-Endpoint** (Worker/Serverless): braucht ebenfalls Account,
   und GitHub Pages ist statisch — es gibt keine Server-Logs, die man auslesen
   koennte (MEASURED: Pages liefert kein Log-Interface).
3. **Gar nicht messen**: legitim. Bei einem 3,99-€-Produkt kann Analytics mehr
   Rechts- und Wartungsaufwand erzeugen als der Erkenntnisgewinn wert ist —
   der Stripe-Funnel-Zaehler aus Ticket 9 reicht evtl. als Signal.

Das ist eine Abwaegung zwischen DSGVO-Aufwand, Account-Besitz und
Erkenntniswert — eine **Nutzer**-Entscheidung, keine Agent-Entscheidung.

## Wann diese Frage ueberhaupt Informationswert hat

Erst wenn ueberhaupt jemand kommen koennte, also wenn
[Ticket 5](5-bing-indexierung-verifizieren.md) (ab 2026-08-07) Indexierung
zeigt **oder** Ticket 3 (Fiverr) live ist. Vorher ist die Antwort mit hoher
Wahrscheinlichkeit „nicht messen" — man wuerde eine Null instrumentieren.

## Anti-Aktionismus-Regel

Kein Tick baut hier eigenmaechtig Analytics ein. Kein Tick setzt einen
Third-Party-Zaehler auf den Kaufpfad, ohne dass diese Frage entschieden ist.
