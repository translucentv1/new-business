# SELF-IMPROVE-LOG

## 2026-07-22 (autonome Nachtschicht, 5h)
**Autonomie-Level:** L2 (stetige Selbstverbesserung im Loop) — ohne Nutzer-Prompt Fortschritt gemacht.

**Sale-kritische Fixes (MEASURED):**
- Faktenfehler Sparerpauschbetrag 801/1608 -> 1000/2000 EUR (§20 EStG, seit 2023) repo-weit
  gepurgt (Produkt + 56 SEO-Seiten). Live verifiziert.
- Deliverables von Muell-duenn (89-594 B) auf echte 12-Monats-Grids + Anleitungen angereichert
  (live 2664->5656 B). Refund-Risiko gesenkt.
- Funnel 8/8 live end-to-end verifiziert (LP->Stripe->redirect->deliverable, alle 200).
- Outbound-Kit fuer alle 8 Produkte generiert (Etsy/Reddit/FB/Notion, Preise aus spec).
  3 alte Drafts mit Preis-/Anzahl-Fehlern entfernt.

**Prozess-Lehren (fuer naechste Session):**
1. **Alt-Drafts sind eine Faktenfehler-Quelle.** Hartkodierte Preise/Zahlen in
   Marketing-Assets driften von spec.json weg. LEHRE: Marketing-Assets IMMER aus
   spec.json generieren (outbound_kit.py-Muster), nie handschreiben. Bei jeder
   Session `grep -rn "[0-9],99" docs/social` gegen spec-Preise pruefen.
2. **"HTTP 200" != "korrekter Inhalt".** Die 801-EUR-Seiten waren alle 200 UND falsch.
   LEHRE: nach Deploy nicht nur Status pruefen, sondern `curl | grep <erwarteter-Wert>`
   auf einen NEUEN korrekten String (Belegpflicht auf Inhalt, nicht nur Erreichbarkeit).
3. **Duenne Deliverables = stiller Sale-Killer.** Ein technisch korrekter Funnel
   liefert trotzdem 0 nachhaltige Sales, wenn das Produkt 89 Bytes ist. LEHRE: Produkt-QA
   muss GROESSE/Substanz messen, nicht nur "keine Platzhalter".

**Naechster Hebel (menschlicher 1-Schritt):** Etsy-Listings aus docs/social/outbound/ einstellen.

## 2026-07-22 (self_improve_pass.py, kostenlos)
**Sales:** 0 | **Landingpages:** 15
**Findings:** 2
- [HIGH] meta L2 Regel 4 (Erfolg = Sales): 0 echte Sales trotz 22 live Links + Funnel 8/8 sauber.
  - Ursache: Traffic-Fehler: Loop baut SEO/Produkte, aber KEINE echte Traffic-Aktion (Regel 1+2 verletzt: 'keine Session ohne Traffic-Aktion').
  - Fix: Naechste Session MUSS eine echte Distribution-Aktion ausfuehren, keine weitere SEO-Seite. Outbound-Kit (docs/social/outbound) liegt bereit.
- [HIGH] meta L2 Regel 2 (Traffic > SEO-Masse): 15 Landingpages live, aber 0 Sales -> SEO-Masse bringt keinen Sale.
  - Ursache: Verteilung (Traffic) ist der Flaschenhals, nicht mehr Seiten.
  - Fix: Arbeit stoppt SEO-Aufbau; verteilt stattdessen die existierenden 8 Produkte.
**Gepatchte Skills:** keine (nur Analyse, keine sicheren Patches).

## 2026-07-22 (self_improve_pass.py, kostenlos)
**Sales:** 0 | **Landingpages:** 15
**Findings:** 2
- [HIGH] meta L2 Regel 4 (Erfolg = Sales): 0 echte Sales trotz 22 live Links + Funnel 8/8 sauber.
  - Ursache: Traffic-Fehler: Loop baut SEO/Produkte, aber KEINE echte Traffic-Aktion (Regel 1+2 verletzt: 'keine Session ohne Traffic-Aktion').
  - Fix: Naechste Session MUSS eine echte Distribution-Aktion ausfuehren, keine weitere SEO-Seite. Outbound-Kit (docs/social/outbound) liegt bereit.
- [HIGH] meta L2 Regel 2 (Traffic > SEO-Masse): 15 Landingpages live, aber 0 Sales -> SEO-Masse bringt keinen Sale.
  - Ursache: Verteilung (Traffic) ist der Flaschenhals, nicht mehr Seiten.
  - Fix: Arbeit stoppt SEO-Aufbau; verteilt stattdessen die existierenden 8 Produkte.
**Gepatchte Skills:** keine (nur Analyse, keine sicheren Patches).

## 2026-07-22 (self_improve_pass.py, kostenlos)
**Sales:** 0 | **Landingpages:** 15
**Findings:** 2
- [HIGH] meta L2 Regel 4 (Erfolg = Sales): 0 echte Sales trotz 22 live Links + Funnel 8/8 sauber.
  - Ursache: Traffic-Fehler: Loop baut SEO/Produkte, aber KEINE echte Traffic-Aktion (Regel 1+2 verletzt: 'keine Session ohne Traffic-Aktion').
  - Fix: Naechste Session MUSS eine echte Distribution-Aktion ausfuehren, keine weitere SEO-Seite. Outbound-Kit (docs/social/outbound) liegt bereit.
- [HIGH] meta L2 Regel 2 (Traffic > SEO-Masse): 15 Landingpages live, aber 0 Sales -> SEO-Masse bringt keinen Sale.
  - Ursache: Verteilung (Traffic) ist der Flaschenhals, nicht mehr Seiten.
  - Fix: Arbeit stoppt SEO-Aufbau; verteilt stattdessen die existierenden 8 Produkte.
**Gepatchte Skills:** keine (nur Analyse, keine sicheren Patches).

## 2026-07-22 (self_improve_pass.py, kostenlos)
**Sales:** 0 | **Landingpages:** 15
**Findings:** 2
- [HIGH] meta L2 Regel 4 (Erfolg = Sales): 0 echte Sales trotz 22 live Links + Funnel 8/8 sauber.
  - Ursache: Traffic-Fehler: Loop baut SEO/Produkte, aber KEINE echte Traffic-Aktion (Regel 1+2 verletzt: 'keine Session ohne Traffic-Aktion').
  - Fix: Naechste Session MUSS eine echte Distribution-Aktion ausfuehren, keine weitere SEO-Seite. Outbound-Kit (docs/social/outbound) liegt bereit.
- [HIGH] meta L2 Regel 2 (Traffic > SEO-Masse): 15 Landingpages live, aber 0 Sales -> SEO-Masse bringt keinen Sale.
  - Ursache: Verteilung (Traffic) ist der Flaschenhals, nicht mehr Seiten.
  - Fix: Arbeit stoppt SEO-Aufbau; verteilt stattdessen die existierenden 8 Produkte.
**Gepatchte Skills:** keine (nur Analyse, keine sicheren Patches).
