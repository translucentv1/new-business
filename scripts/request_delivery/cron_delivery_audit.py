"""Ticket 30 - Steht der MELDEWEG der Cron-Jobs? (stehendes Tor, kein Ad-hoc-Skript)

Ticket 23 hat einen ZUSTAND repariert (4 Jobs mit deliver='origin' + origin=None),
nicht die EIGENSCHAFT. Dieses Tor prueft die Eigenschaft: kommt der Bericht eines
Jobs beim Betreiber AN? Der Defekt macht keinen Job 'failed' -- er ist fuer
cron_health_audit (prueft, ob der Geldpfad LAEUFT) unsichtbar.

GRUNDSATZ (Ticket 16/17): die Regel wird NICHT nachgebaut. Das Tor importiert den
PRODUKTIVEN Resolver `cron.scheduler._resolve_single_delivery_target` und fragt
ihn, was er ausliefern wuerde. Ein Nachbau wuerde vom Original wegdriften und
genau dann gruen bleiben, wenn Hermes seine Routing-Regeln aendert.

GRUNDSATZ 2 ("Check where you are before you measure"): der Resolver liest die
Home-Channel-Fallbacks zur LAUFZEIT aus os.environ. Der Scheduler laeuft im
Gateway-Prozess MIT geladener .env. Ein Audit ohne .env saehe eine voellig andere
Umgebung und wuerde die falsche Diagnose stellen -- deshalb wird dieselbe
.env ueber `hermes_cli.env_loader.load_hermes_dotenv` geladen.

Ergebnisworte: DELIVERY_OK (rc=0) | DELIVERY_DEFEKT (rc=1) | DELIVERY_UNGEPRUEFT (rc=2)
"Nicht messbar" ist ausdruecklich NICHT gruen (Ticket 16/27).

Adressen werden NIE ausgegeben (nur Praefix + Laenge) -- kein Credential im Log.
"""

import json
import os
import sys

HERMES_SRC = os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "hermes", "hermes-agent"
)

# --- Ergebnisworte -----------------------------------------------------------
OK, DEFEKT, UNGEPRUEFT = "DELIVERY_OK", "DELIVERY_DEFEKT", "DELIVERY_UNGEPRUEFT"

# Nicht adressierbare Platzhalter-Werte.
# 'self' ist MEASURED (Ticket 23, logs/gateway-stdio.log, diesen Tick erneut
# nachgelesen): "delivery to whatsapp:self failed: Cannot destructure property
# 'user' of 'jidDecode(...)' as it is undefined" -> HTTP 500.
# Die uebrigen Werte sind ASSUMED (Platzhalter-Heuristik), deshalb nennt die
# Diagnosezeile immer, WELCHE Regel gefeuert hat.
POISON_MEASURED = {"self"}
POISON_ASSUMED = {"me", "none", "null", "origin", "local", "undefined", "-"}

# --- Alarmtraeger ------------------------------------------------------------
# deliver='local' ist NICHT per se ein Defekt - ein Job darf bewusst nur auf
# Platte schreiben. Ein Intent-Satz ("meldet bewusst nur auf Platte") war aber
# eine BEHAUPTUNG statt eines Messwerts (Merkregel Ticket 16). Messbar ist die
# Frage: kann dieser Job ueberhaupt etwas sagen, das jemanden erreichen MUSS?
#
# MEASURED (cron/scheduler.py:1456-1460, diesen Tick gelesen):
#   targets = _resolve_delivery_targets(job)
#   if not targets:
#       if deliver_value == "local":
#           return None  # local-only jobs don't deliver - not a failure
# => Bei deliver='local' wird JEDE Ausgabe verworfen, auch der Fehler-Alert
#    eines nicht-null Exitcodes. Ein Alarm dieses Jobs erreicht per
#    KONSTRUKTION niemanden.
#
# Die Zielmenge wird aus der QUELLE DES JOBS abgeleitet (Merkregel Ticket 17:
# nie hartkodieren): no_agent-Jobs -> ihre Skriptdatei, Agent-Jobs -> ihr
# prompt. Ein neuer Alarm-Job wird damit automatisch mitgeprueft.
ALARM_TOKENS = ("ERSTER SALE", "DEFEKT", "ALARM", "*** ")


def _hermes_home():
    return os.environ.get("HERMES_HOME") or os.path.join(
        os.path.expanduser("~"), "AppData", "Local", "hermes")


def job_source(job):
    """Quelle des Jobs lesen. -> (text, herkunft).

    Skriptdatei fuer no_agent-Jobs (so wie der Scheduler sie aufloest:
    relativ zu HERMES_HOME/scripts, absolute Pfade direkt), sonst der prompt.
    Ist die Skriptdatei unlesbar, wird das GESAGT statt stillschweigend auf
    den prompt auszuweichen - sonst entstuende ein Falsch-Gruen.
    """
    script = (job.get("script") or "").strip()
    if script:
        cand = script if os.path.isabs(script) else os.path.join(
            _hermes_home(), "scripts", script)
        try:
            with open(cand, encoding="utf-8", errors="replace") as fh:
                return fh.read(), "script:%s" % os.path.basename(cand)
        except OSError as exc:
            return None, "script:%s unlesbar (%s)" % (
                os.path.basename(cand), type(exc).__name__)
    return (job.get("prompt") or ""), "prompt"


def alarm_words(text):
    """Welche Alarmworte stehen in der Quelle? -> sortierte Liste."""
    if not text:
        return []
    return sorted({t.strip() or t for t in ALARM_TOKENS if t in text})


def redact(value):
    """Adresse zu '<len=N pre=XXXX>' kuerzen - nie den vollen Wert ausgeben."""
    s = str(value)
    return "<len=%d pre=%s>" % (len(s), s[:4])


def load_env():
    """Dieselbe .env laden, die der Scheduler im Gateway sieht.

    Returns (ok: bool, hinweis: str).
    """
    if HERMES_SRC not in sys.path:
        sys.path.insert(0, HERMES_SRC)
    try:
        from hermes_cli.env_loader import load_hermes_dotenv

        load_hermes_dotenv()
        return True, "hermes_cli.env_loader.load_hermes_dotenv()"
    except Exception as exc:  # pragma: no cover - Umgebungsfehler
        return False, "%s: %s" % (type(exc).__name__, exc)


def import_resolver():
    """Den PRODUKTIVEN Resolver importieren. Returns (modul, fehlertext)."""
    if HERMES_SRC not in sys.path:
        sys.path.insert(0, HERMES_SRC)
    try:
        import cron.scheduler as sched

        for name in ("_resolve_single_delivery_target", "_normalize_deliver_value"):
            if not hasattr(sched, name):
                return None, "cron.scheduler ohne %s (API geaendert)" % name
        return sched, None
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def jobs_path():
    home = os.environ.get("HERMES_HOME") or os.path.join(
        os.path.expanduser("~"), "AppData", "Local", "hermes"
    )
    return os.path.join(home, "cron", "jobs.json")


def read_jobs(path):
    """Returns (items, fehlertext). items = Liste von (job_id, job-dict)."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)
    jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
    if isinstance(jobs, dict):
        items = list(jobs.items())
    elif isinstance(jobs, list):
        items = [(j.get("id"), j) for j in jobs if isinstance(j, dict)]
    else:
        return None, "jobs.json: unerwartete Struktur %s" % type(jobs).__name__
    return items, None


def chat_id_verdict(platform, chat_id):
    """(ist_defekt, regelname) fuer eine aufgeloeste Zieladresse."""
    s = str(chat_id).strip()
    low = s.lower()
    if low in POISON_MEASURED:
        return True, "PLATZHALTER-MEASURED"
    if low in POISON_ASSUMED or s == "":
        return True, "PLATZHALTER-ASSUMED"
    # Formregel, abgeleitet aus den realen Werten (18-stellige Nummer in
    # jobs.json, '...@lid' im Zustell-Log): eine WhatsApp-Adresse ist entweder
    # eine Nummer oder traegt eine JID-Domain.
    if str(platform).lower().startswith("whatsapp"):
        if "@" not in s and not s.lstrip("+").isdigit():
            return True, "WHATSAPP-FORM"
    return False, ""


def expand_parts(sched, deliver_value):
    """deliver-String in konkrete Teilziele zerlegen - mit der Produktivlogik."""
    norm = sched._normalize_deliver_value(deliver_value)
    parts = []
    for raw in str(norm).split(","):
        token = raw.strip()
        if not token:
            continue
        expand = getattr(sched, "_expand_routing_tokens", None)
        parts.extend(expand(token) if expand else [token])
    return norm, parts


def audit(items, sched):
    """Kernpruefung. Returns (zeilen, verdict).

    zeilen = Liste (stufe, text); stufe in {'ok','info','defekt'}.
    """
    lines = []
    defects = 0
    pflichtig = 0  # Jobs, die ueberhaupt zustellen SOLLEN
    local_enabled = 0
    local_stumm = 0  # aktive Jobs ohne Zustellung, die auch nichts zu sagen haben

    for jid, job in items:
        if not job.get("enabled"):
            continue
        deliver_raw = job.get("deliver")
        norm, parts = expand_parts(sched, deliver_raw)
        if norm == "local":
            local_enabled += 1
            # Nicht der Modus ist der Befund, sondern der WIDERSPRUCH:
            # ein Job, dessen eigene Quelle einen Alarm enthaelt, aber dessen
            # Alarm per Konstruktion verworfen wird (scheduler.py:1459-1460).
            quelle, herkunft = job_source(job)
            if quelle is None:
                defects += 1
                lines.append(
                    ("defekt", "DEFEKT %s: Quelle nicht lesbar (%s) - Alarmtraeger"
                     " nicht ausschliessbar" % (str(jid)[:12], herkunft))
                )
                continue
            worte = alarm_words(quelle)
            if worte:
                defects += 1
                lines.append(
                    ("defekt", "DEFEKT %s: Alarmtraeger ohne Zustellziel"
                     " (deliver='local', Alarmwort %s in %s) - der Alarm wird"
                     " von _deliver_result() verworfen"
                     % (str(jid)[:12], "/".join(worte), herkunft))
                )
                continue
            local_stumm += 1
            lines.append(
                ("info", "INFO  %s: deliver='local' - kein Alarmwort in %s,"
                 " Ausgabe bleibt auf Platte" % (str(jid)[:12], herkunft))
            )
            continue
        pflichtig += 1
        for part in parts:
            try:
                target = sched._resolve_single_delivery_target(job, part)
            except Exception as exc:
                defects += 1
                lines.append(
                    ("defekt", "DEFEKT %s: Resolver wirft %s bei deliver='%s'"
                     % (str(jid)[:12], type(exc).__name__, part))
                )
                continue
            if not target:
                defects += 1
                lines.append(
                    ("defekt", "DEFEKT %s: kein Zustellziel aufloesbar (deliver='%s')"
                     " - Bericht verschwindet lautlos" % (str(jid)[:12], part))
                )
                continue
            bad, rule = chat_id_verdict(target.get("platform"), target.get("chat_id"))
            if bad:
                defects += 1
                lines.append(
                    ("defekt", "DEFEKT %s: Ziel %s:%s nicht adressierbar [%s]"
                     % (str(jid)[:12], target.get("platform"),
                        redact(target.get("chat_id")), rule))
                )
            else:
                lines.append(
                    ("ok", "OK    %s: -> %s:%s"
                     % (str(jid)[:12], target.get("platform"),
                        redact(target.get("chat_id"))))
                )

    # --- Eigenschaft statt Zustand: ist die FALLBACK-Waffe entschaerft? ------
    # Ein neu angelegter Job mit deliver='origin' OHNE origin faellt auf den
    # Home-Channel zurueck. Ist der vergiftet, entsteht der Ticket-23-Defekt neu.
    for platform in sched._iter_home_target_platforms():
        try:
            chat_id = sched._get_home_target_chat_id(platform)
        except Exception:
            continue
        if not chat_id:
            continue
        bad, rule = chat_id_verdict(platform, chat_id)
        env_var = ""
        try:
            env_var = sched._resolve_home_env_var(platform) or ""
        except Exception:
            pass
        if bad:
            defects += 1
            lines.append(
                ("defekt", "DEFEKT fallback: %s='%s' ist nicht adressierbar [%s]"
                 " - jeder neue deliver='origin'-Job ohne origin landet hier"
                 % (env_var or platform, redact(chat_id), rule))
            )
        else:
            lines.append(
                ("ok", "OK    fallback: %s -> %s" % (env_var or platform, redact(chat_id)))
            )

    # Gezaehlt statt erklaert (Merkregel Ticket 15: ein Tor, das nur eine Zahl
    # ausgeben kann, ist nie beim Zaehlen beobachtet worden).
    if local_enabled:
        lines.append(
            ("info", "INFO  stumm: %d aktive Jobs ohne Zustellung, davon %d ohne"
             " Alarmwort in der eigenen Quelle" % (local_enabled, local_stumm))
        )

    if defects:
        return lines, DEFEKT
    if pflichtig == 0:
        # Leere-Schleife-Falle (Ticket 16): nichts gemessen ist nicht gruen.
        lines.append(
            ("info", "UNGEPRUEFT: 0 zustellpflichtige Jobs (%d enabled mit"
             " deliver='local') - das Tor hat nichts messen koennen" % local_enabled)
        )
        return lines, UNGEPRUEFT
    return lines, OK


RC = {OK: 0, DEFEKT: 1, UNGEPRUEFT: 2}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()

    print("== Cron-Zustellbarkeit (Ticket 30) ==")
    env_ok, env_note = load_env()
    print("[1] .env geladen : %s (%s)" % ("ja" if env_ok else "NEIN", env_note))
    if not env_ok:
        print("\nERGEBNIS: %s (ohne .env sieht das Audit eine andere Umgebung"
              " als der Scheduler)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    sched, err = import_resolver()
    print("[2] Resolver     : %s" % ("cron.scheduler (produktiv)" if sched else err))
    if sched is None:
        print("\nERGEBNIS: %s (Produktiv-Resolver nicht importierbar)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    path = jobs_path()
    items, err = read_jobs(path)
    print("[3] jobs.json    : %s" % (("%d Jobs" % len(items)) if items is not None else err))
    if items is None:
        print("\nERGEBNIS: %s (jobs.json unlesbar)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]
    if not items:
        print("\nERGEBNIS: %s (0 Jobs - leere Zielmenge ist nicht gruen)" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    lines, verdict = audit(items, sched)
    print("[4] Zustellziele :")
    for stufe, text in lines:
        print("    %s" % text)
    print("\nERGEBNIS: %s" % verdict)
    return RC[verdict]


# --------------------------------------------------------------------------
# Selftest: Fault Injection durch die ECHTE main() / audit().
# Kein Reimplementat - injiziert werden nur die Eingaben (Jobs + os.environ).
# --------------------------------------------------------------------------
def _job(jid, **kw):
    j = {"id": jid, "enabled": True, "deliver": "local", "origin": None}
    j.update(kw)
    return j


def _wa_origin(chat="4915112345678"):
    return {"platform": "whatsapp", "chat_id": chat, "chat_name": "x",
            "thread_id": None, "user_id": chat}


def selftest():
    import io
    import contextlib

    results = []

    def check(label, cond, detail=""):
        results.append((label, bool(cond), detail))

    env_ok, _ = load_env()
    sched, err = import_resolver()
    if sched is None:
        print("SELFTEST nicht durchfuehrbar: %s" % err)
        print("\nERGEBNIS: %s" % UNGEPRUEFT)
        return RC[UNGEPRUEFT]

    def run(items, env=None):
        """audit() durch den ECHTEN Pfad, nur Eingaben injiziert."""
        saved = {}
        env = env or {}
        for k, v in env.items():
            saved[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                lines, verdict = audit(items, sched)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        text = "\n".join(t for _s, t in lines)
        return lines, verdict, text, buf.getvalue()

    # Alle Home-Channels aus dem Weg raeumen, damit die Job-Faelle nicht vom
    # Fallback-Befund ueberlagert werden.
    clear = {}
    for p in sched._iter_home_target_platforms():
        try:
            ev = sched._resolve_home_env_var(p)
        except Exception:
            ev = None
        if ev:
            clear[ev] = ""
            clear[ev + "_THREAD_ID"] = ""
    clear["TELEGRAM_CRON_THREAD_ID"] = ""

    # -- GRUEN: gesunde Lage --------------------------------------------------
    healthy = [("a1", _job("a1", deliver="origin", origin=_wa_origin()))]
    _l, v, t, _o = run(healthy, clear)
    check("gruen/gesunder origin-Job -> OK", v == OK, v)
    check("gruen/Adresse redigiert", "4915112345678" not in t, t)
    check("gruen/OK-Zeile nennt Job", "OK    a1" in t, t)

    # -- ROT 1: der Ticket-23-Defekt (deliver=origin, origin=None) -----------
    broken = [("b1", _job("b1", deliver="origin", origin=None))]
    _l, v, t, _o = run(broken, clear)
    check("rot/origin=None -> DEFEKT", v == DEFEKT, v)
    check("rot/origin=None exakte Zeile",
          "DEFEKT b1: kein Zustellziel aufloesbar (deliver='origin')" in t, t)
    check("rot/origin=None kein Traceback", "Traceback" not in t, t)

    # -- ROT 2: Fallback vergiftet (die EIGENSCHAFT, nicht der Zustand) ------
    poisoned = dict(clear)
    poisoned["WHATSAPP_HOME_CHANNEL"] = "self"
    _l, v, t, _o = run(healthy, poisoned)
    check("rot/Fallback='self' -> DEFEKT", v == DEFEKT, v)
    check("rot/Fallback exakte Zeile",
          "DEFEKT fallback: WHATSAPP_HOME_CHANNEL=" in t
          and "[PLATZHALTER-MEASURED]" in t, t)
    check("rot/Fallback nennt Folge",
          "jeder neue deliver='origin'-Job ohne origin landet hier" in t, t)
    check("rot/Fallback kein Traceback", "Traceback" not in t, t)

    # -- ROT 2b: vergifteter Fallback FAENGT den origin-losen Job ------------
    _l, v, t, _o = run(broken, poisoned)
    check("rot/origin=None + Fallback self -> DEFEKT", v == DEFEKT, v)
    check("rot/Job erbt die Giftadresse",
          "DEFEKT b1: Ziel whatsapp:" in t and "[PLATZHALTER-MEASURED]" in t, t)

    # -- ROT 3: origin-dict ohne chat_id (Teilform, T30 'nicht vergessen') ---
    half = [("c1", _job("c1", deliver="origin",
                        origin={"platform": "whatsapp", "chat_id": ""}))]
    _l, v, t, _o = run(half, clear)
    check("rot/origin ohne chat_id -> DEFEKT", v == DEFEKT, v)
    check("rot/origin ohne chat_id exakte Zeile",
          "DEFEKT c1: kein Zustellziel aufloesbar (deliver='origin')" in t, t)

    # -- ROT 4: origin ist ein String (der #18722-Fall) ----------------------
    poison_origin = [("d1", _job("d1", deliver="origin", origin="ersetzt-job-x"))]
    _l, v, t, _o = run(poison_origin, clear)
    check("rot/origin=str -> DEFEKT", v == DEFEKT, v)
    check("rot/origin=str kein Absturz", "Traceback" not in t, t)

    # -- ROT 5: explizites Ziel mit Platzhalter-Adresse ----------------------
    expl = [("e1", _job("e1", deliver="whatsapp:self"))]
    _l, v, t, _o = run(expl, clear)
    check("rot/deliver='whatsapp:self' -> DEFEKT", v == DEFEKT, v)
    check("rot/explizit exakte Regel", "[PLATZHALTER-MEASURED]" in t, t)

    # -- ROT 6: WhatsApp-Formregel (kein @, keine Nummer) --------------------
    shape = [("f1", _job("f1", deliver="whatsapp:kaputte-adresse"))]
    _l, v, t, _o = run(shape, clear)
    check("rot/WhatsApp-Formregel -> DEFEKT", v == DEFEKT, v)
    check("rot/Formregel benannt", "[WHATSAPP-FORM]" in t, t)

    # -- ROT 7: Listenform ['whatsapp'] (Normalisierungsfalle) ---------------
    listform = [("g1", _job("g1", deliver=["whatsapp"], origin=_wa_origin()))]
    _l, v, t, _o = run(listform, clear)
    check("liste/deliver=['whatsapp'] wird normalisiert -> OK", v == OK, v)

    # -- UNGEPRUEFT: leere Zielmenge ist NICHT gruen -------------------------
    only_local = [("h1", _job("h1", deliver="local"))]
    _l, v, t, _o = run(only_local, clear)
    check("leer/nur local -> UNGEPRUEFT", v == UNGEPRUEFT, v)
    check("leer/nicht gruen", v != OK, v)
    check("leer/Begruendung genannt",
          "0 zustellpflichtige Jobs" in t, t)

    _l, v, t, _o = run([], clear)
    check("leer/0 Jobs -> UNGEPRUEFT (nicht gruen)", v == UNGEPRUEFT, v)

    # -- ROT 7: Alarmtraeger ohne Zustellziel (Agent-Job, Quelle = prompt) ----
    # Positivkontrolle (Ticket 15): das Tor muss den stummen Alarm ERKENNEN,
    # nicht nur die gesunde Lage durchwinken.
    schreier = [("j1", _job("j1", deliver="local",
                            prompt="Bei Sale: GROSS 'ERSTER SALE' melden."))]
    _l, v, t, _o = run(schreier, clear)
    check("rot/Alarm im prompt + local -> DEFEKT", v == DEFEKT, v)
    check("rot/Alarm exakte Zeile",
          "DEFEKT j1: Alarmtraeger ohne Zustellziel (deliver='local',"
          " Alarmwort ERSTER SALE in prompt) - der Alarm wird von"
          " _deliver_result() verworfen" in t, t)
    check("rot/Alarm kein Traceback", "Traceback" not in t, t)

    # -- ROT 8: Alarmtraeger als SKRIPT (Quelle = Datei, nicht prompt) -------
    import tempfile
    fd, skript = tempfile.mkstemp(suffix="_alarmprobe.py", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("print('*** RING MELDET: DEFEKT ***')\n")
        sjob = [("k1", _job("k1", deliver="local", no_agent=True,
                            script=skript, prompt="harmlos, kein Alarmwort"))]
        _l, v, t, _o = run(sjob, clear)
        check("rot/Alarm im Skript + local -> DEFEKT", v == DEFEKT, v)
        check("rot/Skript wird als Quelle genannt",
              "in script:%s" % os.path.basename(skript) in t, t)
        # Der prompt darf die Skriptquelle NICHT ueberstimmen (und umgekehrt):
        check("rot/prompt ueberstimmt Skript nicht", "in prompt" not in t, t)

        # -- ROT 9: Quelle unlesbar ist NICHT gruen --------------------------
        os.unlink(skript)
        _l, v, t, _o = run(sjob, clear)
        check("rot/unlesbare Quelle -> DEFEKT", v == DEFEKT, v)
        check("rot/unlesbare Quelle exakte Zeile",
              "DEFEKT k1: Quelle nicht lesbar" in t
              and "Alarmtraeger nicht ausschliessbar" in t, t)
    finally:
        if os.path.exists(skript):
            os.unlink(skript)

    # -- GRUEN: Alarmtraeger MIT Zustellziel ist in Ordnung ------------------
    # Ohne diesen Fall koennte das Tor nach dem Fix nie wieder gruen werden.
    laut_ok = [("l1", _job("l1", deliver="origin", origin=_wa_origin(),
                           prompt="meldet ERSTER SALE"))]
    _l, v, t, _o = run(laut_ok, clear)
    check("gruen/Alarmtraeger mit Ziel -> OK", v == OK, v)

    # -- GRUEN: stiller local-Job bleibt ohne Defekt-Claim -------------------
    still = [("m1", _job("m1", deliver="local", prompt="sammelt nur Zahlen")),
             ("m2", _job("m2", deliver="origin", origin=_wa_origin()))]
    _l, v, t, _o = run(still, clear)
    check("gruen/local ohne Alarmwort -> kein Defekt", v == OK, v)
    check("gruen/local-Zeile ohne Intent-Behauptung",
          "bewusst" not in t, t)
    check("gruen/local-Zeile nennt die Quelle",
          "INFO  m1: deliver='local' - kein Alarmwort in prompt" in t, t)
    check("zaehlung/stumme Jobs werden gezaehlt",
          "INFO  stumm: 1 aktive Jobs ohne Zustellung, davon 1 ohne" in t, t)

    # -- Mischung: ein gesunder + ein kaputter Job -> DEFEKT gewinnt ---------
    mixed = healthy + broken
    _l, v, t, _o = run(mixed, clear)
    check("misch/ein Kaputter kippt das Ergebnis", v == DEFEKT, v)
    check("misch/gesunder Job bleibt sichtbar", "OK    a1" in t, t)

    # -- disabled Jobs zaehlen nicht -----------------------------------------
    disabled = [("i1", _job("i1", deliver="origin", origin=None, enabled=False))]
    _l, v, t, _o = run(disabled, clear)
    check("disabled/zaehlt nicht als Defekt", v == UNGEPRUEFT, v)

    # -- Kontrakt: rc-Abbildung ----------------------------------------------
    check("rc/OK=0", RC[OK] == 0)
    check("rc/DEFEKT=1", RC[DEFEKT] == 1)
    check("rc/UNGEPRUEFT=2", RC[UNGEPRUEFT] == 2)

    # -- Umgebung: .env muss ladbar sein, sonst misst das Tor die falsche Welt
    check("env/.env ladbar", env_ok, "load_hermes_dotenv")

    # -- redact() gibt nie den vollen Wert preis ------------------------------
    check("redact/kein Klartext", "4915112345678" not in redact("4915112345678"))

    ok = sum(1 for _l, c, _d in results if c)
    for label, cond, detail in results:
        if not cond:
            print("  FAIL %-46s %s" % (label, str(detail)[:120]))
    print("SELFTEST %d/%d" % (ok, len(results)))
    if ok == len(results):
        print("\nERGEBNIS: SELFTEST_OK")
        return 0
    print("\nERGEBNIS: SELFTEST_DEFEKT")
    return 1


if __name__ == "__main__":
    sys.exit(main())
