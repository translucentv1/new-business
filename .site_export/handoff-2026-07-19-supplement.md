# Handoff-Supplement — 2026-07-19 (Hermes Durchgang)

Ergänzt `handoff-2026-07-19.md`. Status: Diagnose + Strategie-Dokument fertig.
Strategie-Dokument: `docs/adr/0022-strategie-klaerung-kanal-ueber-traffic.md` (wartet auf USER-Entscheidung).

## (4.1) Stripe-Draft-Status — GEKLÄRT (MEASURED)
- "10/10 drafts (0 pub)" stammt aus `scripts/publish_all.py` = **Gumroad**-Vokabular
  (Backup-Rail, ADR-0010/0011). Die Live-Site verlinkt auf **Stripe**, nicht Gumroad.
- Stripe-Store ist LIVE + kaufbereit: Account `charges_enabled=True, payouts_enabled=True`
  (DE). 13/13 Links in `stripe_links.json` `active=True` + gültiges aktives Produkt (3,99 €).
  Beispiel-Link HTTP 200.
- `/v1/products`-Liste liefert 0, aber einzelne Links via `expand` zeigen echtes
  `prod_…` (active, 3,99 €) — Stripe-Listen-Quirk, KEINE Auswirkung auf Kaufbarkeit.
- **Fazit:** Store blockt nicht. Echter Engpass = Traffic (~0), bestätigt durch
  `poll ok, 0 new sale(s)`.

## (4.2) WA-Bridge "down (jidDecode)" — IRREFÜHREND (MEASURED)
- Bridge läuft: Port 3000 Listen, `/health` HTTP 200, `{"status":"connected"}`, uptime ~42h.
- `jidDecode` kommt **0x** in `bridge.log` vor. Die "down"-Meldung war ein veralteter
  Watchdog-Status. Reale, harmlose Warnung: fehlendes `link-preview-js` (nur Link-Preview
  fremder Gruppen) — betrifft NICHT Owner-Self-Chat/Bot.
- Kein Fix nötig; Status in `.process_feed.txt` korrigiert.

## (4.3) 2h-Report "cfg drift" — TEILWEISE BEHOBEN (MEASURED)
- Ursache: Hermes Spend-Schutz bei Inference-Config-Drift (provider openrouter→gemini,
  model tencent/hy3:free→gemini-2.5-pro zum Erstellzeitpunkt). Ungepinnte Jobs wurden
  übersprungen ("prevent unintended spend").
- 3 sichtbare `new-business`-Jobs (Nachtschicht, Stripe Boot, Stripe Poll) auf
  aktuellen Default `openrouter`/`tencent/hy3:free` gepinnt → kein Drift mehr.
- DIE 3 GATEWAY-WATCHDOGS (2h report = a89ac41273b2, 30min observer = fa55dfa332e5,
  15min feed = 0dffa096f072) sind NICHT über `cronjob`/`hermes cron` erreichbar —
  sie liegen im Gateway-internen Scheduler-Namespace, nicht in `cron/jobs.json`.
  `cronjob update` schlägt mit "not found" fehl.
- **Offener Punkt / USER-Entscheidung:** Diese 3 Watchdogs neu starten = `hermes gateway
  restart` (oder Gateway-interner Reschedule). ACHTUNG: Memory sagt `gateway restart`
  ist im Gateway-Prozess blockiert (SIGTERM eigenen Parent). Empfehlung: User führt
  `hermes gateway restart` in EINER frischen Shell aus (nicht aus dem Gateway heraus),
  oder lässt sie — sie sind reine Observability-Watchdogs, kein Business-Blocker.

## Warten auf USER
- Kein Bau neuer Produkte/Plattformen (Handoff §5). ADR-0022 liegt zur Entscheidung vor:
  Empfehlung = K1 (SEO passiv) + K2 (Marketplace mit Discovery) als Haupt-Pivot.
- Nächster Schritt nur nach USER-Wahl in ADR-0022 §6.
