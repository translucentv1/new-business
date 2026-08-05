#!/usr/bin/env python3
"""Selftest-Faelle fuer indexnow_submit.py (Ticket 19).

Alle Faelle laufen durch die ECHTE main() einer frisch geladenen Kopie des
Produktivcodes; injiziert werden nur HTTP-Antworten und die lokale sitemap.xml.
Es geht KEIN Byte ins Netz und es wird NIE eine echte Einreichung ausgeloest
(der Selftest prueft das sogar: kein Fall darf gegen den echten Endpoint gehen).

Rot-Faelle werden gegen die EXAKTE Diagnosezeile assertiert (Lehre aus Ticket 17)
und zusaetzlich auf 'Traceback' gefiltert (Exit-Code-Falle aus Ticket 14).
"""
from __future__ import annotations

import sys

from _indexnow_selftest import NET_ERROR, load_module, run_case, sitemap_xml

_results: list[tuple[bool, str]] = []


def t(cond, label, detail=""):
    # detail defensiv nach str: eine Harness, die an ihrem eigenen
    # Detail-Argument abstuerzt, macht aus einem Rot-Fall einen Traceback.
    detail = "" if detail == "" else str(detail)
    _results.append((bool(cond), label + (" — " + detail if detail else "")))
    return bool(cond)


def _erg(out):
    for ln in out.splitlines():
        if ln.startswith("ERGEBNIS:"):
            return ln.strip()
    return "(kein ERGEBNIS-Wort)"


def _wort(out):
    """Nur das Ergebniswort selbst — exakter Vergleich statt Substring.

    Ticket 17: gegen die EXAKTE Diagnosezeile assertieren. 'SUBMIT_OK' ist
    Substring von 'SUBMIT_OK_TEILMENGE'; ein Substring-Test haette einen
    stillen Wechsel zwischen beiden nie bemerkt.
    """
    ln = _erg(out)
    if not ln.startswith("ERGEBNIS:"):
        return "(kein ERGEBNIS-Wort)"
    rest = ln[len("ERGEBNIS:"):].strip()
    return rest.split()[0] if rest else "(leer)"


def case(mod, label, *, erwartet_wort, erwartet_rc, erwartet_submits=None, **kw):
    rc, out, fake = run_case(mod, **kw)
    ok_wort = _wort(out) == erwartet_wort
    ok_rc = rc == erwartet_rc
    ok_tb = "Traceback" not in out
    ok_sub = (erwartet_submits is None or len(fake.submits) == erwartet_submits)
    t(ok_wort, label + " -> " + erwartet_wort, _erg(out))
    t(ok_rc, label + " -> rc=%s" % erwartet_rc, "gemessen rc=%s" % rc)
    t(ok_tb, label + " -> kein Traceback")
    if erwartet_submits is not None:
        t(ok_sub, label + " -> %s Einreichung(en)" % erwartet_submits,
          "gemessen %d" % len(fake.submits))
    return rc, out, fake


def run_selftest(modul_pfad):
    mod = load_module(modul_pfad, "indexnow_unter_test")
    B = mod.BASE
    gesund = [B + "a.html", B + "b.html"]
    live_gesund = (200, sitemap_xml(gesund))

    print("== indexnow_submit.py --selftest (Fault Injection, kein Netz) ==")

    # --- GRUEN: der Normalfall muss gruen sein UND wirklich einreichen ---------
    rc, out, fake = case(mod, "[gruen] alles gesund", erwartet_wort="SUBMIT_OK",
                         erwartet_rc=0, erwartet_submits=1,
                         local_urls=gesund, live_sitemap=live_gesund,
                         submit_codes=[200])
    t(sorted(fake.submitted_urls) == sorted(gesund),
      "[gruen] genau die Sitemap-URLs eingereicht",
      "gemessen %s" % fake.submitted_urls)
    t("vollzaehlig=ja" in out, "[gruen] Geltungsbereich gedruckt (vollzaehlig=ja)")
    case(mod, "[gruen] HTTP 202", erwartet_wort="SUBMIT_OK", erwartet_rc=0,
         local_urls=gesund, live_sitemap=live_gesund, submit_codes=[202])

    # --- KEY -------------------------------------------------------------------
    case(mod, "[rot] Key-Datei 404", erwartet_wort="KEY_NICHT_LIVE", erwartet_rc=1,
         erwartet_submits=0, key=(404, "not found"), local_urls=gesund)
    case(mod, "[rot] Key 200, falscher Body", erwartet_wort="KEY_NICHT_LIVE",
         erwartet_rc=1, erwartet_submits=0, key=(200, "falscherkey"),
         local_urls=gesund)
    case(mod, "[ungeprueft] Netz/DNS tot beim Key",
         erwartet_wort="INDEXNOW_UNGEPRUEFT", erwartet_rc=2, erwartet_submits=0,
         key=(NET_ERROR, "URLError(gaierror)"), local_urls=gesund)

    # --- SITEMAP-QUELLE --------------------------------------------------------
    case(mod, "[rot] leere lokale Sitemap", erwartet_wort="KEINE_URLS",
         erwartet_rc=1, erwartet_submits=0, local_urls=[], live_sitemap=live_gesund)
    case(mod, "[rot] lokale Sitemap fehlt", erwartet_wort="KEINE_URLS",
         erwartet_rc=1, erwartet_submits=0, local_sitemap_missing=True,
         live_sitemap=live_gesund)
    case(mod, "[ungeprueft] LIVE-Sitemap nicht abrufbar",
         erwartet_wort="INDEXNOW_UNGEPRUEFT", erwartet_rc=2, erwartet_submits=0,
         local_urls=gesund, live_sitemap=(NET_ERROR, "URLError"))

    # --- GELTUNGSBEREICH / DRIFT (Ticket 18) ------------------------------------
    case(mod, "[rot] URL lokal aber live 404", erwartet_wort="INDEXNOW_DRIFT",
         erwartet_rc=1, erwartet_submits=0,
         local_urls=gesund + [B + "unveroeffentlicht.html"],
         live_sitemap=live_gesund, submit_codes=[200])
    case(mod, "[rot] stille Schrumpfung (live hat mehr)",
         erwartet_wort="INDEXNOW_DRIFT", erwartet_rc=1, erwartet_submits=0,
         local_urls=[B + "a.html"], live_sitemap=live_gesund, submit_codes=[200])
    rc, out, fake = case(mod, "[gruen] --allow-drift reicht Schnittmenge ein",
                         erwartet_wort="SUBMIT_OK_TEILMENGE", erwartet_rc=0,
                         erwartet_submits=1, argv=["--allow-drift"],
                         local_urls=gesund + [B + "unveroeffentlicht.html"],
                         live_sitemap=live_gesund, submit_codes=[200])
    t(sorted(fake.submitted_urls) == sorted(gesund),
      "[allow-drift] die 404-URL wurde NICHT eingereicht",
      "gemessen %s" % fake.submitted_urls)

    # --- SUBMIT-CODES ----------------------------------------------------------
    case(mod, "[rot] Submit 500", erwartet_wort="SUBMIT_FEHLER", erwartet_rc=1,
         local_urls=gesund, live_sitemap=live_gesund, submit_codes=[500])
    case(mod, "[rot] Submit 429", erwartet_wort="SUBMIT_FEHLER", erwartet_rc=1,
         local_urls=gesund, live_sitemap=live_gesund, submit_codes=[429])
    case(mod, "[rot] Submit 422 (Scope/Key falsch)", erwartet_wort="SUBMIT_FEHLER",
         erwartet_rc=1, local_urls=gesund, live_sitemap=live_gesund,
         submit_codes=[422])
    case(mod, "[403] Key noch nicht gecrawlt",
         erwartet_wort="SUBMIT_403_KEY_NOCH_NICHT_GECRAWLT", erwartet_rc=3,
         local_urls=gesund, live_sitemap=live_gesund, submit_codes=[403])
    case(mod, "[ungeprueft] Netz tot beim Senden",
         erwartet_wort="INDEXNOW_UNGEPRUEFT", erwartet_rc=2,
         local_urls=gesund, live_sitemap=live_gesund, submit_codes=[NET_ERROR])

    # --- MEHRERE BATCHES (die all()-Hypothese aus Ticket 19) --------------------
    drei = [B + "a.html", B + "b.html", B + "c.html"]
    live_drei = (200, sitemap_xml(drei))
    case(mod, "[rot] gemischte Batches 200+500", erwartet_wort="SUBMIT_FEHLER",
         erwartet_rc=1, erwartet_submits=3, batch=1,
         local_urls=drei, live_sitemap=live_drei, submit_codes=[200, 500, 200])
    case(mod, "[rot] 500 darf nicht von 403 maskiert werden",
         erwartet_wort="SUBMIT_FEHLER", erwartet_rc=1, batch=1,
         local_urls=drei, live_sitemap=live_drei, submit_codes=[500, 403, 403])
    case(mod, "[ungeprueft] Netzfehler in einem Batch",
         erwartet_wort="INDEXNOW_UNGEPRUEFT", erwartet_rc=2, batch=1,
         local_urls=drei, live_sitemap=live_drei,
         submit_codes=[200, NET_ERROR, 200])
    case(mod, "[403] 200+403 gemischt bleibt 403-Wort",
         erwartet_wort="SUBMIT_403_KEY_NOCH_NICHT_GECRAWLT", erwartet_rc=3,
         batch=1, local_urls=drei, live_sitemap=live_drei,
         submit_codes=[200, 403, 200])
    rc, out, fake = case(mod, "[gruen] 3 Batches alle 200", erwartet_wort="SUBMIT_OK",
                         erwartet_rc=0, erwartet_submits=3, batch=1,
                         local_urls=drei, live_sitemap=live_drei,
                         submit_codes=[200, 200, 200])
    t(sorted(fake.submitted_urls) == sorted(drei),
      "[gruen] alle 3 URLs ueber 3 Batches eingereicht",
      "gemessen %d" % len(fake.submitted_urls))

    # --- LEERE SCHLEIFE / _bewerte direkt --------------------------------------
    wort, rc_leer = mod._bewerte([])
    t("SUBMIT_FEHLER" in wort and rc_leer == 1,
      "[rot] leere Code-Liste ist NICHT gruen", "%s rc=%s" % (wort, rc_leer))

    # --- GROSSE LIVE-SITEMAP (real gemessener Defekt vom 2026-08-05) -----------
    # http() kuerzt Bodies auf 400 Zeichen. Bei 60 URLs (> 4 kB) kaemen ohne
    # maxlen=None nur die ersten ~3 <loc> an -> falscher INDEXNOW_DRIFT-Alarm
    # gegen eine kerngesunde Site. Die Attrappe kuerzt genauso wie das Original.
    viele = [B + "seite-%03d.html" % i for i in range(60)]
    rc, out, fake = case(mod, "[gruen] 60-URL-Sitemap wird ungekuerzt gelesen",
                         erwartet_wort="SUBMIT_OK", erwartet_rc=0,
                         erwartet_submits=1, local_urls=viele,
                         live_sitemap=(200, sitemap_xml(viele)),
                         submit_codes=[200])
    t(len(fake.submitted_urls) == 60,
      "[gruen] alle 60 URLs eingereicht (keine Body-Kuerzung)",
      "gemessen %d" % len(fake.submitted_urls))
    t("live : 60 URLs im Scope" in out,
      "[gruen] LIVE-Sitemap vollstaendig geparst",
      [ln for ln in out.splitlines() if "live :" in ln])

    # --- SCOPE-FILTER -----------------------------------------------------------
    rc, out, fake = case(mod, "[gruen] Fremdhost und /dl/ werden verworfen",
                         erwartet_wort="SUBMIT_OK", erwartet_rc=0,
                         local_urls=gesund + ["https://example.com/x.html",
                                              B + "dl/rtd/geheim.html"],
                         live_sitemap=(200, sitemap_xml(
                             gesund + ["https://example.com/x.html",
                                       B + "dl/rtd/geheim.html"])),
                         submit_codes=[200])
    t(sorted(fake.submitted_urls) == sorted(gesund),
      "[scope] weder Fremdhost noch /dl/ eingereicht",
      "gemessen %s" % fake.submitted_urls)

    # --- --limit / --check ------------------------------------------------------
    rc, out, fake = case(mod, "[gruen] --limit 1 reicht genau 1 URL ein",
                         erwartet_wort="SUBMIT_OK_TEILMENGE", erwartet_rc=0,
                         argv=["--limit", "1"], local_urls=gesund,
                         live_sitemap=live_gesund, submit_codes=[200])
    t(len(fake.submitted_urls) == 1, "[limit] genau 1 URL im Payload",
      "gemessen %d" % len(fake.submitted_urls))
    case(mod, "[gruen] --check bei gesundem Key", erwartet_wort="KEY_LIVE",
         erwartet_rc=0, erwartet_submits=0, argv=["--check"], local_urls=gesund)
    case(mod, "[rot] --check bei 404-Key", erwartet_wort="KEY_NICHT_LIVE",
         erwartet_rc=1, erwartet_submits=0, argv=["--check"], key=(404, "nope"),
         local_urls=gesund)
    case(mod, "[ungeprueft] --check bei totem Netz",
         erwartet_wort="INDEXNOW_UNGEPRUEFT", erwartet_rc=2, erwartet_submits=0,
         argv=["--check"], key=(NET_ERROR, "URLError"), local_urls=gesund)

    ok = sum(1 for c, _ in _results if c)
    for cond, label in _results:
        if not cond:
            print("  ROT: %s" % label)
    print("%d/%d Checks bestanden" % (ok, len(_results)))
    if ok == len(_results):
        print("ERGEBNIS: SELFTEST_OK")
        return 0
    print("ERGEBNIS: SELFTEST_ROT")
    return 1


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(run_selftest(os.path.join(here, "indexnow_submit.py")))
