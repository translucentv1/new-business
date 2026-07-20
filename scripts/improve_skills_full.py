"""Ticket G2: LLM generiert verbesserte SKILL.md direkt (nicht nur Vorschläge).
Pro Skill: alte SKILL.md -> hy3 -> verbesserte Version (selbe Struktur,
deutlichere Formate, Edge-Cases, Beispiele, strikteres 'Output ONLY').
Speichert nach *_improved.md. Agent verifiziert danach via QA (qa_skills.py).
"""
import os, json, urllib.request, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO, "products", "promptbase-agent-skills", "skills")
KEY = None
for p in [os.path.join(REPO, ".env"), r"C:\Users\phili\AppData\Local\hermes\.env"]:
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.startswith("OPENROUTER_API_KEY="):
                KEY = line.strip().split("=", 1)[1]

SYS = """Du bist Senior-Prompt-Ingenieur. Nimm diese SKILL.md und gib die VERBESSERTE Version zurueck.
Regeln:
- Behalte frontmatter (name/description) und die Grundstruktur bei.
- Mache das Output-Format explizit (keine <...> Platzhalter mehrdeutig lassen; sage genau welcher Typ).
- Fuege eine '## Examples' Sektion mit 1 konkreten Beispiel-Input + erwartetem Output hinzu.
- Fuege Edge-Case-Regeln hinzu (leerer Input, mehrere Fehler, nicht reproduzierbar).
- Mache 'Output ONLY' strikt: keine Einleitung, kein Postscript, kein Markdown-Codeblock um das Ganze.
- Keine neuen Halluzinations-Risiken. Antworte NUR mit der verbesserten SKILL.md (inkl. frontmatter)."""

def call(text):
    body = json.dumps({"model": "tencent/hy3:free",
        "messages": [{"role":"system","content":SYS},
                     {"role":"user","content":f"SKILL.md:\n\n{text}"}],
        "max_tokens": 2500}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=body, headers={"Authorization": f"Bearer {KEY}", "Content-Type":"application/json"})
    r = urllib.request.urlopen(req, timeout=90)
    j = json.loads(r.read()); ch = j["choices"][0]
    return (ch.get("message",{}).get("content") or ch.get("message",{}).get("reasoning") or "")

if __name__ == "__main__":
    for fn in sorted(os.listdir(SKILL_DIR)):
        if not fn.endswith(".md"): continue
        text = open(os.path.join(SKILL_DIR, fn), encoding="utf-8").read()
        print(f"=== improving {fn} ===", flush=True)
        try:
            improved = call(text)
        except Exception as e:
            print(f"  ERROR {e}"); continue
        # strip accidental code fences
        if improved.startswith("```"):
            improved = improved.split("\n", 1)[1]
        if improved.endswith("```"):
            improved = improved.rsplit("```", 1)[0]
        out = os.path.join(SKILL_DIR, fn.replace(".md", "_improved.md"))
        open(out, "w", encoding="utf-8").write(improved)
        print(f"  written {out} ({len(improved)} chars)", flush=True)
        time.sleep(2)
    print("ALL DONE", flush=True)
