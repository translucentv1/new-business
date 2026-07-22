"""Integration-Verifikation fuer resilient_gateway.py.

Laeuft OHNE Secrets im Chat: Keys kommen aus der Hermes-.env bzw. Env.
Testet laut Task-Spec Punkt 5:
 (a) echte Calls pro task_type (>=3) laufen durch  -> use_cache=False + unique Prompts
 (b) simulierter 429 (Circuit Breaker trip) -> automatischer Fallback greift
 (c) call_safe() liefert None statt Exception bei Totalausfall

Schreibt alle Belege nach gateway.log (und druckt sie).
"""
import os, sys, time, logging

HERMES_ENV = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "AppData", "Local", "hermes", ".env"))
for p in (HERMES_ENV,):
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line.startswith(("OPENROUTER_API_KEY=", "NVIDIA_API_KEY=", "NOUS_PORTAL_API_KEY=")):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resilient_gateway import ResilientGateway

logging.basicConfig(
    filename="gateway.log", level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("verify")

gw = ResilientGateway()

print("=== ENV presence (length only, no values) ===")
for k in ("OPENROUTER_API_KEY", "NVIDIA_API_KEY", "NOUS_PORTAL_API_KEY"):
    v = os.environ.get(k, "")
    print(f"  {k}: {'SET len='+str(len(v)) if v else 'absent'}")

TASKS = {
    "reasoning": "Erklaere in einem Satz, warum Fallback-Ketten Resilienz erhoehen.",
    "coding": "Schreibe eine Python-Funktion, die prueft, ob ein String ein Palindrom ist.",
    "long_context": "Fasse in einem Satz zusammen: 'Resiliente Systeme ueberleben Einzelausfaelle durch Redundanz und automatischen Failover.'",
}

def _content(r):
    if r is None:
        return None
    ch = r["choices"][0]["message"]
    return ch.get("content") or ch.get("reasoning") or ""

results = {}
print("\n=== (a) ECHTE CALLS je task_type (>=3, use_cache=False, unique Prompts) ===")
for ttype, q in TASKS.items():
    ok = 0
    for i in range(3):
        # unique prompt -> kein Cache-Treffer, echter Call jedes Mal
        prompt = f"{q} (Runde {i+1})"
        r = gw.call_safe(task_type=ttype,
                         messages=[{"role": "user", "content": prompt}],
                         max_tokens=256, use_cache=False)
        if r is None:
            print(f"  [{ttype}] call {i+1}: None (kein Modell verfuegbar)")
            continue
        c = _content(r) or ""
        ok += 1
        print(f"  [{ttype}] call {i+1}: OK ({len(c)} chars)")
        time.sleep(1)
    results[ttype] = ok
    print(f"  => {ttype}: {ok}/3 erfolgreich")

print("\n=== (b) SIMULIERTER 429 -> Fallback greift (Circuit Breaker) ===")
gw.breaker.trip("nvidia_nim", "z-ai/glm-5.2")
log.warning("TEST: Circuit OPEN fuer nvidia_nim/z-ai/glm-5.2 erzwungen (simulierter 429-Cooldown)")
r = gw.call_safe(task_type="reasoning",
                 messages=[{"role": "user", "content": TASKS["reasoning"] + " (Fallback-Test)"}],
                 max_tokens=256, use_cache=False)
fb_ok = r is not None
print(f"  nach simuliertem 429 auf nvidia_nim: call_safe -> "
      f"{'OK (Fallback griff)' if fb_ok else 'None (Kette komplett blockiert)'}")
gw.breaker.reset("nvidia_nim", "z-ai/glm-5.2")

print("\n=== (c) call_safe liefert None statt Exception bei Totalausfall ===")
saved = {}
for k in ("OPENROUTER_API_KEY", "NVIDIA_API_KEY", "NOUS_PORTAL_API_KEY"):
    saved[k] = os.environ.pop(k, None)
r = gw.call_safe(task_type="reasoning",
                 messages=[{"role": "user", "content": "test"}], max_tokens=64)
crashed = False
try:
    gw.call(task_type="reasoning", messages=[{"role": "user", "content": "test"}], max_tokens=64)
except Exception as e:
    crashed = True
    print(f"  call() bei Totalausfall: Exception gefangen ({type(e).__name__}) -> sicher")
for k, v in saved.items():
    if v is not None:
        os.environ[k] = v
print(f"  call_safe() bei Totalausfall: returned {r!r} (None = korrekt, kein Crash)")

print("\n=== ZUSAMMENFASSUNG ===")
for t, ok in results.items():
    print(f"  {t}: {ok}/3 echte Calls erfolgreich")
print(f"  Fallback bei simuliertem 429: {'JA' if fb_ok else 'NEIN'}")
print(f"  call_safe None bei Totalausfall: {'JA' if r is None else 'NEIN'}")
print("  Siehe gateway.log fuer detaillierte Belege (OK-Zeilen, Circuit-Warnungen).")
