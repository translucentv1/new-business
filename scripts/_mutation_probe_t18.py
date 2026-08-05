#!/usr/bin/env python3
"""Mutationsprobe fuer Ticket 18 (verify.py).

Zwei Beweisrichtungen:

A) ALT-STAND-PROBE — nicht argumentiert, sondern AUSGEFUEHRT.
   Die Fassung aus HEAD wird in eine Sandbox gelegt und mit genau den Defekten
   konfrontiert, die der neue Selftest abdeckt. Erwartung: sie merkt sie nicht.

B) MUTANTEN DER HEUTIGEN FASSUNG — der Selftest muss rot werden, wenn man
   verify.py kaputtmacht. Sonst ist er Dekoration.
   Mutiert wird der PRODUKTIVCODE auf der Platte; danach sha256-genaue
   Wiederherstellung und rc-Wechsel 0 -> 1 -> 0.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "scripts" / "verify.py"
sys.path.insert(0, str(ROOT / "scripts"))

from _verify_selftest import (
    build_sandbox,
    m_keywords_geschrumpft,
    m_kw_demand_stumm,
    run_sandbox,
)

results: list[tuple[bool, str]] = []


def t(cond: bool, label: str, detail: str = "") -> bool:
    results.append((bool(cond), label + (f" — {detail}" if detail else "")))
    return bool(cond)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def alt_stand() -> str:
    r = subprocess.run(["git", "show", "HEAD:scripts/verify.py"], cwd=ROOT,
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("git show HEAD:scripts/verify.py fehlgeschlagen: " + r.stderr[:120])
    return r.stdout


def selftest_rc() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(VERIFY), "--selftest"],
                       cwd=ROOT, capture_output=True, text=True, timeout=900)
    return r.returncode, r.stdout + r.stderr


# ------------------------------------------------------------------ Teil A
def teil_a() -> None:
    print("== A) ALT-STAND-PROBE (HEAD:scripts/verify.py, ausgefuehrt) ==")
    alt = alt_stand()

    # A1: stille Schrumpfung der Pruefflaeche
    tmp = build_sandbox()
    try:
        (tmp / "scripts" / "verify.py").write_text(alt, encoding="utf-8")
        m_keywords_geschrumpft(tmp)
        rc, out = run_sandbox(tmp, "--offline")
        n = re.search(r"VERIFY: (\d+) ok", out)
        t(rc == 0, "A1 Alt-Stand BLIND bei KEYWORDS 37->1",
          f"rc={rc} ({n.group(1) if n else '?'} ok) -> " +
          ("gruen trotz 36 ungeprueften Seiten" if rc == 0 else "unerwartet rot"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # A2: Netzausfall wird als kaputte Seite gemeldet
    tmp = build_sandbox()
    try:
        v = tmp / "scripts" / "verify.py"
        neu = alt.replace('BASE = "https://translucentv1.github.io/new-business"',
                          'BASE = "https://127.0.0.1:9/new-business"')
        if neu == alt:
            raise RuntimeError("BASE-Zeile im Alt-Stand nicht gefunden")
        v.write_text(neu, encoding="utf-8")
        m_kw_demand_stumm(tmp)
        rc, out = run_sandbox(tmp, "--live")
        falscher_claim = any(ln.strip().startswith("FAIL  live:") for ln in out.splitlines())
        t(falscher_claim and rc == 1,
          "A2 Alt-Stand meldet Netzausfall als Seitendefekt",
          f"rc={rc}, 'FAIL  live:'={'ja' if falscher_claim else 'nein'} "
          "(kein drittes Ergebniswort)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # A3: akkumulierende Ergebnislisten
    tmp = build_sandbox()
    try:
        (tmp / "scripts" / "verify.py").write_text(alt, encoding="utf-8")
        code = ("import sys;sys.argv=['v','--offline'];sys.path.insert(0,r'%s');"
                "import verify;verify.main();n1=len(verify.OK);"
                "verify.main();n2=len(verify.OK);print('N',n1,n2)"
                % str(tmp / "scripts"))
        r = subprocess.run([sys.executable, "-c", code], cwd=str(tmp),
                           capture_output=True, text=True, timeout=300)
        m = re.search(r"N (\d+) (\d+)", r.stdout)
        n1, n2 = (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
        t(m is not None and n2 > n1, "A3 Alt-Stand addiert Ergebnisse auf",
          f"{n1} -> {n2} ok im selben Prozess")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ Teil B
MUTANTEN = [
    ("Reset der Ergebnislisten entfernt",
     "    _reset()\n", "    pass  # _reset() entfernt\n"),
    ("Deckungs-Check der Blogseiten entschaerft",
     'check("engine: keine ungedeckte Blogseite", not uncovered,',
     'check("engine: keine ungedeckte Blogseite", True,'),
    ("Netzfehler wieder als Defekt-Claim",
     '    code, home = fetch(f"{BASE}/")\n    if code == 0:',
     '    code, home = fetch(f"{BASE}/")\n    if False:'),
    ("Leere-Keyword-Wache entfernt",
     ('    if not check("engine: Keyword-Liste nicht leer", '
      'len(te.KEYWORDS) > 0, "0 Keywords"):\n        return []\n'),
     '    check("engine: Keyword-Liste nicht leer", True)\n'),
    ("check() kann nicht mehr rot werden",
     "    (OK if cond else FAIL).append", "    (OK if True else FAIL).append"),
]


def teil_b() -> None:
    print("== B) MUTANTEN DER HEUTIGEN FASSUNG ==")
    original = VERIFY.read_bytes()
    sha_vorher = sha(VERIFY)
    rc0, _ = selftest_rc()
    t(rc0 == 0, "B0 Selftest gruen vor der Mutation", f"rc={rc0}")
    try:
        for label, alt, neu in MUTANTEN:
            src = original.decode("utf-8")
            if alt not in src:
                t(False, f"B [{label}]", "Mutationsmuster nicht gefunden")
                continue
            VERIFY.write_text(src.replace(alt, neu, 1), encoding="utf-8")
            rc, out = selftest_rc()
            rote = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL")]
            t(rc == 1 and "SELFTEST_DEFEKT" in out, f"B [{label}]",
              f"rc={rc} (soll 1), {len(rote)} Rot-Meldung(en): "
              f"{rote[0][:60] if rote else '—'}")
    finally:
        VERIFY.write_bytes(original)
    t(sha(VERIFY) == sha_vorher, "B99 sha256-genau wiederhergestellt", sha(VERIFY)[:16])
    rc1, _ = selftest_rc()
    t(rc1 == 0, "B99 Selftest nach Wiederherstellung wieder gruen", f"rc-Wechsel 0->1->{rc1}")


if __name__ == "__main__":
    teil_a()
    teil_b()
    print()
    fails = [lbl for ok, lbl in results if not ok]
    for ok, lbl in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {lbl}")
    print(f"\nMUTATIONSPROBE: {len(results) - len(fails)}/{len(results)} bestanden")
    print("ERGEBNIS: " + ("MUTATION_PROBE_OK" if not fails else "MUTATION_PROBE_DEFEKT"))
    sys.exit(1 if fails else 0)
