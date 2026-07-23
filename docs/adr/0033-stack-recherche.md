# ADR-0033 — Stack-Recherche: Hermes-Ökosystem + günstige Infra

Erstellt: 2026-07-23 (autonome Recherche, Nutzer-Wunsch "bessere/tools billige stacks")
Quellen: hermes-agent.nousresearch.com/docs (offiziell), github.com/0xNyk/awesome-hermes-agent,
github.com/NousResearch/hermes-agent, promptquorum.com Local LLM Stack 2026 (mit Primärquellen-Links)

## Hermes-Ökosystem (was wir verpassen könnten)
- **awesome-hermes-agent** (GitHub 0xNyk, 4.9k★, wöchentlich gepflegt): kuratierte
  Skills, Plugins, Memory-Provider, Tools, Surfaces. Wir nutzen nur bundled-Skills.
  → Hebel: dort gezielt nützliche Skills/Provider installieren (z.B. Qdrant-Memory,
     Honcho user-modeling). Aber: nur was autonom/legal passt.
- **Honcho** (plastic-labs, dialectic user modeling): externe User-Modellierung, läuft
  zusätzlich zu Cognee. Optional, kein Muss.
- **Memory-Architektur bestätigt**: MEMORY.md/USER.md (bounded 2200/1375 char) + FTS5
  session_search + externe Provider. Wir haben Cognee already. Passt.

## Günstiger AI-Stack 2026 (Primärquellen-gestützt)
| Layer | Tool | Lizenz/Kosten | Zweck |
|---|---|---|---|
| Local LLM server | Ollama | OSS, free | einfach, Chat/Reasoning lokal |
| Prod LLM server | vLLM | OSS, free | 3-5× throughput, API/Batch |
| Code-Modell | Qwen3-Coder (Apache 2.0) | free, self-host | Coding 82% HumanEval |
| Vektor-DB | Qdrant | Apache 2.0, Docker | RAG embeddings lokal/privat |
| RAG | LlamaIndex | OSS | Chunking + Retrieval |
- Kosten: 0 EUR wenn selbst gehostet (braucht GPU/VRAM). Wir haben aktuell KEINEN lokale
  GPU im Stack → hy3 (Nous Portal, :free) ist der einzige Modell-Zugang.
- **Relevanz für uns**: erst Sinnvoll NACH erstem Sale (Reinvest in GPU/Rechenpower,
  ADR-0031 70%-Anteil). Vorher: hy3:free reicht.

## Fazit
- Wir haben vermutlich schon den besten *agent*-Stack (Hermes + Cognee + Skills + hy3:free).
- Lücke: externe Community-Skills (awesome-hermes-agent) ungenutzt → gezielt prüfen.
- Billiger Self-Host-Stack lohnt erst nach Sale (Reinvest-Budget).
- KEIN AI-Slop: alle Quellen offizielle Docs/GitHub/technische Blogs mit Primärquellen.

## Nächste Schritte (optional, nach Sale)
1. awesome-hermes-agent scannen → 1-2 nützliche Skills/Provider installieren
2. Bei Reinvest: Qwen3-Coder + vLLM auf GPU für Code-Subagenten (senkt API-Kosten)
