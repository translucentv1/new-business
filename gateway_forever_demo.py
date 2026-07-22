"""Demo: run_forever() ueberlebt Fehler in work_fn (Punkt 4 + 5d).

Wird NICHT endlos gestartet - wir brechen nach N Zyklen sauber ab,
indem work_fn einmal einen Fehler wirft und wir danach via KeyboardInterrupt
simulieren. Zeigt: run_forever faengt unerwartete Exceptions in work_fn
und laeuft weiter, statt den Prozess zu toeten.

Echter 24/7-Betrieb: run_forever(one_step, idle_sleep_seconds=...) in einem
Prozess-Supervisor starten (siehe Bericht Punkt 7).
"""
import os, sys, time
HERMES_ENV = r"C:\Users\phili\AppData\Local\hermes\.env"
for line in open(HERMES_ENV, encoding="utf-8", errors="ignore"):
    line = line.strip()
    if line.startswith(("OPENROUTER_API_KEY=", "NVIDIA_API_KEY=", "NOUS_PORTAL_API_KEY=")):
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resilient_gateway import ResilientGateway, run_forever

gw = ResilientGateway()

def one_step():
    # bewusst: 1. Zyklus wirft, um run_forever's Resilience zu zeigen
    one_step.calls += 1
    if one_step.calls == 1:
        raise RuntimeError("SIMULIERTER BUG in work_fn (zyklus 1)")
    r = gw.call_safe(task_type="reasoning",
                     messages=[{"role": "user", "content": f"Zyklus {one_step.calls}: kurz antworten."}],
                     max_tokens=64, use_cache=False)
    if r is None:
        print(f"  [Zyklus {one_step.calls}] kein Modell verfuegbar -> uebersprungen, warte auf naechsten")
        return
    print(f"  [Zyklus {one_step.calls}] OK: {(r['choices'][0]['message'].get('content') or '')[:60]}...")

one_step.calls = 0

print("Starte run_forever-Demo (bricht nach 3 Zyklen via KeyboardInterrupt ab)...")
try:
    # wir laufen nur kurz: nach 3 erfolgreichen/geskippten Zyklen selbst abbrechen
    orig = one_step
    def limited():
        orig()
        if orig.calls >= 4:
            raise KeyboardInterrupt  # sauberer Supervisor-Stop simuliert
    run_forever(limited, idle_sleep_seconds=2.0)
except KeyboardInterrupt:
    print("DEMO ENDE: run_forever hat den simulierten Bug in Zyklus 1 ueberlebt und weitergearbeitet.")
