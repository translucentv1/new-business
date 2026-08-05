#!/usr/bin/env python3
"""Mutationsprobe fuer Ticket 19 (indexnow_submit.py).

Zwei Beweisrichtungen (Konvention Ticket 16-18):

A) ALT-STAND-PROBE — nicht argumentiert, sondern AUSGEFUEHRT.
   HEAD:scripts/indexnow_submit.py wird in eine Sandbox gelegt und mit genau den
   Defekten konfrontiert, die der neue Selftest abdeckt. Wo der Alt-Stand gruen
   bleibt oder einen falschen Vorwurf erhebt, war er blind.

B) MUTANTEN DER HEUTIGEN FASSUNG — der Selftest muss rot werden, wenn man den
   PRODUKTIVCODE kaputtmacht. Mutiert wird die Datei auf der Platte; danach
   sha256-genaue Wiederherstellung und rc-Wechsel 0 -> 1 -> 0.

Es geht in keinem Fall ein Byte ins Netz (http() ist immer ersetzt).
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "scripts" / "indexnow_submit.py"
sys.path.insert(0, str(ROOT / "scripts"))

from _indexnow_selftest import (
    NET_ERROR,
    load_module,
    run_case,
    sitemap_xml,
)

results: list[tuple[bool, str]] = []


def t(cond, label, detail=""):
    results.append((bool(cond), label + (" — " + detail if detail else "")))
    return bool(cond)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def erg(out):
    for ln in out.splitlines():
        if ln.startswith("ERGEBNIS:"):
            return ln.strip()
    return "(kein ERGEBNIS-Wort)"


def selftest_rc():
    r = subprocess.run([sys.executable, str(TARGET), "--selftest"], cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------- A) Alt-Stand
def alt_stand_probe():
    r = subprocess.run(["git", "show", "HEAD:scripts/indexnow_submit.py"], cwd=ROOT,
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("git show fehlgeschlagen: " + r.stderr[:200])
    alt = Path(tempfile.mkdtemp(prefix="t19_alt_")) / "indexnow_submit.py"
    alt.write_text(r.stdout, encoding="utf-8")
    mod = load_module(str(alt), "alt_indexnow_t19")
    B = mod.BASE
    print("== A) ALT-STAND-PROBE (HEAD:scripts/indexnow_submit.py) ==")

    # A1: lokale URL existiert live nicht -> Alt-Stand reicht eine 404-URL ein
    rc, out, fake = run_case(mod, local_urls=[B + "gibtesnichtlive.html"],
                             submit_codes=[200])
    print("   A1 lokal-nicht-live : rc=%s %s" % (rc, erg(out)))
    t(rc == 0 and "SUBMIT_OK" in erg(out) and len(fake.submitted_urls) == 1,
      "A1 Alt-Stand reicht eine live nicht existierende URL ein -> war BLIND",
      "rc=%s %s" % (rc, erg(out)))

    # A2: lokale Sitemap auf 1 URL geschrumpft (live haette 3) -> gruen
    rc, out, fake = run_case(mod, local_urls=[B + "a.html"], submit_codes=[200])
    print("   A2 stille Schrumpfung: rc=%s %s" % (rc, erg(out)))
    t(rc == 0 and "SUBMIT_OK" in erg(out),
      "A2 Alt-Stand meldet gruen, obwohl nur 1 statt 3 URLs eingereicht wurden "
      "-> war BLIND", "rc=%s" % rc)

    # A3: Netz tot -> Defekt-Vorwurf gegen die eigene (gesunde) Key-Datei
    rc, out, fake = run_case(mod, key=(NET_ERROR, "URLError(gaierror)"),
                             local_urls=[B + "a.html"])
    print("   A3 Netz tot          : rc=%s %s" % (rc, erg(out)))
    t(rc == 1 and "KEY_NICHT_LIVE" in erg(out),
      "A3 Alt-Stand erhebt bei totem Netz einen Defekt-Vorwurf gegen die "
      "Key-Datei", "rc=%s %s" % (rc, erg(out)))

    # A4: 500 wird von 403 maskiert
    rc, out, fake = run_case(mod, local_urls=[B + "a.html", B + "b.html"],
                             submit_codes=[500, 403], batch=1)
    print("   A4 500 hinter 403    : rc=%s %s" % (rc, erg(out)))
    t("SUBMIT_403" in erg(out),
      "A4 Alt-Stand maskiert einen echten 500er als 'kein URL-Fehler'",
      erg(out))

    # A5: Netzfehler beim Senden -> Defekt-Vorwurf statt 'unmessbar'
    rc, out, fake = run_case(mod, local_urls=[B + "a.html"],
                             submit_codes=[NET_ERROR])
    print("   A5 Netz beim Senden  : rc=%s %s" % (rc, erg(out)))
    t(rc == 1 and "SUBMIT_FEHLER" in erg(out),
      "A5 Alt-Stand liest Netzausfall beim Senden als Einreichungsfehler",
      erg(out))

    # Gegenprobe: die NEUE Fassung faellt auf keinen dieser Faelle herein
    neu = load_module(str(TARGET), "neu_indexnow_t19")
    B = neu.BASE
    live3 = (200, sitemap_xml([B + "a.html", B + "b.html", B + "c.html"]))
    print("== A') GEGENPROBE mit der heutigen Fassung ==")
    for label, kw, erwartet, erw_rc in [
        ("A1", dict(local_urls=[B + "gibtesnichtlive.html"],
                    live_sitemap=(200, sitemap_xml([B + "a.html"])),
                    submit_codes=[200]), "INDEXNOW_DRIFT", 1),
        ("A2", dict(local_urls=[B + "a.html"], live_sitemap=live3,
                    submit_codes=[200]), "INDEXNOW_DRIFT", 1),
        ("A3", dict(key=(NET_ERROR, "URLError"), local_urls=[B + "a.html"]),
         "INDEXNOW_UNGEPRUEFT", 2),
        ("A4", dict(local_urls=[B + "a.html", B + "b.html", B + "c.html"],
                    live_sitemap=live3, submit_codes=[500, 403, 403], batch=1),
         "SUBMIT_FEHLER", 1),
        ("A5", dict(local_urls=[B + "a.html"],
                    live_sitemap=(200, sitemap_xml([B + "a.html"])),
                    submit_codes=[NET_ERROR]), "INDEXNOW_UNGEPRUEFT", 2),
    ]:
        rc, out, fake = run_case(neu, **kw)
        print("   %s neu: rc=%s %s" % (label, rc, erg(out)))
        t(erwartet in erg(out) and rc == erw_rc,
          "%s neue Fassung -> %s (rc=%s)" % (label, erwartet, erw_rc),
          "gemessen rc=%s %s" % (rc, erg(out)))
        if label in ("A1", "A2"):
            t(len(fake.submits) == 0,
              "%s neue Fassung reicht bei Drift NICHTS ein" % label,
              "gemessen %d Einreichungen" % len(fake.submits))


# ------------------------------------------------------------------ B) Mutanten
MUTANTEN = [
    ("M1 Drift-Pruefung entfernt",
     "    if nur_lokal or nur_live:",
     "    if False:"),
    ("M2 Netzfehler zaehlt als Erfolg",
     '    hart = [c for c in codes if c not in (200, 202, 403, NET)]',
     '    hart = [c for c in codes if c not in (200, 202, 403, NET, 500, 429)]'),
    ("M3 403 maskiert wieder alles",
     "    if hart:\n        return \"SUBMIT_FEHLER codes=%s\" % (codes,), RC_DEFEKT",
     "    if 403 in codes:\n        return \"SUBMIT_403_KEY_NOCH_NICHT_GECRAWLT codes=%s\" % (codes,), RC_403\n    if hart:\n        return \"SUBMIT_FEHLER codes=%s\" % (codes,), RC_DEFEKT"),
    ("M4 leere Code-Liste ist gruen",
     '    if not codes:  # Leere-Schleife-Falle (Ticket 16): nichts gesendet ist nicht gruen\n        return "SUBMIT_FEHLER kein einziger Batch gesendet codes=[]", RC_DEFEKT',
     '    if not codes:\n        return "SUBMIT_OK codes=[]", RC_OK'),
    ("M5 Netzausfall am Key wieder als Defekt",
     '    if zustand == "unmessbar":\n        print("ERGEBNIS: INDEXNOW_UNGEPRUEFT - Netz/DNS nicht erreichbar, "\n              "keine Aussage ueber die Key-Datei.")\n        return RC_UNGEPRUEFT',
     '    if zustand == "unmessbar":\n        zustand = "falsch"'),
    ("M6 Scope-Filter aus (/dl/ und Fremdhost)",
     '    scoped = [u for u in urls if u.startswith(BASE) and "/dl/" not in u]',
     '    scoped = list(urls)'),
    # M7 stellt exakt den Defekt wieder her, der am 2026-08-05 im ECHTEN Lauf
    # zuschlug: gekuerzte Live-Sitemap -> falscher Drift-Alarm (3 statt 1220).
    ("M7 Live-Sitemap wieder gekuerzt lesen",
     "    status, body = http(LIVE_SITEMAP_URL, maxlen=None)",
     "    status, body = http(LIVE_SITEMAP_URL)"),
]


def mutanten_probe():
    print("== B) MUTANTEN DER HEUTIGEN FASSUNG ==")
    original = TARGET.read_bytes()
    sha_vorher = sha(TARGET)
    rc0, _ = selftest_rc()
    t(rc0 == 0, "Selftest vor der Mutation gruen", "rc=%s" % rc0)
    try:
        for label, alt, neu in MUTANTEN:
            text = original.decode("utf-8")
            if alt not in text:
                t(False, "%s: Ankertext nicht gefunden (Mutation nicht angewandt)"
                  % label)
                continue
            TARGET.write_text(text.replace(alt, neu, 1), encoding="utf-8")
            rc, out = selftest_rc()
            rot = rc != 0 and "SELFTEST_ROT" in out
            kein_tb = "Traceback" not in out
            print("   %-42s rc=%s rot=%s" % (label, rc, rot))
            t(rot, "%s -> Selftest wird ROT" % label, "rc=%s" % rc)
            t(kein_tb, "%s -> rot durch Assertion, nicht durch Absturz" % label)
    finally:
        TARGET.write_bytes(original)
    sha_nachher = sha(TARGET)
    t(sha_vorher == sha_nachher, "Produktivdatei sha256-genau wiederhergestellt",
      sha_nachher[:16])
    rc1, _ = selftest_rc()
    t(rc1 == 0, "Selftest nach Wiederherstellung wieder gruen", "rc=%s" % rc1)
    print("   rc-Wechsel: 0 -> 1 -> %s" % rc1)


def main():
    alt_stand_probe()
    mutanten_probe()
    ok = sum(1 for c, _ in results if c)
    print()
    for cond, label in results:
        if not cond:
            print("  ROT: %s" % label)
    print("%d/%d Proben bestanden" % (ok, len(results)))
    if ok == len(results):
        print("ERGEBNIS: MUTATION_PROBE_OK")
        return 0
    print("ERGEBNIS: MUTATION_PROBE_ROT")
    return 1


if __name__ == "__main__":
    sys.exit(main())
