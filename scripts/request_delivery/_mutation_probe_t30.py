"""Ticket 30 - Mutationsprobe: faengt der Selftest von cron_delivery_audit.py
echte Defekte, oder besteht er nur, weil nichts geprueft wird?

Vorgehen (wie _mutation_probe_t28.py): der PRODUKTIVCODE wird mutiert, der
ECHTE Selftest laufen gelassen und ROT erwartet. Danach sha256-genaue
Wiederherstellung. Belegt wird der rc-Wechsel 0 -> 1 -> 0.

Ein Mutant, der gruen bleibt, ist ein Loch im Selftest.
"""

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "cron_delivery_audit.py")

# (Label, alter Text, neuer Text) - jede Mutation bricht eine echte Eigenschaft.
MUTANTS = [
    (
        "Defektzaehler ignoriert (meldet nie DEFEKT)",
        "    if defects:\n        return lines, DEFEKT",
        "    if False:\n        return lines, DEFEKT",
    ),
    (
        "Leere Zielmenge wird gruen (Leere-Schleife-Falle)",
        "        return lines, UNGEPRUEFT\n    return lines, OK",
        "        return lines, OK\n    return lines, OK",
    ),
    (
        "Platzhalter 'self' nicht mehr als Gift bekannt",
        'POISON_MEASURED = {"self"}',
        "POISON_MEASURED = set()",
    ),
    (
        "WhatsApp-Formregel abgeschaltet",
        '        if "@" not in s and not s.lstrip("+").isdigit():\n'
        '            return True, "WHATSAPP-FORM"',
        '        if False:\n            return True, "WHATSAPP-FORM"',
    ),
    (
        "Fallback-Pruefung uebersprungen (nur Zustand, nicht Eigenschaft)",
        "        bad, rule = chat_id_verdict(platform, chat_id)\n"
        "        env_var = \"\"",
        "        bad, rule = (False, \"\")\n"
        "        env_var = \"\"",
    ),
    (
        "disabled-Filter entfernt (misst die falsche Menge)",
        '        if not job.get("enabled"):\n            continue',
        '        if False:\n            continue',
    ),
    (
        "unaufloesbares Ziel wird durchgewunken",
        "            if not target:\n                defects += 1",
        "            if not target:\n                defects += 0",
    ),
    # --- Mutanten fuer die Alarmtraeger-Regel (dieser Tick) -----------------
    (
        "Alarmwortliste leer (stummer Alarmtraeger wird gruen)",
        'ALARM_TOKENS = ("ERSTER SALE", "DEFEKT", "ALARM", "*** ")',
        "ALARM_TOKENS = ()",
    ),
    (
        "Alarmtraeger erkannt, aber nicht als Defekt gezaehlt",
        "            if worte:\n                defects += 1",
        "            if worte:\n                defects += 0",
    ),
    (
        "unlesbare Quelle wird durchgewunken statt gemeldet",
        "            if quelle is None:\n                defects += 1",
        "            if quelle is None:\n                defects += 0",
    ),
    (
        "Skriptquelle ignoriert (faellt still auf den prompt zurueck)",
        '    script = (job.get("script") or "").strip()',
        '    script = ""',
    ),
]


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_selftest():
    proc = subprocess.run(
        [sys.executable, TARGET, "--selftest"],
        capture_output=True, text=True, cwd=HERE, timeout=600,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main():
    results = []
    # BINAER lesen/schreiben: Textmodus uebersetzt unter Windows \n -> \r\n und
    # die "Wiederherstellung" waere byte-ungenau (genau das ist beim ersten
    # Lauf passiert). Die Probe darf den Produktivcode NICHT veraendern.
    with open(TARGET, "rb") as _fh:
        original_bytes = _fh.read()
    original = original_bytes.decode("utf-8")
    digest_before = sha256(TARGET)
    print("Zieldatei : %s" % TARGET)
    print("sha256 vor: %s" % digest_before)

    rc0, out0 = run_selftest()
    print("\n[0] Unmutiert: rc=%d %s" % (rc0, out0.strip().splitlines()[-1] if out0.strip() else ""))
    results.append(("Ausgang gruen (rc=0)", rc0 == 0, out0[-200:]))

    try:
        for label, old, new in MUTANTS:
            if old not in original:
                results.append(("ANKER FEHLT: %s" % label, False, "Muster nicht gefunden"))
                print("  ANKER FEHLT  %s" % label)
                continue
            mutated = original.replace(old, new, 1)
            if mutated == original:
                results.append(("MUTATION WIRKUNGSLOS: %s" % label, False, ""))
                continue
            with open(TARGET, "wb") as fh:
                fh.write(mutated.encode("utf-8"))
            rc, out = run_selftest()
            rot = rc != 0
            sauber = "Traceback" not in out
            results.append(("rot: %s" % label, rot, "rc=%d" % rc))
            results.append(("kein Absturz: %s" % label, sauber, out[-160:]))
            print("  %-4s rc=%d  %s%s" % ("ROT" if rot else "GRUEN", rc, label,
                                          "" if sauber else "  [TRACEBACK!]"))
    finally:
        with open(TARGET, "wb") as fh:
            fh.write(original_bytes)

    digest_after = sha256(TARGET)
    print("\nsha256 nach: %s" % digest_after)
    results.append(("sha256-genau wiederhergestellt", digest_after == digest_before,
                    "%s != %s" % (digest_before, digest_after)))

    rc2, out2 = run_selftest()
    print("[N] Nach Restore: rc=%d %s" % (rc2, out2.strip().splitlines()[-1] if out2.strip() else ""))
    results.append(("Ausgang wieder gruen (rc=0)", rc2 == 0, out2[-200:]))

    ok = sum(1 for _l, c, _d in results if c)
    print()
    for label, cond, detail in results:
        if not cond:
            print("  FAIL %-52s %s" % (label, str(detail)[:120]))
    print("MUTATIONSPROBE %d/%d" % (ok, len(results)))
    if ok == len(results):
        print("\nERGEBNIS: MUTATION_PROBE_OK (rc-Wechsel 0 -> 1 -> 0 belegt)")
        return 0
    print("\nERGEBNIS: MUTATION_PROBE_DEFEKT")
    return 1


if __name__ == "__main__":
    sys.exit(main())
