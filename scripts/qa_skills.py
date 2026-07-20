"""Ticket A (autonomous-business-design loop): SELLABLE SKILL QA.
RUN the skill on a realistic input, check raw output matches declared format.
Per skill pitfall: 'RUN IT, DON'T JUST READ IT'. Uses tencent/hy3:free.
"""
import os, sys, json, urllib.request, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO, "products", "promptbase-agent-skills", "skills")
KEY = None
for p in [os.path.join(REPO, ".env"), r"C:\Users\phili\AppData\Local\hermes\.env"]:
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.startswith("OPENROUTER_API_KEY="):
                KEY = line.strip().split("=", 1)[1]

# realistic inputs per skill
INPUTS = {
    "commit-message-writer": "git diff: changed whispercpp_stt.py to convert audio to wav via ffmpeg before calling whisper_cli",
    "ci-pipeline-trier": "GitHub Actions run failed:\nError: process '/usr/bin/npm' failed with exit code 1\nat Run npm ci\nENOENT: no such file or directory, open package-lock.json",
    "root-cause-debugger": "TypeError: Cannot read properties of undefined (reading 'map')\n    at renderList (app.js:42)\nWorks locally, crashes in prod after deploy.",
    "daily-standup-writer": "Today I fixed login bug, reviewed PR #14, started checkout refactor. Yesterday I wrote the auth spec. Blocker: waiting on API team for /users endpoint.",
    "messy-data-cleaner": "name,age,city\nMax,28,Berlin\nmax,,berlin\nAnna,34,München\nAnna,34,Munich\n(blank row)\nTom,NA,Hamburg",
    "test-case-generator": "def divide(a,b): return a/b  # function to test",
    "clean-code-reviewer": "def get(u):\n  x = db.query('SELECT * FROM u WHERE id='+u)\n  return x",
}


def call(skill_text, user_input):
    body = json.dumps({
        "model": "tencent/hy3:free",
        "messages": [
            {"role": "system", "content": skill_text},
            {"role": "user", "content": f"Input:\n{user_input}\n\nProduce your output per your instructions."},
        ],
        "max_tokens": 1500,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=60)
    j = json.loads(r.read())
    ch = j["choices"][0]
    content = ch.get("message", {}).get("content")
    if not content:
        content = ch.get("message", {}).get("reasoning") or ""
    return content or "", ch.get("finish_reason")


def check_format(name, out):
    o = out.strip().lower()
    checks = {}
    if name == "commit-message-writer":
        checks["type_prefix"] = any(o.startswith(t) for t in
            ["feat", "fix", "refactor", "docs", "test", "chore", "perf"])
        checks["no_preamble"] = not o.startswith(("here", "sure", "ok", "ich"))
    elif name == "ci-pipeline-trier":
        checks["has_failed_job"] = ("FAILED" in out or "FAILURE" in out or "first" in o or "red" in o)
        checks["has_fix"] = ("fix" in o or "solution" in o or "→" in out)
    elif name == "root-cause-debugger":
        checks["has_symptom"] = "symptom" in o
        checks["has_root_cause"] = "root cause" in o
    elif name == "daily-standup-writer":
        checks["has_gestern"] = ("gestern" in o or "yesterday" in o or "GESTERN" in out)
        checks["has_heute"] = ("heute" in o or "today" in o or "HEUTE" in out)
        checks["has_blocker"] = "blocker" in o
    elif name == "messy-data-cleaner":
        checks["mentions_dedupe"] = ("dedup" in o or "duplicate" in o or "near-dup" in o)
        checks["mentions_normalize"] = ("case" in o or "normalize" in o or "casing" in o or "datum" in o or "date" in o)
    elif name == "test-case-generator":
        checks["has_p0"] = "p0" in o
        checks["has_given_when_then"] = ("given" in o and "when" in o and "then" in o)
    elif name == "clean-code-reviewer":
        checks["has_p1_p4"] = any(f"[p{i}]" in out for i in range(1, 5)) or "VERDICT" in out
        checks["has_verdict"] = "verdict" in o
    return checks


results = []
for name, inp in INPUTS.items():
    sp = os.path.join(SKILL_DIR, name + ".md")
    skill = open(sp, encoding="utf-8").read()
    try:
        out, fr = call(skill, inp)
    except Exception as e:
        out, fr = f"ERROR: {e}", "error"
    checks = check_format(name, out)
    passed = all(checks.values())
    results.append((name, passed, fr, checks, out[:600]))
    time.sleep(2)

log = ["# SKILL QA-LOG (Ticket A) — MEASURED " + time.strftime("%Y-%m-%d %H:%M")]
log.append("Modell: tencent/hy3:free | 7 Skills auf realistischem Input getestet\n")
for name, passed, fr, checks, out in results:
    log.append(f"## {name}: {'PASS' if passed else 'PROBLEM'} (finish={fr})")
    log.append(f"  Checks: {checks}")
    log.append(f"  Output (excerpt):\n```\n{out}\n```\n")

open(os.path.join(REPO, "products", "promptbase-agent-skills", "QA-LOG.md"),
    "w", encoding="utf-8").write("\n".join(log))
print("QA done. Results:")
for name, passed, fr, checks, _ in results:
    print(f"  {name}: {'PASS' if passed else 'PROBLEM'} | {checks}")
