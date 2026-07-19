# ADR-0021 — GRILL: Neue PD-Bücher (SEO / mehr Produkte) — BLOCKED

- **Status:** Entscheidung ausgesetzt (Initiale Grill-Bewertung, nicht autonom gebaut)
- **Datum:** 2026-07-19 (MEASURED heute Nacht, ~03:5x)
- **Autor:** Hermes (autonomer Cron-Durchgang, Charta + ADR-0013-Nachtrag)
- **Kontext:** Kanban leer (TB-8…TB-20 = done, 0 offene Tickets). Dauerschleife
  verlangt bei leerem Vorrat neue Initiative via GRILL→SPEC→TICKETS→IMPLEMENT.

## GRILL (schriftlich, selbst)
- **Frage:** Bringt das Hinzufügen weiterer PD-Bücher (mehr Landingpages =
  mehr Long-Tail-SEO-URLs) messbar den ersten Sale näher?
- **Sale-Bezug:** JA. Mehr indexierte Produktseiten = größere Entdeckungsfläche.
  TB-SEO (39 URLs) war bereits der einzige SEO-Hebel (kein Social erlaubt).
- **Beleg (MEASURED):**
  - Site lebt: `index` HTTP 200, `1342` HTTP 200 mit 61 "Kapitel"-TOC,
    keine Platzhalter (publish_site.py: "No changes to publish" → gh-pages aktuell).
  - Sale-Poll: `[OK] poll ok, 0 new sale(s)` — bisher 0 Sales (`sales.log` fehlt).
  - `OPENROUTER_API_KEY`: in dieser Umgebung **leer/unset** (MEASURED via
    `echo $OPENROUTER_API_KEY` → NO; keine Key-Datei im Repo).
- **Ehrliches Loch:** Aktuell 0 Sales ⇒ Traffic vermutlich ~0. Mehr Bücher
  helfen NUR bei SEO-Entdeckung, nicht bei Conversion. Zudem erzwingt das
  ADR-0018-Produktmodell pro Buch eine `study_guide.json` MIT Inhalt
  (kein Platzhalter) — sonst Regression von TB-20 ("keine Platzhalter mehr").
- **Hard Stop / Blocker:** `study_guide_gen.py::build_guide` erzeugt NUR Gerüst +
  PLATZHALTER (`"[ZUSAMMENFASSUNG Kapitel N — vom Agenten per LLM zu fuellen]"`).
  Das Befüllen (Zusammenfassungen/Diskussionsfragen) läuft über
  `companion_llm.py` und braucht `OPENROUTER_API_KEY`. Key fehlt ⇒ ein neues
  Buch würde ein Platzhalter-Produkt liefern = TB-20-Regression. Das Setzen/
  Entgegennehmen von Keys ist ein **Hard Stop** (Charta).

## Entscheidung
Initiative überlebt GRILL **NICHT** für autonome Ausführung in dieser Umgebung.
Status dieser Sitzung: **"warte, beobachte Sales"** (Leerlauf ok, Aktionismus nicht).

## Benötigt USER-Entscheidung (eine von drei)
1. `OPENROUTER_API_KEY` bereitstellen (dann LLM-Fill möglich), **oder**
2. Produktformat OHNE LLM-Study-Guide akzeptieren (nur regelbasierte
   Kapitelstruktur im Guide — explizit Platzhalter vermeiden), **oder**
3. Neue Bücher aufschieben, bis Voraussetzung (1) erfüllt ist.

## Nächster Schritt (sobald entschieden)
TB-21 als IMPLEMENT ausführen: `pd_scanner.fetch_text` → `pd_processor`
(clean/QA) → `deliverable_gen` → `stripe_uploader.create_link` →
`study_guide_gen` (+ ggf. LLM-Fill) → `landingpage_gen` → `publish_site` →
Live-Check 200 → `test_download_gate` + `test_pd_processor` grün → commit/push.
