"""QA der verbesserten Skills (Ticket G3): prueft ob _improved.md noch 7/7 PASS haelt.
Ersetzt temporaer die SKILL.md durch _improved, laeuft qa_skills.py, stellt zurueck.
Oder: kopiert _improved -> temp und testet direkt.
"""
import os, sys, subprocess, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO, "products", "promptbase-agent-skills", "skills")

# Baue eine QA-Variante, die _improved testet
src = open(os.path.join(REPO, "scripts", "qa_skills.py"), encoding="utf-8").read()
# qa_skills.py sucht in SKILL_DIR nach <name>.md. Wir testen _improved stattdessen:
# Einfach: kopiere _improved -> <name>.md temporaer, qa laufen lassen, restore.
import glob
improved = glob.glob(os.path.join(SKILL_DIR, "*_improved.md"))
print(f"Found {len(improved)} improved skills")
for imp in improved:
    base = os.path.basename(imp).replace("_improved", "")
    orig = os.path.join(SKILL_DIR, base)
    bak = orig + ".bak"
    if os.path.exists(orig):
        shutil.copy(orig, bak)
    shutil.copy(imp, orig)  # temp replace

# qa_skills.py laufen lassen
r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "qa_skills.py")],
                   capture_output=True, text=True)
print(r.stdout[-1500:])

# restore
for imp in improved:
    base = os.path.basename(imp).replace("_improved", "")
    orig = os.path.join(SKILL_DIR, base)
    bak = orig + ".bak"
    if os.path.exists(bak):
        shutil.move(bak, orig)
print("RESTORED originals")
