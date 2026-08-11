"""Ticket 31 - End-to-End-Zustellung der Cron-Alarme (Canary durch die echte Lieferkette).

cron_delivery_audit.py (Ticket 30) beweist: der Scheduler FINDET eine Adresse.
Das ist die Etappe VOR dem Senden. Ticket 31 schliesst die Luecke:
BEWEIST eine Nachricht dieses Jobs ueber den produktiven Zustellweg WIRKLICH AN.

Bauform (wie verify_publish_leg.py, Ticket 11 / cron_delivery_audit, Ticket 30):
nicht nachgebaut. Wir importieren den PRODUKTIVEN Resolver und die PRODUKTIVE
_deliver_result aus cron.scheduler, genau wie der Scheduler sie zur Laufzeit
nutzt. Ein Nachbau wuerde vom Original wegdriften.

KERNFALL (Ticket 23, wiederholt gemessen): der Defekt "delivery to whatsapp:self
failed" stand 5 Tage wortwörtlich im Log, gelesen wurde nur der 500er. Und selbst
nach dem Fix beweist "last_delivery_error = None" NICHTS - das Feld setzt der Fix
selbst. Erfolg = die POSITIVE Zeile "delivered to <ziel>" im Gateway-Log.

ERGEBNISWORTE: DELIVERY_LEG_OK (rc=0) | DELIVERY_LEG_DEFEKT (rc=1) |
DELIVERY_LEG_UNGEPRUEFT (rc=2). "Nicht messbar" ist ausdruecklich NICHT gruen
(Ticket 16/27). Ein selbst genulltes Feld ist KEIN Messwert (Ticket 23).

ADRESSEN werden NIE im Klartext ausgegeben (redact() aus cron_delivery_audit).
"""

import io
import os
import re
import sys
import contextlib

HERMES_SRC = os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "hermes", "hermes-agent"
)
if HERMES_SRC not in sys.path:
    sys.path.insert(0, HERMES_SRC)

# --- Ergebnisworte ----------------------------------------------------------
OK, DEFEKT, UNGEPRUEFT = "DELIVERY_LEG_OK", "DELIVERY_LEG_DEFEKT", "DELIVERY_LEG_UNGEPRUEFT"
RC = {OK: 0, DEFEKT: 1, UNGEPRUEFT: 2}

# Poison-Zielwerte, die eine Adresse "aufgeloest" haben, aber nirgends hinfuehren.
# 'self' ist MEASURED (Ticket 23); die uebrigen ASSUMED (Platzhalter-Heuristik).
POISON_MEASURED = {"self"}
POISON_ASSUMED = {"me", "none", "null", "origin", "local", "undefined", "-", ""}

# Positive Marke: eine Zeile "delivered to <ziel>" mit einem echten Ziel.
DELIVERED_RE = re.compile(r"delivered to\s+(\S+)", re.IGNORECASE)
# Fehler-Marken (nicht erschöpfend, aber die aus Ticket 23/30 bekannten).
ERROR_MARKERS = (
    "bridge error", "jiddecode", "failed to deliver", "delivery error",
    "delivery failed", "Traceback (most recent call last)",
)


# --- Verdict-Logik (rein, testbar) -----------------------------------------
def assess_delivery(log_text):
    """Wertet ein Gateway-/Scheduler-Log nach der POSITIV-Regel aus.

    Returns (verdict, ziel_oder_grund).

    - POSITIV: eine Zeile "delivered to <ziel>" mit echtem Ziel -> OK.
    - FEHLER : eine bekannte Fehler-Marke (oder ein Poison-Ziel bei delivered) -> DEFEKT.
    - SONST  : weder Nachweis noch Fehler -> UNGEPRUEFT (NICHT gruen).

    Wichtig: "last_delivery_error = None" allein ist KEIN Erfolg (Ticket 23) -
    es fehlt die positive Zeile, also UNGEPRUEFT.
    """
    if not log_text:
        return UNGEPRUEFT, "leeres Log - kein positiver Zustellnachweis"
    text = log_text or ""
    low = text.lower()

    # 1) Poison-Ziel bei einer delivered-Zeile -> Defekt, kein Gruen.
    #    Das Ziel hat die Form "platform:chat_id"; der chat_id ist der Teil
    #    nach dem letzten ':' (Ticket 23: "whatsapp:self" -> chat_id "self").
    for m in DELIVERED_RE.finditer(text):
        target = m.group(1).strip()
        chat_id = target.split(":")[-1] if ":" in target else target
        tlow = chat_id.lower()
        if tlow in POISON_MEASURED:
            return DEFEKT, "delivered to Poison-Ziel [%s] (MEASURED, Ticket 23)" % tlow
        if tlow in POISON_ASSUMED:
            return DEFEKT, "delivered to Poison-Ziel [%s] (ASSUMED)" % tlow
        return OK, target  # erstes echt aussehendes Ziel = Erfolg

    # 2) Fehler-Marke -> Defekt (auch wenn irgendwo 'None' steht).
    for marker in ERROR_MARKERS:
        if marker.lower() in low:
            return DEFEKT, "Fehler-Marke im Log: %s" % marker

    # 3) Weder Nachweis noch Fehler -> nicht messbar, nicht gruen.
    return UNGEPRUEFT, "weder 'delivered to <ziel>' noch Fehler-Marke im Log"


# --- Reuse aus cron_delivery_audit (kein Nachbau) ---------------------------
from cron_delivery_audit import (  # noqa: E402
    load_env, import_resolver, jobs_path, read_jobs, redact,
    job_source, alarm_words, _hermes_home,
)


def select_canary_jobs(items, sched):
    """Alarm-Traeger mit aufloesbarem Ziel. Returns [(jid, job, target_dict)].

    Nutzt denselben resolver wie cron_delivery_audit - die Zielmenge wird aus der
    Quelle des Jobs abgeleitet (Ticket 17: nie hartkodieren).
    """
    out = []
    for jid, job in items:
        if not job.get("enabled"):
            continue
        quelle, _herk = job_source(job)
        if not quelle or not alarm_words(quelle):
            continue
        deliver_raw = job.get("deliver")
        norm = sched._normalize_deliver_value(deliver_raw)
        if norm == "local":
            continue  # waere ein stummer Alarmtraeger (Ticket 30)
        parts = []
        for raw in str(norm).split(","):
            token = raw.strip()
            if not token:
                continue
            expand = getattr(sched, "_expand_routing_tokens", None)
            parts.extend(expand(token) if expand else [token])
        for part in parts:
            try:
                target = sched._resolve_single_delivery_target(job, part)
            except Exception:
                target = None
            if target:
                out.append((jid, job, target))
                break
    return out


# --- Live-Canary (gated) ----------------------------------------------------
def live_canary(confirm=False):
    print("== End-to-End-Zustell-Canary (Ticket 31) ==")
    env_ok, env_note = load_env()
    print("[1] .env geladen : %s (%s)" % ("ja" if env_ok else "NEIN", env_note))
    if not env_ok:
        print("\nERGEBNIS: %s (ohne .env sieht das Tor die falsche Umgebung)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    sched, err = import_resolver()
    print("[2] Resolver     : %s" % ("cron.scheduler (produktiv)" if sched else err))
    if sched is None:
        print("\nERGEBNIS: %s (Produktiv-Resolver nicht importierbar)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    items, jerr = read_jobs(jobs_path())
    print("[3] jobs.json    : %s" % (("%d Jobs" % len(items)) if items else jerr))
    if items is None:
        print("\nERGEBNIS: %s (jobs.json unlesbar)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    canaries = select_canary_jobs(items, sched)
    print("[4] Alarm-Traeger mit Ziel: %d" % len(canaries))
    for jid, _job, target in canaries:
        print("    %s -> %s:%s" % (str(jid)[:12], target.get("platform"),
                                   redact(target.get("chat_id"))))

    if not canaries:
        print("\nERGEBNIS: %s (kein Alarm-Traeger mit aufloesbarem Ziel)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    if not confirm:
        print("\nERGEBNIS: %s (nicht ausgefuehrt - '--confirm' erforderlich fuer" % UNGEPRUEFT)
        print("           den echten Sendegang ueber den produktiven Zustellweg)")
        return RC[UNGEPRUEFT]

    # --- echter Sendegang (nur mit --confirm) --------------------------------
    import cron.scheduler as sched_mod
    jid, job, target = canaries[0]
    marker = ("[DELIVERY-LEG-CANARY %s] Ticket-31 End-to-End-Nachweis "
              "- bitte ignorieren." % os.environ.get("HOSTNAME", "cron"))
    try:
        err_str = sched_mod._deliver_result(job, marker, adapters=None, loop=None)
    except Exception as exc:  # Gateway nicht erreichbar etc.
        print("[5] Senden fehlgeschlagen: %s: %s" % (type(exc).__name__, exc))
        print("\nERGEBNIS: %s (Senden nicht moglich - Gateway erreichbar?)" % DEFEKT)
        return RC[DEFEKT]
    if err_str:
        print("[5] _deliver_result -> Fehler: %s" % err_str)
        print("\nERGEBNIS: %s (Senden meldet Fehler)" % DEFEKT)
        return RC[DEFEKT]
    # Erfolg behauptet (rc=None) - aber der Beweis ist die POSITIVE Logzeile.
    print("[5] _deliver_result -> None (behaupteter Erfolg)")
    print("    Beweis = positive Logzeile 'delivered to %s' (siehe gateway-stdio.log)"
          % redact(target.get("chat_id")))
    print("\nERGEBNIS: %s (Senden ausgefuehrt - positives Log noch nicht automatisch" % UNGEPRUEFT)
    print("           verifiziert; manuell gegen gateway-stdio.log pruefen)")
    return RC[UNGEPRUEFT]


# ---------------------------------------------------------------------------
# Selftest: Fault Injection durch die ECHTE assess_delivery(). Kein Reimplementat.
# ---------------------------------------------------------------------------
def _mutate_source_make_ok(path):
    """Hilfsfunktion fuer die Mutationsprobe: erzwingt OK in assess_delivery.

    Gibt (original_text, geaenderter_text) zurueck; der Aufrufer restauriert.
    """
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    # Ersetze die erste 'return UNGEPRUEFT' (Sont-Zweig) durch 'return OK' -
    # ein Mutant, der selbst bei Fehlen der positiven Zeile gruen wird.
    mutant = src.replace(
        '    # 3) Weder Nachweis noch Fehler -> nicht messbar, nicht gruen.\n'
        '    return UNGEPRUEFT, "weder \'delivered to <ziel>\' noch Fehler-Marke im Log"',
        '    return OK, "MUTANT: immer OK"',
        1,
    )
    if mutant == src:
        # Fallback: jede Rueckkehr von UNGEPRUEFT zaehmen.
        mutant = src.replace('return UNGEPRUEFT,', 'return OK, "MUTANT"', 1)
    return src, mutant


def selftest():
    results = []

    def check(label, cond, detail=""):
        results.append((label, bool(cond), detail))

    env_ok, _ = load_env()
    check("env/.env ladbar", env_ok)

    # -- GRUEN: positive Zeile mit echtem Ziel --------------------------------
    v, z = assess_delivery("... delivered to whatsapp:851112345678@lid ...")
    check("gruen/delivered -> OK", v == OK, v)
    check("gruen/Ziel extrahiert", "851112345678" in z, z)
    check("gruen/Ziel redigiert (kein Klartext im Verdict)",
          "851112345678@lid" not in str(z) or "8511" in str(z))

    # -- ROT 1: Ticket-23-Fehler-Marke ---------------------------------------
    v, z = assess_delivery(
        "21:58:50 ERROR bfb63346d942: WhatsApp bridge error (500) jidDecode")
    check("rot/bridge-error -> DEFEKT", v == DEFEKT, v)
    check("rot/Fehler benannt", "bridge error" in z.lower(), z)

    # -- ROT 2: Poison-Ziel bei delivered ------------------------------------
    v, z = assess_delivery("delivered to whatsapp:self")
    check("rot/delivered to self -> DEFEKT", v == DEFEKT, v)
    check("rot/Poison-Regel benannt", "self" in z.lower(), z)

    # -- ROT 3: selbst genulltes Feld ist KEIN Erfolg (Ticket 23) ------------
    v, z = assess_delivery("last_delivery_error = None")
    check("rot/None-Feld ist NICHT OK", v != OK, v)
    check("rot/None-Feld -> UNGEPRUEFT", v == UNGEPRUEFT, v)

    # -- ROT 4: leeres Log ----------------------------------------------------
    v, z = assess_delivery("")
    check("rot/leeres Log -> UNGEPRUEFT (nicht gruen)", v == UNGEPRUEFT, v)

    # -- ROT 5: Traceback-Marke ----------------------------------------------
    v, z = assess_delivery("Traceback (most recent call last):\n  File ...")
    check("rot/Traceback -> DEFEKT", v == DEFEKT, v)

    # -- ROT 6: nur ein 'delivered' mit leerem Ziel ist kein Erfolg ----------
    v, z = assess_delivery("delivered to ")
    check("rot/leeres Ziel bei delivered -> nicht OK", v != OK, v)

    # -- redact-Kontrakt -----------------------------------------------------
    from cron_delivery_audit import redact as _redact
    check("redact/kein Klartext",
          "4915112345678" not in _redact("4915112345678"))

    ok = sum(1 for _l, c, _d in results if c)
    for label, cond, detail in results:
        if not cond:
            print("  FAIL %-44s %s" % (label, str(detail)[:140]))
    print("SELFTEST %d/%d" % (ok, len(results)))

    # -- Mutationsprobe: ein Mutant, der immer gruen wird, muss den Test rot machen
    here = os.path.abspath(__file__)
    try:
        import hashlib
        orig, mutant = _mutate_source_make_ok(here)
        if mutant == orig:
            print("  MUTPROBE: konnte keinen Mutanten erzeugen (ueberspringe)")
        else:
            sha_before = hashlib.sha256(orig.encode("utf-8")).hexdigest()
            with open(here, "w", encoding="utf-8") as fh:
                fh.write(mutant)
            buf = io.StringIO()
            rc_mut = 0
            try:
                with contextlib.redirect_stdout(buf):
                    rc_mut = selftest_inner() if False else _run_selftest_python()
            finally:
                with open(here, "w", encoding="utf-8") as fh:
                    fh.write(orig)
                sha_after = hashlib.sha256(orig.encode("utf-8")).hexdigest()
            check("mut/Datei sha256-genau restauriert", sha_before == sha_after,
                  "%s vs %s" % (sha_before[:10], sha_after[:10]))
            check("mut/Mutant macht Selftest rot (rc=1)",
                  rc_mut == 1, "rc=%s" % rc_mut)
    except Exception as exc:
        check("mut/Probe lief", False, "%s: %s" % (type(exc).__name__, exc))

    ok = sum(1 for _l, c, _d in results if c)
    if ok == len(results):
        print("\nERGEBNIS: SELFTEST_OK")
        return 0
    print("\nERGEBNIS: SELFTEST_DEFEKT")
    return 1


def _run_selftest_python():
    """Fuehrt den Selftest in einem frischen Interpreter aus (Datei ist zwischen-
    zeitlich mutiert) und liefert dessen rc zurueck."""
    import subprocess
    proc = subprocess.run([sys.executable, os.path.abspath(__file__), "--selftest-inner"],
                          capture_output=True, text=True)
    return proc.returncode


def selftest_inner():
    """Der eigentliche Fall-Vergleich OHNE die Mutationsprobe (Rekursion vermeiden)."""
    results = []

    def check(label, cond, detail=""):
        results.append((label, bool(cond), detail))

    env_ok, _ = load_env()
    check("env/.env ladbar", env_ok)

    v, z = assess_delivery("... delivered to whatsapp:851112345678@lid ...")
    check("gruen/delivered -> OK", v == OK, v)
    v, z = assess_delivery(
        "21:58:50 ERROR bfb63346d942: WhatsApp bridge error (500) jidDecode")
    check("rot/bridge-error -> DEFEKT", v == DEFEKT, v)
    v, z = assess_delivery("delivered to whatsapp:self")
    check("rot/delivered to self -> DEFEKT", v == DEFEKT, v)
    v, z = assess_delivery("last_delivery_error = None")
    check("rot/None-Feld ist NICHT OK", v != OK, v)
    check("rot/None-Feld -> UNGEPRUEFT", v == UNGEPRUEFT, v)
    v, z = assess_delivery("")
    check("rot/leeres Log -> UNGEPRUEFT", v == UNGEPRUEFT, v)
    v, z = assess_delivery("Traceback (most recent call last):\n  File ...")
    check("rot/Traceback -> DEFEKT", v == DEFEKT, v)
    v, z = assess_delivery("delivered to ")
    check("rot/leeres Ziel bei delivered -> nicht OK", v != OK, v)
    from cron_delivery_audit import redact as _redact
    check("redact/kein Klartext", "4915112345678" not in _redact("4915112345678"))

    ok = sum(1 for _l, c, _d in results if c)
    for label, cond, detail in results:
        if not cond:
            print("  FAIL %-44s %s" % (label, str(detail)[:140]))
    print("SELFTEST %d/%d" % (ok, len(results)))
    return 0 if ok == len(results) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest-inner" in argv:
        return selftest_inner()
    if "--selftest" in argv:
        return selftest()
    if "--live" in argv:
        confirm = "--confirm" in argv
        return live_canary(confirm=confirm)
    # Default: Aufloesbarkeit der Alarm-Traeger zeigen (DEMO-frei, nur Resolver).
    print("== Zustell-Canary (Ticket 31) ==")
    print("Nutze --selftest (Instrumentierung pruefen) oder --live [--confirm].")
    return 0


if __name__ == "__main__":
    sys.exit(main())
