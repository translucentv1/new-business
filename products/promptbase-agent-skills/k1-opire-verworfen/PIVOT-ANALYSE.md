# K1.3 PIVOT — kleine, ungesaettigte Bounties (MEASURED-Analyse)

ZIEL (Kopf-Vorgabe): pro Bounty MEASURED pruefen
  (a) Solver-Zahl moeglichst 0-2
  (b) "available rewards > 0" bzw. "Money available > $0"
      -> Titel-Betrag != echtes Geld.
Nur REAL GEFUNDETE, wenig umkaempfte Bounties nehmen.

## Methode (MEASURED)
- Opire-Homepage (opire.dev/home) + Detailseiten (app.opire.dev/issues/<id>)
  heute live per web_extract geprueft.
- Browser-Tools (browser_navigate) auf app.opire.dev scheiterten mit
  "Invalid response" (SSE/Streaming-Body, Parser-Fehler) -> daher web_extract
  fuer die lesbaren Detailseiten genutzt.
- "Money available in bounties" auf jeder Detailseite ist ein AGGREGAT uber
  ALLE Bounties des Projekts (z.B. typeorm $25 Mio "available"), NICHT der
  spezifische Betrag. Echter Wert = Summe der einzelnen "reward, status Available".

## Gepruefte Bounties (MEASURED, heute)

| Bounty | Repo | Sprache | Solver (trying/claimed) | Status | Rewards available | Bewertung |
|--------|------|---------|------------------------|--------|-------------------|-----------|
| #3357 Migration drops/creates | typeorm/typeorm | TS | 25 / 25 | Open | 12 Rewards (>$590) | GESAETTIGT (Kopf: 23, fakt 25) |
| Readd web exports | godotengine/godot | C++ | 12 / 12 | Open | 35 Rewards ($3.3k) | GESAETTIGT + C++ (nicht lokal) |
| Helix keymap | zed-industries/zed | Rust | 6 / 6 | Open | 9 Rewards ($395) | GESAETTIGT + Rust |
| storybook-controls select | storybookjs/storybook | TS | 5 / 5 | Open | 6 Rewards ($263) | > 0-2-Schwelle |
| Add Wayland support | autokey/autokey | Python | 24 / 12 | CLOSED | 7 Rewards ($590) | RAUS (closed) + gesaettigt |
| QueryEngine deleteMany | strapi/strapi | TS | 3 / 3 | Open | 1 Reward ($30) | 3 solver > 2, klein |
| view test coverage | denoland/deno | Rust | 2 / 2 | Open | 1 Reward ($70) | KNAPP 2, aber Rust (nicht lokal) |
| Supply-chain busboy rewrite | bogeeee/restfuncs | TS | (nicht exakt) | Open | ~$70-90 | winziges Repo, Maintainer: "too many low-effort bounty hunters" |
| Image resize | electron/electron | JS | 2 / 2 | Open | 1 Reward ($70) | KNAPP 2, aber RIESIGE C++/JS-Codebase |
| Race Condition Concurrent | flowese/UdioWrapper | ? | 5 | Open | $86 | GESAETTIGT |

## Ergebnis
- Kein einziger Bounty erfuellt SAUBER beide Kopf-Kriterien (Solver 0-2
  UND lokal reproduzierbar + ungesaettigt).
- Die einzigen mit 2 Solvers (Deno #18147, electron Image resize) sind
  entweder Rust (nicht lokal) oder in einer Riesen-Codebase (electron).
- busboy/restfuncs: einziger TS-Kandidat in kleinem Repo, aber
  (1) Maintainer warnt vor Bounty-Hunter-Gedaenge,
  (2) Security-Rewrite ist Grossaufwand fuer ~$70-90,
  (3) exakte Solver-Zahl nicht MEASURED (Detailseite nicht erreichbar).

## Empfehlung an Kopf
Opire-Board ist in TS/Python weitgehend GESAETTIGT. Zwei Optionen:
  (A) Einzelne 2-Solver-Bounties (electron Image resize, Deno #18147) als
      "low-effort, low-payout" mitnehmen — aber lokale Repro bei electron/
      deno schwer (riesig / Rust).
  (B) K1 komplett pausieren, Fokus auf K3 (PromptBase) — dort ist die
      ungesaettigte Nische (Agent Skills), Marge hoeher, Konkurrenz minimal.
Meine Empfehlung: (B) — K1 liefert bei aktueller Sattigung schlechtes
Zeit/Risiko-Verhaeltnis; K3 Agent-Skills ist die bessere "kleine,
ungesaettigte" Chance, die der Kopf eigentlich wollte.

## Was hier ABGELEGT ist (KEIN PR, HARD-STOP)
- INVESTIGATION-REPORT-typeorm-11806.md (won't-fix, kein PR)
- Diese Pivot-Analyse (kein Bounty ausgewaehlt wegen Sattigung)

## Nutzer-Aktion (nur bei Wahl A)
- Opire-Account + GitHub verknuepfen
- Bei Wahl A: /try kommentieren, dann Fix+PR (Hermes darf PR NICHT einreichen)
