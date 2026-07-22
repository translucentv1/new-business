# Memory Setup — Status (2026-07-22)

## VERIFIZIERT (echter Lauf gegen Gemini API)
- `memory.py` = leichtgewichtiges persistentes Gedaechtnis (litellm + sqlite).
  Cold start ~3s (KEIN torch/unstructured wie Cognee).
- Round-Trip bestanden:
  - remember "Der erste Verkaufskanal sind Stripe Payment Links..." -> id=9c217122f3f3e0b2
  - remember "Das new-business Repo verkauft Notion-Templates..." -> id=23c7a529dc9986a9
  - recall "Wie verkaufen wir das Produkt?" ->
      [0.687] Stripe Payment Links
      [0.642] Notion-Templates DE-Nischen
    -> semantisch korrekt (nicht nur Keyword-Match).
  - list -> beide Eintraege vorhanden.
- LLM/Embeddings = Gemini (kostenlos). Key aus HERMES_HOME/.env gelesen,
  NICHT im Repo. Daten in cognee_data/memory.db (gitignored).
- Gemini-Embedding-Dimension: 3072 (gemini-embedding-001, gemessen).

## Cognee (schwer, hier NICHT nutzbar)
- cognee 1.4.0 + cognee-mcp 0.5.5 installiert in .venv (isoliert),
  aber: `import cognee` dauert >10 Min (torch 2.13 + unstructured unter
  Windows/MSYS) -> fuer interaktives Gedaechtnis unbrauchbar.
- MCP-Server startet nur im Vordergrund; als Daemon/BG stirbt er.
  Hermes' 32s-MCP-Timeout reicht ohnehin nicht.
- Cognee-Artefakte (cognee_daemon.py, cognee_cli_verify.py,
  cognee_smoke_test.py) daher GELoesCHT. .venv mit cognee/cognee-mcp
  kann bei Bedarf via uv entfernt werden.

## Nutzung (fuer Hermes)
cd C:/Users/phili/new-business
env -u PYTHONPATH .venv/Scripts/python.exe memory.py remember "Fakt"
env -u PYTHONPATH .venv/Scripts/python.exe memory.py recall "Frage"
env -u PYTHONPATH .venv/Scripts/python.exe memory.py list
env -u PYTHONPATH .venv/Scripts/python.exe memory.py forget   # wipe

Key wird automatisch aus %LOCALAPPDATA%/hermes/.env (GEMINI_API_KEY) gelesen.
