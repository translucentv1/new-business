# Ticket 12 — Tier-Differenzierung im Fulfillment (Versprechen vs. Lieferung)

Typ: `wayfinder:task` (AFK)
Status: **CLOSED 2026-08-04** — Resolution am Ende dieser Datei
Claim: Cron-Tick 2026-08-04 20:15 (autonom)
Parent: `wayfinder_map.md`

## Question

Der Kaufpfad verkauft **drei Preisstufen** mit ausdrücklich unterschiedlichem
Leistungsumfang. Erreicht die gewählte Stufe überhaupt die Erzeugung des
Deliverables — oder bekommt ein Premium-Käufer (14,99 €) dasselbe wie ein
Basis-Käufer (3,99 €)?

Anlass: In allen bisherigen Ticks wurde der Geldpfad *technisch* gemessen
(Link → Zahlung → Generierung → Publish → Abruf). Was der Kunde inhaltlich
**für sein Geld** bekommt, war nie Gegenstand einer Messung. Der Publish-Beweis
aus Ticket 11 sagt „eine Datei kommt live an" — nicht „die richtige Datei".

## Befund (MEASURED 2026-08-04)

**1. Das Versprechen steht an drei Stellen, davon einer vertragsbindend:**

| Stelle | Basis 3,99 € | Standard 7,99 € | Premium 14,99 € |
|---|---|---|---|
| `rtd.html` Z. 47–49 | kurzes Deliverable | mittel, inkl. 1 Revision | ausführlich, 2 Revisionen |
| `gig.html` Z. 90–92 | bis ~300 Wörter / ~50 Zeilen Code, keine Revision | bis ~800 Wörter / ~150 Zeilen Code, 1 Revision | bis ~2000 Wörter / komplettes Template, 2 Revisionen |
| `agb.html` § 3 Z. 46 | — | 1 Revision | 2 Revisionen |

`agb.html` ist **live und verlinkt** — das ist Vertragsinhalt, nicht Marketing.

**2. Die Preisstufe erreicht die Erzeugung nachweislich nicht.**
`auto_fulfill.fulfill_session()` liest aus der Session ausschließlich das
Feld `anfrage` und ruft `gen_deliverable(req_text)` auf. `gen_deliverable`
(in `scripts/gig_fulfill.py`) hat die Signatur `(req_text)` — **kein**
Preis-, Tier- oder Umfangs-Parameter. `amount_total` wird zwar in
`fulfilled_live.json` und `sales.log` protokolliert, aber nie ausgewertet.
=> Basis, Standard und Premium durchlaufen **denselben** Prompt.

**3. Empirisch bestätigt (echter Ollama-Lauf, identische Anfrage):**
```
Lauf 1: err=None bytes=2257 woerter=290
Lauf 2: err=None bytes=2437 woerter=292
```
~290 Wörter — unabhängig davon, was bezahlt wurde. Das entspricht exakt der
**Basis**-Stufe. Ein Premium-Käufer zahlt das 3,76-fache für dasselbe Produkt.

**4. Revisionen existieren nirgends außer im Text.** Weder Code noch
Deliverable-Seite kennen den Begriff; der Käufer erfährt nie, dass ihm
1 bzw. 2 Revisionen zustehen, und hat keinen benannten Weg, sie einzufordern.

**Ehrliche Abgrenzung (nicht überziehen):** `gig.html` formuliert „**bis** ~2000
Wörter" — eine Obergrenze, keine Zusage. Eine kurze Lieferung ist damit nicht
automatisch vertragswidrig. Der Defekt ist ein anderer und härter: die
verkaufte **Differenzierung existiert im Code nicht**, und die Revisionszusage
der AGB hat keinen Mechanismus.

## Warum das jetzt zählt (und nicht erst nach dem ersten Sale)

Der erste Sale kann jede der drei Stufen sein. Trifft er Premium, liefert das
System heute stillschweigend das Basis-Produkt — Rückerstattung/Chargeback
ausgerechnet beim ersten zahlenden Kunden. Dieselbe Defektklasse wie die
IndexNow-Branch-Falle und die ungemessene Publish-Etappe: ein nie geprüfter
Claim auf dem Geldpfad, nur diesmal zwischen „Kunde hat bezahlt" und
„Kunde hat bekommen, wofür er bezahlt hat".

## Nicht anfassen

Die drei LIVE Payment Links (einzige Einnahmequelle) bleiben unverändert —
der Defekt liegt hinter der Zahlung, nicht davor.

---

## Resolution (2026-08-04, MEASURED)

**Behoben.** Die Preisstufe erreicht jetzt die Erzeugung.

1. `scripts/gig_fulfill.py`: `gen_deliverable(req_text, tier=None)` — neuer
   optionaler Parameter, Default-Verhalten unverändert (Altaufrufer wie
   `fulfill()` bleiben funktionsfähig). `TIER_SPEC` bildet Cent-Betrag →
   Umfang/Abschnitte/Revisionen ab. Premium wird **abschnittsweise** erzeugt
   (Gliederung → Abschnitte → Zusammenbau), weil ein Einzelprompt das
   Zielvolumen nachweislich nicht erreicht (683 Wörter bei Ziel 1800–2000,
   188 s — gemessen, bevor gebaut wurde).
2. `scripts/request_delivery/auto_fulfill.py`: `tier_for_amount()` leitet die
   Stufe aus `session.amount_total` ab und reicht sie durch. Unbekannter Betrag
   → **Basis** (nie mehr versprechen, als bezahlt wurde) und `tier_guess=True`
   im Protokoll.
3. Deliverable-Seite nennt jetzt Stufe, Umfang und Revisionsanspruch samt
   Abruf-Weg (E-Mail aus dem Impressum) — die AGB-Zusage wird dadurch erstmals
   einlösbar statt bloß behauptet.
4. `--selftest` mit Fault Injection (Konvention „Prüfer prüfen").

**Messung nach dem Bau** — `scripts/request_delivery/measure_tier_diff.py`,
echter Ollama-Lauf, **identische** Anfrage je Stufe:

```
Basis       399 cent  ziel~  300 -> woerter=  219 bytes=  1661 zeit=   31s err=None
Standard    799 cent  ziel~  800 -> woerter=  570 bytes=  4536 zeit=  167s err=None
Premium    1499 cent  ziel~ 2000 -> woerter= 1337 bytes= 10354 zeit=  422s err=None

Basis 219 < Standard 570 < Premium 1337 -> DIFFERENZIERT
Faktor Premium/Basis = 6.11x (vor dem Fix: 1.00x, identischer Prompt)
TIER_DIFF_OK
```

**Was damit belegt ist:** Die Stufe verändert die Lieferung. Vorher 1,00x
(bitweise derselbe Prompt), jetzt 6,11x.

**Was damit NICHT belegt ist (ehrlich):** Keine Stufe erreicht ihren
Nominalwert punktgenau (219/300, 570/800, 1337/2000). Das ist mit der
Formulierung „**bis** ~X Woerter" vereinbar — eine Obergrenze, keine Zusage —
aber es ist ausdruecklich **kein** Beleg dafuer, dass die Zielwerte erreicht
werden. Wer das behaupten will, muss die Zielwerte senken oder ein groesseres
Modell messen (`qwen2.5:7b` liegt lokal vor, wurde hier nicht gemessen).

**Laufzeit-Nebenbefund:** Ein Premium-Auftrag belegt den Tick ~422 s allein
fuer die Erzeugung (+ bis zu 180 s `wait_live`). Unkritisch gegen die
AGB-Frist von 24 h, aber ein Tick mit Premium-Sale dauert ~10 min.

**Selftest** (`auto_fulfill.py --selftest`, gruen):
```
TIER OK [399] -> Basis ziel~300 rev=0 geraten=False
TIER OK [799] -> Standard ziel~800 rev=1 geraten=False
TIER OK [1499] -> Premium ziel~2000 rev=2 geraten=False
TIER OK [1499] -> Premium ziel~2000 rev=2 geraten=False   (String-Betrag)
TIER OK [None] -> Basis ziel~300 rev=0 geraten=True
TIER OK [1234] -> Basis ziel~300 rev=0 geraten=True
TIER OK [revisionsweg] Premium nennt Kontakt, Basis nicht
FAULT INJECTION OK: 'alles ist Basis' wird erkannt, Restore ok
SEITE OK: Stufe+Umfang+Revisionen+Kontakt stehen drauf
```

**Regressionsschutz:** `verify_publish_leg.py --selftest` (Ticket 11) nach dem
Eingriff erneut **9/9** — `write_page()` hat neue Parameter, aber nur mit
Defaults; der Canary-Aufruf ist unveraendert gueltig. `verify_rtd_chain.py`
danach **KETTE_OK** (3 LIVE-Links unveraendert, 399/799/1499 cent) — der Fix
liegt vollstaendig hinter der Zahlung, die Einnahmequelle wurde nicht angefasst.

**Beim Bauen gefunden:** In `gig_fulfill.py` hiess der Leer-Fehlercode
`OLLAB_EMPTY` (Tippfehler) — nach `OLLAMA_EMPTY` korrigiert. Und mein eigenes
Messskript startete zunaechst mit `ModuleNotFoundError` (falsche ROOT-Berechnung)
— gefangen, weil die Ausgabe geprueft wurde und nicht nur der Exit-Code.

**Offen (nicht Teil dieses Tickets):** Die Revisionszusage ist jetzt auf der
Abrufseite sichtbar und per Mail einforderbar, aber es gibt keinen
automatisierten Revisionslauf — eine Revision waere Handarbeit. Solange
BESUCHER = 0, ist das kein Engpass; bei echten Sales gehoert es geticketet.

