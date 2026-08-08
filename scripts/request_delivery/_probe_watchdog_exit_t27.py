"""Ticket 27: misst den GEAENDERTEN Zweig des Waechter-Loaders.

Der Loader liegt ausserhalb des Repos ($HERMES_HOME/scripts) und hat keinen
--selftest. Statt zu behaupten "exit 0 ist jetzt exit 3", wird eine Kopie mit
verbogenem TARGET wirklich ausgefuehrt. Die installierte Datei bleibt
unangetastet (nur gelesen).
"""

import hashlib
import os
import subprocess
import sys
import tempfile

LOADER = os.path.join(os.environ.get("HERMES_HOME", ""), "scripts",
                      "rtd_health_watchdog.py")
ok = bad = 0


def t(cond, label):
    global ok, bad
    if cond:
        ok += 1
        print(f"  OK   {label}")
    else:
        bad += 1
        print(f"  FAIL {label}")


src_bytes = open(LOADER, "rb").read()
sha_vorher = hashlib.sha256(src_bytes).hexdigest()
src = src_bytes.decode("utf-8")
print(f"Loader: {LOADER}\nsha256: {sha_vorher}\n")

tmp = tempfile.mkdtemp(prefix="t27_wd_")

# Fall 1: Repo-Skript fehlt -> frueher exit 0 (GRUEN trotz kaputter
# Installation), jetzt exit 3.
fehlt = os.path.join(tmp, "wd_fehlt.py")
alt = '''TARGET = os.path.join(
    r"C:\\Users\\phili\\new-business", "scripts", "request_delivery",
    "cron_health_audit.py",
)'''
neu = f'TARGET = {os.path.join(tmp, "gibt_es_nicht.py")!r}'
t(alt in src, "Anker fuer TARGET gefunden")
with open(fehlt, "w", encoding="utf-8", newline="") as fh:
    fh.write(src.replace(alt, neu, 1))
p = subprocess.run([sys.executable, fehlt], capture_output=True, text=True,
                   timeout=120)
aus = (p.stdout or "") + (p.stderr or "")
t(p.returncode == 3, f"fehlendes Audit-Skript -> exit {p.returncode} (erwartet 3)")
t(p.returncode != 0, "fehlendes Audit-Skript ist NICHT mehr gruen")
t(p.returncode != 2, "benutzt NICHT Code 2 (Interpreter-reserviert)")
t("WAECHTER_UNGEPRUEFT" in aus,
  "Wort bleibt WAECHTER_UNGEPRUEFT (kein Defekt-Claim gegen den Cron)")

# Fall 2: Audit antwortet mit rc=2 (unmessbar) -> frueher exit 0, jetzt 3.
stub = os.path.join(tmp, "audit_rc2.py")
with open(stub, "w", encoding="utf-8", newline="") as fh:
    fh.write("import sys\nprint('ERGEBNIS: CRON_HEALTH_UNGEPRUEFT')\n"
             "sys.exit(2)\n")
wd2 = os.path.join(tmp, "wd_rc2.py")
with open(wd2, "w", encoding="utf-8", newline="") as fh:
    fh.write(src.replace(alt, f"TARGET = {stub!r}", 1))
p2 = subprocess.run([sys.executable, wd2], capture_output=True, text=True,
                    timeout=120)
aus2 = (p2.stdout or "") + (p2.stderr or "")
t(p2.returncode == 3, f"Audit rc=2 -> Waechter exit {p2.returncode} (erwartet 3)")
t("WAECHTER_UNGEPRUEFT" in aus2, "Wort korrekt bei unmessbarem Audit")

# Fall 3: echter Defekt bleibt Code 1 - sonst waeren die beiden Faelle
# wieder ununterscheidbar.
stub1 = os.path.join(tmp, "audit_rc1.py")
with open(stub1, "w", encoding="utf-8", newline="") as fh:
    fh.write("import sys\nprint('ERGEBNIS: CRON_HEALTH_DEFEKT')\nsys.exit(1)\n")
wd3 = os.path.join(tmp, "wd_rc1.py")
with open(wd3, "w", encoding="utf-8", newline="") as fh:
    fh.write(src.replace(alt, f"TARGET = {stub1!r}", 1))
p3 = subprocess.run([sys.executable, wd3], capture_output=True, text=True,
                    timeout=120)
t(p3.returncode == 1, f"echter Cron-Defekt -> exit {p3.returncode} (erwartet 1)")
t("WAECHTER_DEFEKT" in (p3.stdout or ""), "Wort WAECHTER_DEFEKT bei rc=1")

# Fall 4: gesund bleibt gruen.
stub0 = os.path.join(tmp, "audit_rc0.py")
with open(stub0, "w", encoding="utf-8", newline="") as fh:
    fh.write("import sys\nprint('ERGEBNIS: CRON_HEALTH_OK')\nsys.exit(0)\n")
wd4 = os.path.join(tmp, "wd_rc0.py")
with open(wd4, "w", encoding="utf-8", newline="") as fh:
    fh.write(src.replace(alt, f"TARGET = {stub0!r}", 1))
p4 = subprocess.run([sys.executable, wd4], capture_output=True, text=True,
                    timeout=120)
t(p4.returncode == 0, f"gesundes Audit bleibt gruen (exit {p4.returncode})")
t(len({p4.returncode, p3.returncode, p2.returncode}) == 3,
  f"OK/DEFEKT/UNGEPRUEFT paarweise verschieden "
  f"({p4.returncode}/{p3.returncode}/{p2.returncode})")

sha_nachher = hashlib.sha256(open(LOADER, "rb").read()).hexdigest()
t(sha_nachher == sha_vorher, "installierter Loader unangetastet (sha256 gleich)")

print(f"\nERGEBNIS: {'WAECHTER_PROBE_OK' if not bad else 'WAECHTER_PROBE_FEHLGESCHLAGEN'}"
      f" {ok}/{ok + bad}")
sys.exit(1 if bad else 0)
