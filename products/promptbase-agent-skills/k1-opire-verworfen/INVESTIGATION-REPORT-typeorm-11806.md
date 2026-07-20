# Investigation Report — typeorm/typeorm #11806 (KEIN PR, won't-fix)

Status: Investigation abgeschlossen. EMPFEHLUNG: KEINEN PR einreichen.
Begründung unten (Maintainer-Intent + expliziter Test am HEAD).

## Bounty-Metadaten (MEASURED)
- Quelle: https://app.opire.dev/issues/01HWT2MKE4GWPJXDPMAFEAHHHE
- Betrag laut Opire-Titel: 30 $
- Status: Open; 0 paid rewards; 2 Teilnehmer; keine konkurrierende PR
- Repo: https://github.com/typeorm/typeorm (lokal geklont)
- Sprache: TypeScript

## Behauptung im Issue
"createQueryBuilder ignores invalidWhereValuesBehavior.undefined: 'ignore'"
Erwartung: wenn `invalidWhereValuesBehavior = { undefined: 'ignore' }` gesetzt ist,
soll `.where({ text: undefined })` die Bedingung ignorieren (0 Treffer statt 3).

## Reproduktion (MEASURED, heute voriger Turn)
Umgebung: node v24.18.0, npm 11.16.0, git 2.55.0.
- Repo geklont, `npm install`, `npm run build` (tsc -> build/compiled/src/index.js OK)
- ormconfig auf sqljs (WASM) — better-sqlite3 braucht natives VS-Build (nicht vorh.)
- Test angelegt: test/github-issues/11806/issue-11806.test.ts
- Lauf MIT unveraendertem Code:
    FAIL  github-issues/11806  (1 failing)
    expected +0 to equal 3   <- Bug reproduziert
- Control-Test (setFindOptions mit gleicher Option) lief GREEN.

=> Der Bug ist REAL und reproduzierbar: QueryBuilder.where() respektiert
   invalidWhereValuesBehavior.undefined='ignore' NICHT (liefert 0 statt 3 Zeilen).

## Ursachen-Analyse (MEASURED)
- Fix in src/query-builder/QueryBuilder.ts getWhereCondition() implementiert:
  undefined-Werte respektieren invalidWhereValuesBehavior.
- Nach Fix: der Test lief GREEN.
- ABER am HEAD existiert ein expliziter, Absicht bekundender Test:
  test/functional/null-undefined-handling/query-builders.test.ts
  -> "invalidWhereValuesBehavior does NOT affect QB .where()"
  -> Begruendung im Test: "QB is low-level" (QueryBuilder ist bewusst low-level)
- Maintainer-Kommentar in #11806 / verwandt #11818: invalidWhereValuesBehavior
  soll NUR FindOptions / setFindOptions betreffen, NICHT QueryBuilder.where().

## Entscheidung
Der Bug ist "by design / won't-fix". Ein Fix-PR wuerde vom Maintainer-Team
abgelehnt werden (es gibt einen Test, der das aktuelle Verhalten als korrekt
festhaelt, plus dokumentierte Intent).

Merge-Wahrscheinlichkeit eines Fix-PRs: ~0 %.
Konkurrenz: gering (2 Teilnehmer) — aber sinnlos wegen won't-fix.

## Aktion
- Quellcode-Aenderung komplett rueckgaengig gemacht (git diff src/ == leer, verifiziert).
- KEIN PR-Entwurf angelegt (laut Kopf-Entscheidung: nur Investigation-Report).
- Repro-Test belassen unter test/github-issues/11806/ (als Beleg der Reproduktion,
  aber nicht als PR-Grundlage).

## Dateien / Belege auf Disk
- Repro-Test: k1-opire/typeorm/test/github-issues/11806/issue-11806.test.ts
- Kompiliert:  k1-opire/typeorm/build/compiled/test/github-issues/11806/issue-11806.test.js
- repro-11806.mjs (Hilfs-Skript)
- git diff src/ == leer (Fix rueckgaengig)

## Nutzer-Aktion (optional)
Wenn du das Verhalten trotzdem als Feature willst: Issue kommentieren /
Discussion eroeffnen statt PR. Aber aus Bounty-Sicht: 30$ bei ~0% Merge
lohnen die Zeit nicht. Empfehlung: Bounty fallen lassen, auf Pivot (K1.3) gehen.
