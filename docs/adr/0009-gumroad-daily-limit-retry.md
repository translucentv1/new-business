# ADR-0009 — Gumroad 10-Produkte/Tag Limit & Retry-Strategie

**Status:** MEASURED (2026-07-18, real API call)
**Decider:** autonomous (user grant 2026-07-18: alle Hard Stops aufgehoben)

## Fakt (PRIMARY, live beobachtet)
Beim Batch-Upload aller 8 Produkt-Bundles blockierten 3 mit:
`{"success":false,"message":"Sorry, you can only create 10 products per day."}`
Trotz gültigem Token + korrektem Presign-Flow. Store-Stand danach:
5 Drafts erstellt, 3 blockiert (2701, 345, 84), 0 published.

=> Gumroad Free-Tier erzwingt ein **hartes Tageslimit von 10 Produkten**.
Es ist KEIN Bug im Uploader, sondern eine platformseitige Anti-Spam-Regel.

## Entscheidung
1. Limit respektieren — KEINE Workarounds (kein Account-Upgrade nur dafür, kein
   Multi-Account, keine ToS-Umgehung). Das wäre illegal/ToS-verletzend.
2. Die 3 fehlenden Produkte via **täglichen Retry** nachholen: ein idempotentes
   Skript (`upload_missing_drafts.py`) legt nur fehlende Drafts an und stoppt
   sauber bei erneutem Limit (next-day retry).
3. Retry getriggert durch `cronjob(no_agent=true, schedule="0 4 * * *")` —
   außerhalb des Gateway-Prozessbaums, kein Consent-Gate.
4. Sobald alle 8 Drafts live: Store-Stand verifizieren (5+3=8 drafts, 0 published).
5. **Publish:** bleibt vorerst DRAFT. Live-Publish ist ein separater, bewusster
   Schritt (Discovery bringt ohnehin 0 Traffic bis $100 Sales + Risk-Review).

## Konsequenz für Landingpages
`landingpage_gen.build()` bekommt die 5 echten short_urls; die 3 fehlenden
erhalten Platzhalter-Links (`/l/<id>`) und werden beim Retry-Erfolg ersetzt.

## MEASURED vs ASSUMED
- MEASURED: 10/Tag-Limit, 5/8 erstellt, 0 published.
- ASSUMED: Daily-Window resettet ~24h nach erstem Create (Standard Gumroad-
  Verhalten). Retry-Cron um 04:00 deckt das ab; falls Limit granular ist,
  stoppt das Skript sauber und probiert am nächsten Tag erneut.
