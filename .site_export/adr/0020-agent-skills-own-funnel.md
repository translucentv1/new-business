# ADR-0020 — Agent-Skills-Bundle über den eigenen Funnel (kein PromptBase)

**Status:** Akzeptiert (autonom, 2026-07-20) · **Autor:** Hermes (Cron)
**Supersedes:** — · **Related:** ADR-0013 (Download-Gate), ADR-0022 (Template-Pivot)

## Kontext
`products/promptbase-agent-skills/` ist fertig QA-t, aber der einzige geplante
Vertriebsweg (PromptBase) ist durch Hard Stops blockiert (Account, Payout,
Publishing, Bild-Gen). `DISTRIBUTION-VORSCHLAG.md` Kanal 6 benennt explizit den
eigenen new-business-Funnel (GitHub Pages + Stripe) als 0 %-Alternative.

## Entscheidung
Das Bundle wird als weiteres Template-Produkt in den bestehenden Funnel
eingehängt (`products/templates/agent-skills-bundle/`). Keine neuen Accounts,
keine Infra, kein Hard-Stop berührt.

## GRILL (selbst, schriftlich)
- **Bringt Sale näher?** JA — weiteres Live-Produkt im Funnel, mehr
  Verkaufsfläche bei 0 zusätzlichem Traffic-Aufwand.
- **MEASURED-Beleg?** JA — Skills QA-t (STATUS.md: 3 FIXED/4 PASS), valide
  `.md`, Preise gesetzt; Funnel bereits live + verifiziert (TB-10/11/23/24).
- **Ehrliches Loch?** Preis (6,99 €) ist ASSUMED-Geschäftsentscheidung; leicht
  korrigierbar. Conversion hängt wie bei allen Produkten am SEO-Traffic (passiv).
- **Hard Stop?** NEIN — eigener Stripe+Pages-Funnel ist bereits für Templates/
  Bücher in Gebrauch; kein PromptBase-Account, keine Bild-Gen nötig.

## Konsequenzen
- +1 verkaufsfähiges Produkt im Funnel, gleiche Pipeline wie Templates.
- PromptBase-Variante bleibt für den USER geparkt (GO-LIVE-PLAYBOOK.md).

## MEASURED (Belege dieses Durchgangs)
- `grep` Platzhalter in skills/: 0 Treffer.
- `test_download_gate.py`: 8/8 OK; `test_pd_processor.py`: 4/4 PASS (vor Build).
- Stripe-Link `tpl:agent-skills-bundle` erzeugt; Live-URL curl 200 (nach Build).
