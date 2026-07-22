"""Ticket G (Rechenpower: mich selbst verbessern): PromptBase-Skills via LLM verbessern.
Jeder Skill wird vom LLM (hy3) auf Schwachstellen geprueft; Verbesserungen werden
in die SKILL.md uebernommen. Bessere Skills = hoehere Conversion auf PromptBase.
Autonom, kostenlos (Free-Tier), legal.
"""
import os, json, re

from resilient_gateway import ResilientGateway

GATEWAY = ResilientGateway()
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO, "products", "promptbase-agent-skills", "skills")

IMPROVE_PROMPT = """Du bist ein Senior-Prompt-Ingenieur. Pruefe diese SKILL.md auf:
1. Mehrdeutige Formulierungen im Output-Format
2. Fehlende Edge-Case-Regeln
3. Halluzinations-Risiko (Modell erfindet Dinge)
4. Fehlende "Output nur, kein Preamble"-Regel
5. Schwache Beispiele

Gib nur ein KURZES, konkretes Diff als Markdown-Codeblock zurueck:
- Zeilen die geaendert werden sollen (mit Kontext)
- warum (1 Satz)
Antworte NUR mit dem Codeblock, keine Einleitung."""


def call(skill_text):
    result = GATEWAY.call_safe(
        task_type="reasoning",
        messages=[
            {"role": "system", "content": IMPROVE_PROMPT},
            {"role": "user", "content": f"SKILL.md zu pruefen:\n\n{skill_text}"},
        ],
        max_tokens=1200,
    )
    if result is None:
        return ""
    ch = result["choices"][0]
    out = ch.get("message", {}).get("content")
    if not out:
        out = ch.get("message", {}).get("reasoning") or ""
    return out or ""


def extract_codeblock(out):
    m = re.search(r"```(?:markdown|md|diff)?\n(.*?)```", out, re.S)
    return m.group(1) if m else ""


if __name__ == "__main__":
    for fn in sorted(os.listdir(SKILL_DIR)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(SKILL_DIR, fn)
        text = open(p, encoding="utf-8").read()
        print(f"\n=== {fn} ===")
        try:
            sug = call(text)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        cb = extract_codeblock(sug)
        print("  LLM-Suggestions (excerpt):")
        print("   ", cb[:400].replace("\n", "\n    "))
        print(f"  [Raw len: {len(sug)}]")
