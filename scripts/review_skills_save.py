import os, json, urllib.request, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO, "products", "promptbase-agent-skills", "skills")
KEY = None
for p in [os.path.join(REPO, ".env"), r"C:\Users\phili\AppData\Local\hermes\.env"]:
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.startswith("OPENROUTER_API_KEY="):
                KEY = line.strip().split("=", 1)[1]

IMPROVE_PROMPT = """Du bist ein Senior-Prompt-Ingenieur. Pruefe diese SKILL.md auf Schwachstellen:
1. Mehrdeutige Formulierungen im Output-Format
2. Fehlende Edge-Case-Regeln
3. Halluzinations-Risiko
4. Fehlende "Output nur, kein Preamble"-Regel
5. Schwache Beispiele

Antworte mit KONKRETEN, anwendbaren Verbesserungen als Markdown-Block:
Fuer jede Aenderung: den exakten alten Text-Ausschnitt, den neuen Text, und 1 Satz Grund.
Sei praezise, keine Einleitung."""

def call(skill_text):
    body = json.dumps({"model": "tencent/hy3:free",
        "messages": [{"role":"system","content":IMPROVE_PROMPT},
                     {"role":"user","content":f"SKILL.md:\n\n{skill_text}"}],
        "max_tokens": 1500}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=body, headers={"Authorization": f"Bearer {KEY}", "Content-Type":"application/json"})
    r = urllib.request.urlopen(req, timeout=60)
    j = json.loads(r.read()); ch = j["choices"][0]
    return (ch.get("message",{}).get("content") or ch.get("message",{}).get("reasoning") or "")

out_path = os.path.join(REPO, "products", "promptbase-agent-skills", "SKILL-LLM-REVIEW.md")
lines = ["# LLM-Review der 7 Agent-Skills (Ticket G — Rechenpower-Selbstverbesserung)\n"]
for fn in sorted(os.listdir(SKILL_DIR)):
    if not fn.endswith(".md"): continue
    text = open(os.path.join(SKILL_DIR, fn), encoding="utf-8").read()
    lines.append(f"\n## {fn}\n")
    try:
        sug = call(text)
    except Exception as e:
        lines.append(f"  ERROR: {e}\n"); continue
    lines.append(sug + "\n")
    import time; time.sleep(2)

open(out_path, "w", encoding="utf-8").write("\n".join(lines))
print("REVIEW written:", out_path)
