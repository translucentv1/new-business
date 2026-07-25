"""
Deliverable generator for Request-to-Delivery (ADR-0035).

Given a customer request string, produce a first-draft deliverable:
  - text/template/summary  -> markdown
  - code snippet           -> fenced code block

Strategy (autonomous, 0 cost):
  1. If a local LLM endpoint is reachable (HERMES/ Nous local or Ollama),
     send the request and return the raw completion.
  2. Else fall back to a structured template so the pipeline still produces
     something reviewable. The operator (or a later agent turn) upgrades the
     quality once a paid LLM key is available.

NO external API keys are required for the fallback. When an LLM is wired,
its key comes from the environment, never hardcoded.
"""
import os
import json
import urllib.request
import urllib.error

LOCAL_LLM_URL = os.environ.get(
    "LOCAL_LLM_URL",
    "http://127.0.0.1:11434/api/generate",  # Ollama default
)


def _call_local_llm(prompt: str, timeout: int = 60) -> str | None:
    body = json.dumps({
        "model": os.environ.get("LOCAL_LLM_MODEL", "llama3.1:latest"),
        "prompt": prompt,
        "stream": False,
    }).encode()
    try:
        req = urllib.request.Request(
            LOCAL_LLM_URL, data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        return data.get("response") or data.get("text")
    except Exception:
        return None


def generate(request: str) -> str:
    prompt = (
        "Erstelle ein fertiges Lieferobjekt (deutsch) fuer diese Anfrage. "
        "Sei konkret und sofort nutzbar:\n\n" + request
    )
    llm_out = _call_local_llm(prompt)
    if llm_out and len(llm_out.strip()) > 20:
        return llm_out.strip()

    # Fallback template (no LLM available)
    return f"""# Dein Lieferobjekt

**Anfrage:** {request}

## Entwurf (Template-Fallback – kein LLM verfuegbar)
1. Kernpunkt der Anfrage strukturiert erfassen.
2. Schritt-fuer-Schritt-Ausarbeitung.
3. Direkt anwendbares Ergebnis.

> Hinweis: Mit einem lokalen oder per API angebundenen LLM wird dieser
> Entwurf automatisch mit echtem Inhalt gefuellt. Siehe generator.py.
"""


if __name__ == "__main__":
    import sys
    req = sys.argv[1] if len(sys.argv) > 1 else "Beispielanfrage"
    print(generate(req))
