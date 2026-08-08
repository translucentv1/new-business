#!/usr/bin/env python3
"""Ticket 24 - stehendes Tor fuer die CRON-INFRASTRUKTUR des Geldpfads.

WARUM (MEASURED, Ticket 22): Der Job, der die 24-h-Zusage aus agb.html § 3
traegt, war 143 Laeufe lang tot (0 completed vom 30.07. bis 06.08.), waehrend
JEDER Pruefer im Repo gruen meldete. Ursache lag ausserhalb des Repos:
erst "RuntimeError: HTTP 404" (Modell weg), dann 135x "Skipped to prevent
unintended spend ... this job is unpinned" nach einem globalen Modellwechsel.
Ticket 22 hat das EINMALIG von Hand gemessen und repariert - ein stehendes Tor
gab es nicht. Genau das ist dieses Skript.

MERKREGEL, die hier umgesetzt wird: Ein Pruefer, der nur das Repo kennt, sieht
die Infrastruktur nicht. Bei jeder Zusage fragen: welches System muss dafuer
laufen, und wo steht sein Protokoll?  -> $HERMES_HOME/cron/{jobs.json,executions.db}

ZIELMENGE WIRD ABGELEITET, NICHT HARTKODIERT (Merkregel Ticket 17):
Geldpfad-Traeger = ein Cron-Job, dessen Skript - direkt oder ueber den Loader
unter $HERMES_HOME/scripts/ - Code aus <REPO>/scripts/request_delivery/
ausfuehrt. Eine hartkodierte Job-Id waere still veraltet, sobald der Nutzer den
Job neu anlegt.

LEERE ZIELMENGE IST NICHT GRUEN (Merkregel Ticket 16): "kein Job liefert aus"
ist exakt der Ticket-22-Zustand und muss rot sein, nicht gruen.

AGENTENGETRIEBENE JOBS ZAEHLEN NICHT ALS TRAEGER (Entscheidung, MEASURED
begruendet): Ticket 22 hat belegt, dass genau diese Bauform ausfaellt
(Spend-Protection, HTTP 404/429/524 auf das Modell). Ein Job mit
no_agent=False haengt an Modellverfuegbarkeit und kann eine 24-h-Zusage nicht
tragen. Solche Jobs werden als "Nebentraeger" protokolliert, aber sie machen
die Zielmenge nicht voll.

Ergebniswoerter (Merkregel Ticket 16/17/18/19):
    CRON_HEALTH_OK          rc=0
    CRON_HEALTH_DEFEKT      rc=1   (echter Defekt schlaegt Unmessbarkeit)
    CRON_HEALTH_UNGEPRUEFT  rc=2   (jobs.json/executions.db nicht lesbar o.ae.)

Aufruf:
    python scripts/request_delivery/cron_health_audit.py
    python scripts/request_delivery/cron_health_audit.py --selftest
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MONEY_DIR = os.path.join(ROOT, "scripts", "request_delivery")

MONEY_TOKEN = "request_delivery"
# Ticket 25: "nennt den Geldpfad" != "liefert". Ein WAECHTER-Job ruft nur das
# Audit auf; er traegt keine Lieferung und schreibt keinen Heartbeat. Wuerde
# er als Traeger gelten, meldete das Audit fuer immer UNGEPRUEFT ("2 Traeger,
# nur EIN Heartbeat") und beurteilte ihn nach einem Beleg, den er per
# Konstruktion nie erzeugt. Traeger ist deshalb nur, wer die
# Fulfillment-Pipeline anstoesst.
FULFILL_TOKEN = "auto_fulfill"
# Ticket 25: woran ein WAECHTER erkannt wird - er ruft dieses Audit auf.
AUDIT_TOKEN = "cron_health_audit"
# § 3 agb.html verspricht Lieferung binnen 24 h -> ein Traeger, der seltener
# als taeglich laeuft, kann die Zusage nicht halten.
MAX_PROMISE_MIN = 1440

# Ticket 25 (LATCH): Der Exitstatus des Traegers wird von DIESEM Audit
# mitbestimmt - es laeuft als Etappe [3] IN cron_auto_fulfill.py. Ein Urteil,
# das sich aus "letztes completed" speist, kann sich daher nie wieder
# freimachen: ein rotes Audit verhindert das naechste completed, wodurch das
# Alter weiter waechst. MEASURED 2026-08-07 an 5 Laeufen von bfb63346d942:
# 909 -> 940 -> 970 -> 1001 -> 1031 min, monoton, Pipeline dabei kerngesund.
# Kriterien daher NUR noch kausal VOR dem Urteil liegende Groessen:
#   [A] Lauf-VERSUCHE aus executions.db (feuert der Job ueberhaupt?)
#   [B] Pipeline-Heartbeat, geschrieben nach Etappe [1]+[2] (lief die
#       Lieferung?) - unabhaengig davon, wie das Audit danach urteilt.
PIPELINE_HB = os.path.join(MONEY_DIR, ".pipeline_heartbeat.json")
# Fenster, in dem nach globalem Scheduler-Stillstand gesucht wird.
STILLSTAND_FENSTER_MIN = 2880
# Toleranz fuer die Erfolgs-Luecke: drei Intervalle, mindestens 3 h, hoechstens
# die Zusage selbst.
MIN_TOLERANZ_MIN = 180

# Zieldatei eines Loaders: der .py-Name, der direkt hinter dem Token
# "request_delivery" steht (os.path.join-Form ODER Pfadform mit / bzw. \).
TARGET_RE = re.compile(
    r"request_delivery[\"'\s,\\/)]{0,40}[\"']?([A-Za-z0-9_.\-]+\.py)"
)
ABSPATH_RE = re.compile(r"[A-Za-z]:[\\/][^\"'\n]{2,200}")


class Unmessbar(Exception):
    """Eine Etappe ist nicht messbar - weder gruen noch Defekt-Claim."""


def nk(path):
    return os.path.normcase(os.path.normpath(str(path)))


# --------------------------------------------------------------------------
# IO-Schicht. Alles, was die Aussenwelt beruehrt, laeuft ueber diese Namen -
# der --selftest ersetzt sie ueber globals() und faehrt die ECHTE main().
# --------------------------------------------------------------------------
def io_home():
    return os.environ.get("HERMES_HOME")


def io_read_jobs(home):
    path = os.path.join(home, "cron", "jobs.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        raise Unmessbar(f"jobs.json nicht lesbar: {exc}") from exc
    except ValueError as exc:
        raise Unmessbar(f"jobs.json nicht parsebar: {exc}") from exc
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    if isinstance(jobs, dict):
        jobs = list(jobs.values())
    if not isinstance(jobs, list):
        raise Unmessbar("jobs.json hat unerwartete Struktur")
    return jobs


def io_read_executions(home):
    """job_id -> Liste (status, timestamp-string). Read-only, WAL-schonend."""
    path = os.path.join(home, "cron", "executions.db")
    if not os.path.isfile(path):
        raise Unmessbar(f"executions.db fehlt: {path}")
    uri = "file:///" + path.replace("\\", "/") + "?mode=ro"
    out = {}
    try:
        con = sqlite3.connect(uri, uri=True, timeout=10)
        try:
            rows = con.execute(
                "SELECT job_id, status, COALESCE(started_at, claimed_at, "
                "finished_at) FROM executions"
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise Unmessbar(f"executions.db nicht lesbar: {exc}") from exc
    for job_id, status, ts in rows:
        out.setdefault(job_id, []).append((status, ts))
    return out


def io_isfile(path):
    return os.path.isfile(path)


def io_isdir(path):
    return os.path.isdir(path)


def io_read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError as exc:
        raise Unmessbar(f"Skript nicht lesbar: {path} ({exc})") from exc


def io_now():
    return datetime.now(timezone.utc)


def io_read_pipeline_hb():
    """Heartbeat der Liefer-Pipeline. -> (ts-string|None, fehlertext|None).

    Geschrieben von cron_auto_fulfill.py NACH Etappe [1]+[2] und damit
    kausal VOR dem Urteil dieses Audits (Ticket 25, Latch-Fix).
    """
    try:
        with open(PIPELINE_HB, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None, (f"Pipeline-Heartbeat fehlt ({os.path.basename(PIPELINE_HB)}"
                      f") - die Pipeline hat seit Einfuehrung nie gemeldet")
    except OSError as exc:
        return None, f"Pipeline-Heartbeat nicht lesbar: {exc}"
    except ValueError as exc:
        return None, f"Pipeline-Heartbeat nicht parsebar: {exc}"
    if not isinstance(data, dict) or not data.get("ts"):
        return None, "Pipeline-Heartbeat ohne Feld 'ts'"
    return data.get("ts"), None


# --------------------------------------------------------------------------
def parse_ts(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def interval_minutes(job):
    """(minuten, fehlertext) - None bedeutet: nicht ableitbar (unmessbar)."""
    sched = job.get("schedule")
    if isinstance(sched, dict):
        if sched.get("kind") == "interval":
            minutes = sched.get("minutes")
            if isinstance(minutes, (int, float)) and minutes > 0:
                return float(minutes), None
        return None, f"schedule nicht als Intervall lesbar: {sched!r}"
    return None, f"kein schedule-Feld ({sched!r})"


def classify(jobs, home):
    """Zielmenge ABLEITEN. -> (traeger, waechter, nebentraeger, offen, info)"""
    traeger, waechter, neben, offen, info = [], [], [], [], []
    for job in jobs:
        script = job.get("script")
        prompt = job.get("prompt") or ""
        name = f"{job.get('id')} {str(job.get('name'))[:40]}"
        if not script:
            if MONEY_TOKEN in prompt:
                neben.append((job, "agentengetrieben, Prompt nennt "
                                   + MONEY_TOKEN))
            continue
        path = script if os.path.isabs(script) else os.path.join(
            home, "scripts", script)
        if not io_isfile(path):
            # Klassifikation nur ueber den Prompt moeglich - ehrlich benennen.
            if MONEY_TOKEN in prompt:
                offen.append((job, f"Skript fehlt ({path}), Prompt nennt "
                                   f"{MONEY_TOKEN} -> Klassifikation offen"))
            else:
                info.append(f"{name}: Skript fehlt ({path}), Prompt nennt "
                            f"{MONEY_TOKEN} nicht -> kein Geldpfad")
            continue
        try:
            text = io_read_text(path)
        except Unmessbar as exc:
            offen.append((job, str(exc)))
            continue
        if MONEY_TOKEN in text or nk(path).startswith(nk(MONEY_DIR)):
            # Ticket 25: Traeger ist nur, wer die Lieferung ANSTOESST. Ein
            # Waechter ruft bloss dieses Audit auf; er schreibt per
            # Konstruktion nie einen Pipeline-Heartbeat. Wuerde er als
            # Traeger zaehlen, meldete [B] fuer immer "nur EIN Heartbeat"
            # -> CRON_HEALTH_UNGEPRUEFT auf Dauer, und der Waechter wuerde
            # nach einem Beleg beurteilt, den er nie erzeugen kann.
            if FULFILL_TOKEN in text:
                traeger.append((job, path, text))
            elif AUDIT_TOKEN in text:
                waechter.append((job, path, text))
            else:
                offen.append((job, f"Skript liegt im Geldpfad, nennt aber "
                                   f"weder {FULFILL_TOKEN} noch {AUDIT_TOKEN} "
                                   f"-> Rolle nicht ableitbar"))
        elif MONEY_TOKEN in prompt and not job.get("no_agent"):
            neben.append((job, "agentengetrieben, Prompt nennt " + MONEY_TOKEN))
    return traeger, waechter, neben, offen, info


def global_stillstand(execs, now):
    """Groesste Zeitspanne im Fenster, in der KEIN EINZIGER Job gefeuert hat.

    Trennt \"der Geldpfad-Job ist tot\" von \"der ganze Scheduler stand\"
    (Rechner/Gateway aus). Ohne diese Trennung wird eine Nachtabschaltung als
    Geldpfad-Defekt gemeldet - MEASURED 2026-08-07: 15 h ohne einen einzigen
    Lauf irgendeines Jobs, danach 5x CRON_HEALTH_DEFEKT gegen eine gesunde
    Pipeline. -> Minuten (float) oder None, wenn nicht bestimmbar.
    """
    if not execs:
        return None
    grenze = now - timedelta(minutes=STILLSTAND_FENSTER_MIN)
    stamps = []
    for rows in execs.values():
        for _, raw in rows:
            t = parse_ts(raw)
            if t and t >= grenze:
                stamps.append(t)
    if not stamps:
        return None          # nichts im Fenster -> keine Aussage (nicht 0!)
    stamps.sort()
    # Nur echte Luecken ZWISCHEN Laeufen und die Luecke bis jetzt zaehlen.
    # Der Fensterrand zaehlt NICHT - sonst meldet eine frische DB Stillstand.
    luecke = (now - stamps[-1]).total_seconds() / 60.0
    for a, b in zip(stamps, stamps[1:]):
        luecke = max(luecke, (b - a).total_seconds() / 60.0)
    return luecke


def check_traeger(job, path, text, execs, now, defects, unknown, out,
                  hb_ts=None, hb_err=None, stillstand=None):
    jid = job.get("id")
    tag = f"{jid} {str(job.get('name'))[:44]}"
    out.append(f"  * {tag}")
    out.append(f"      script    = {path}")

    # -- Zieldatei im Repo -------------------------------------------------
    targets = sorted({m for m in TARGET_RE.findall(text)
                      if m != os.path.basename(path)})
    if not targets:
        unknown.append(f"{tag}: Zieldatei in {os.path.basename(path)} nicht "
                       f"erkennbar -> Klassifikation offen")
        out.append("      Ziel      = (nicht erkennbar)")
    for tgt in targets:
        full = os.path.join(MONEY_DIR, tgt)
        if io_isfile(full):
            out.append(f"      Ziel      = {full}  [vorhanden]")
        else:
            defects.append(f"{tag}: Zieldatei fehlt: {full}")
            out.append(f"      Ziel      = {full}  [FEHLT]")

    # -- Loader zeigt auf dieses Repo? ------------------------------------
    abspaths = [p for p in ABSPATH_RE.findall(text) if p.rstrip("\"',) ")]
    if abspaths and not any(nk(p).startswith(nk(ROOT)) for p in abspaths):
        defects.append(f"{tag}: Loader nennt keinen Pfad in diesem Repo "
                       f"({ROOT}) -> zeigt auf fremdes Repo")

    # -- Bauform / Aktivierung --------------------------------------------
    if not job.get("enabled"):
        defects.append(f"{tag}: enabled=False - Geldpfad-Job ist abgeschaltet")
    if not job.get("no_agent"):
        defects.append(f"{tag}: no_agent=False - Job braucht einen "
                       f"Inferenz-Call (exakt die Ticket-22-Ursache: "
                       f"Spend-Protection/Modellausfall killt die Lieferung)")
    out.append(f"      enabled   = {job.get('enabled')}   "
               f"no_agent = {job.get('no_agent')}")

    # -- workdir -----------------------------------------------------------
    workdir = job.get("workdir")
    if not workdir:
        defects.append(f"{tag}: workdir nicht gesetzt - Pipeline liefe im "
                       f"falschen Verzeichnis")
    elif not io_isdir(workdir):
        defects.append(f"{tag}: workdir existiert nicht: {workdir}")
    out.append(f"      workdir   = {workdir}")

    # -- Intervall gegen die 24-h-Zusage -----------------------------------
    minutes, err = interval_minutes(job)
    if minutes is None:
        unknown.append(f"{tag}: Intervall nicht ableitbar ({err})")
        out.append("      Intervall = (nicht ableitbar)")
        toleranz = None
    else:
        if minutes > MAX_PROMISE_MIN:
            defects.append(f"{tag}: Intervall {minutes:.0f} min > "
                           f"{MAX_PROMISE_MIN} min - die 24-h-Zusage aus "
                           f"agb.html § 3 ist nicht gedeckt")
        toleranz = min(max(3 * minutes, MIN_TOLERANZ_MIN), MAX_PROMISE_MIN)
        out.append(f"      Intervall = {minutes:.0f} min  "
                   f"(erlaubte Erfolgs-Luecke {toleranz:.0f} min)")

    # -- Protokoll: laeuft er wirklich? ------------------------------------
    if execs is None:
        out.append("      Laeufe    = (executions.db nicht lesbar)")
        return
    rows = execs.get(jid, [])
    done = [parse_ts(ts) for st, ts in rows if st == "completed"]
    done = [d for d in done if d]
    attempts = [parse_ts(ts) for _, ts in rows]
    attempts = [a for a in attempts if a]
    n_fail = sum(1 for st, _ in rows if st not in ("completed",))
    out.append(f"      Laeufe    = {len(rows)} gesamt / "
               f"{len(done)} completed / {n_fail} nicht-completed")
    if not rows:
        defects.append(f"{tag}: 0 Laeufe protokolliert - der Job hat nie "
                       f"gefeuert (Ticket-22-Zustand)")
        return

    # -- Job-Exitstatus: ab Ticket 25 nur noch INFO ------------------------
    # Er ist KEIN Kriterium mehr, weil dieses Audit ihn selbst mitbestimmt
    # (Etappe [3] in cron_auto_fulfill.py -> rc=1 -> Job faellt -> nie wieder
    # 'completed' -> Alter waechst monoton = Latch).
    if done:
        ok_age = (now - max(done)).total_seconds() / 60.0
        out.append(f"      letzter Job-Exit 'completed' vor {ok_age:.0f} min "
                   f"[INFO - kein Kriterium, Selbstbezug]")
    else:
        out.append(f"      letzter Job-Exit 'completed' = keiner in "
                   f"{len(rows)} Laeufen [INFO - kein Kriterium, Selbstbezug; "
                   f"ob geliefert wird, sagen [A] und [B]]")

    stillstand_deckt = (stillstand is not None
                        and toleranz is not None
                        and stillstand > toleranz)

    # -- [A] Feuert der Job ueberhaupt? (Lauf-VERSUCHE, jeder Status) ------
    if attempts:
        a_age = (now - max(attempts)).total_seconds() / 60.0
        out.append(f"      [A] letzter Lauf-VERSUCH vor {a_age:.0f} min")
        if toleranz is not None and a_age > toleranz:
            if stillstand_deckt and stillstand >= a_age - 1:
                unknown.append(
                    f"{tag}: seit {a_age:.0f} min kein Lauf - in dieser Zeit "
                    f"lief aber KEIN einziger Job ({stillstand:.0f} min "
                    f"Scheduler-Stillstand, Rechner/Gateway aus) -> nicht dem "
                    f"Geldpfad anlastbar")
            else:
                defects.append(
                    f"{tag}: letzter Lauf-VERSUCH vor {a_age:.0f} min, "
                    f"erlaubt waeren {toleranz:.0f} min - der Job feuert nicht")
    else:
        unknown.append(f"{tag}: kein Lauf-Zeitstempel parsebar")

    # -- [B] Lief die Liefer-Pipeline? (Heartbeat aus Etappe [1]+[2]) ------
    if hb_err:
        out.append("      [B] Pipeline-Heartbeat = (fehlt)")
        unknown.append(f"{tag}: {hb_err} -> Pipeline-Lauf nicht belegbar")
        return
    hb = parse_ts(hb_ts)
    if hb is None:
        out.append(f"      [B] Pipeline-Heartbeat = (ts unlesbar: {hb_ts!r})")
        unknown.append(f"{tag}: Pipeline-Heartbeat-Zeitstempel unlesbar "
                       f"({hb_ts!r})")
        return
    hb_age = (now - hb).total_seconds() / 60.0
    out.append(f"      [B] Pipeline-Heartbeat vor {hb_age:.0f} min "
               f"({hb.isoformat()})")
    if toleranz is not None and hb_age > toleranz:
        if stillstand_deckt and stillstand >= hb_age - 1:
            unknown.append(
                f"{tag}: Pipeline meldete zuletzt vor {hb_age:.0f} min - in "
                f"dieser Zeit stand der Scheduler ({stillstand:.0f} min) -> "
                f"nicht dem Geldpfad anlastbar")
        else:
            defects.append(
                f"{tag}: Liefer-Pipeline meldete zuletzt vor {hb_age:.0f} min, "
                f"erlaubt waeren {toleranz:.0f} min - die Lieferung steht")


def check_waechter(job, path, text, execs, now, defects, unknown, out,
                   stillstand=None):
    """Der zweite, unabhaengige Ring (Ticket 25).

    Er traegt KEINE Lieferung, also gilt Kriterium [B] (Pipeline-Heartbeat)
    fuer ihn nicht. Geprueft wird nur, ob er ueberhaupt feuert - und das ueber
    Lauf-VERSUCHE, nicht ueber 'completed': sein Exitstatus haengt am Urteil
    des Audits, das er selbst startet (derselbe Latch wie beim Traeger).
    """
    jid = job.get("id")
    tag = f"{jid} {str(job.get('name'))[:44]}"
    out.append(f"  * {tag}  [WAECHTER]")
    out.append(f"      script    = {path}")

    if not job.get("enabled"):
        defects.append(f"{tag}: enabled=False - der zweite Ring ist "
                       f"abgeschaltet")
    if not job.get("no_agent"):
        defects.append(f"{tag}: no_agent=False - ein Waechter mit "
                       f"Inferenz-Call erbt exakt die Ausfallmodi, gegen die "
                       f"er schuetzen soll (Ticket 22)")
    out.append(f"      enabled   = {job.get('enabled')}   "
               f"no_agent = {job.get('no_agent')}")

    minutes, err = interval_minutes(job)
    if minutes is None:
        unknown.append(f"{tag}: Intervall nicht ableitbar ({err})")
        toleranz = None
    else:
        toleranz = min(max(3 * minutes, MIN_TOLERANZ_MIN), MAX_PROMISE_MIN)
        out.append(f"      Intervall = {minutes:.0f} min  "
                   f"(erlaubte Lauf-Luecke {toleranz:.0f} min)")

    if execs is None:
        out.append("      Laeufe    = (executions.db nicht lesbar)")
        return
    rows = execs.get(jid, [])
    attempts = [parse_ts(ts) for _, ts in rows]
    attempts = [a for a in attempts if a]
    out.append(f"      Laeufe    = {len(rows)} gesamt")
    if not rows:
        defects.append(f"{tag}: 0 Laeufe protokolliert - der Waechter "
                       f"existiert, hat aber nie gefeuert")
        return
    if not attempts:
        unknown.append(f"{tag}: kein Lauf-Zeitstempel parsebar")
        return
    a_age = (now - max(attempts)).total_seconds() / 60.0
    out.append(f"      [A] letzter Lauf-VERSUCH vor {a_age:.0f} min")
    if toleranz is not None and a_age > toleranz:
        if (stillstand is not None and stillstand > toleranz
                and stillstand >= a_age - 1):
            unknown.append(
                f"{tag}: seit {a_age:.0f} min kein Lauf - in dieser Zeit lief "
                f"aber KEIN einziger Job ({stillstand:.0f} min "
                f"Scheduler-Stillstand) -> nicht dem Waechter anlastbar")
        else:
            defects.append(
                f"{tag}: letzter Lauf-VERSUCH vor {a_age:.0f} min, erlaubt "
                f"waeren {toleranz:.0f} min - der Waechter feuert nicht")


def main():
    print("== cron_health_audit (Ticket 24) ==")
    print("Geltungsbereich : Scheduler-Infrastruktur ($HERMES_HOME) + "
          "lokaler Repo-Baum (kein Netz)")
    defects, unknown, out = [], [], []

    home = io_home()
    print(f"HERMES_HOME     : {home}")
    print(f"Repo            : {ROOT}")
    if not home:
        print("ERGEBNIS: CRON_HEALTH_UNGEPRUEFT (HERMES_HOME nicht gesetzt - "
              "der Scheduler ist von hier aus nicht auffindbar)")
        return 2
    try:
        jobs = io_read_jobs(home)
    except Unmessbar as exc:
        print(f"ERGEBNIS: CRON_HEALTH_UNGEPRUEFT ({exc})")
        return 2

    try:
        execs = io_read_executions(home)
    except Unmessbar as exc:
        execs = None
        unknown.append(f"Protokoll nicht lesbar: {exc}")

    traeger, waechter, neben, offen, info = classify(jobs, home)
    n_en = sum(1 for j in jobs if j.get("enabled"))
    print(f"Jobs            : {len(jobs)} gesamt, {n_en} enabled")
    print(f"Geldpfad-Traeger (abgeleitet, nicht hartkodiert): {len(traeger)}")
    print(f"Waechter (2. Ring, Ticket 25): {len(waechter)}")

    now = io_now()
    stillstand = global_stillstand(execs, now) if execs else None
    hb_ts, hb_err = io_read_pipeline_hb()
    if stillstand is not None:
        print(f"Scheduler-Stillstand (groesste Luecke ohne EINEN Job-Lauf in "
              f"{STILLSTAND_FENSTER_MIN} min): {stillstand:.0f} min")
        # Nur ein Stillstand JENSEITS der Zusage ist ein echter Defekt: dann
        # war die 24-h-Lieferzusage in diesem Fenster real ungedeckt.
        if stillstand > MAX_PROMISE_MIN:
            defects.append(
                f"Scheduler stand {stillstand:.0f} min still (> "
                f"{MAX_PROMISE_MIN} min) - in diesem Fenster war die "
                f"24-h-Zusage aus agb.html § 3 real ungedeckt")
    print(f"Pipeline-Heartbeat: "
          + (f"{hb_ts}" if not hb_err else f"(fehlt) {hb_err}"))
    if len(traeger) > 1 and not hb_err:
        # Ehrliche Grenze: es gibt genau EINE Heartbeat-Datei. Bei mehreren
        # Traegern kann [B] nicht sagen, WELCHER geliefert hat.
        unknown.append(
            f"{len(traeger)} Geldpfad-Traeger, aber nur EIN Pipeline-"
            f"Heartbeat -> Kriterium [B] ist nicht traegerscharf")
    for job, path, text in traeger:
        check_traeger(job, path, text, execs, now, defects, unknown, out,
                      hb_ts=hb_ts, hb_err=hb_err, stillstand=stillstand)
    for job, path, text in waechter:
        check_waechter(job, path, text, execs, now, defects, unknown, out,
                       stillstand=stillstand)
    for line in out:
        print(line)

    if neben:
        print("Nebentraeger (agentengetrieben - zaehlen NICHT, Ticket 22: "
              "genau diese Bauform fiel 143x aus):")
        for job, why in neben:
            print(f"  - {job.get('id')} {str(job.get('name'))[:40]} "
                  f"| enabled={job.get('enabled')} "
                  f"last_status={job.get('last_status')} | {why}")
    for job, why in offen:
        unknown.append(f"{job.get('id')} {str(job.get('name'))[:40]}: {why}")
    if info:
        print("Nur protokolliert (kein Geldpfad):")
        for line in info:
            print(f"  - {line}")

    if not traeger:
        defects.append(
            "KEIN Geldpfad-Job: kein Cron fuehrt Code aus "
            "scripts/request_delivery/ aus (Ticket-22-Zustand) - die "
            "24-h-Zusage aus agb.html § 3 traegt niemand")

    if defects:
        print(f"DEFEKTE ({len(defects)}):")
        for d in defects:
            print(f"  ! {d}")
    if unknown:
        print(f"UNMESSBAR ({len(unknown)}):")
        for u in unknown:
            print(f"  ? {u}")

    # Reihenfolge: echter Defekt > unmessbar > OK (Merkregel Ticket 17/19)
    if defects:
        print(f"ERGEBNIS: CRON_HEALTH_DEFEKT ({len(defects)} Defekt(e), "
              f"{len(traeger)} Geldpfad-Traeger geprueft)")
        return 1
    if unknown:
        print(f"ERGEBNIS: CRON_HEALTH_UNGEPRUEFT ({len(unknown)} Etappe(n) "
              f"nicht messbar)")
        return 2
    print(f"ERGEBNIS: CRON_HEALTH_OK ({len(traeger)} Geldpfad-Traeger "
          f"ueberwacht, Geltungsbereich: Scheduler + Repo-Baum)")
    return 0


# --------------------------------------------------------------------------
def _selftest():
    """Fault Injection durch die ECHTE main() - kein Reimplementat."""
    import contextlib
    import io as _io

    g = globals()
    results = []

    def t(cond, name, detail=""):
        results.append((bool(cond), name))
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}"
              + (f" | {detail}" if detail else ""))

    NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
    HOME = os.path.join("Z:", "fakehermes")
    LOADER = os.path.join(HOME, "scripts", "rtd_auto_fulfill.py")
    TARGET = os.path.join(MONEY_DIR, "cron_auto_fulfill.py")
    LOADER_TEXT = (
        'TARGET = os.path.join(\n'
        f'    r"{ROOT}", "scripts", "request_delivery",\n'
        '    "cron_auto_fulfill.py",\n)\nrunpy.run_path(TARGET)\n'
    )

    def ts(minutes_ago):
        return (NOW - timedelta(minutes=minutes_ago)).isoformat()

    def job(**kw):
        base = dict(id="j1", name="RTD Auto-Fulfill", enabled=True,
                    no_agent=True, script="rtd_auto_fulfill.py",
                    workdir=ROOT, prompt="",
                    schedule={"kind": "interval", "minutes": 30})
        base.update(kw)
        return base

    HEALTHY_EXEC = {"j1": [("completed", ts(10)), ("failed", ts(400)),
                           ("completed", ts(45))]}

    def run(jobs, execs=None, files=None, dirs=None, jobs_exc=None,
            exec_exc=None, home=HOME, hb="__frisch__", hb_err=None):
        files = {nk(LOADER): LOADER_TEXT, nk(TARGET): ""} if files is None \
            else {nk(k): v for k, v in files.items()}
        dirs = {nk(ROOT)} if dirs is None else {nk(d) for d in dirs}
        execs = HEALTHY_EXEC if execs is None else execs
        if hb == "__frisch__":
            hb = ts(10)

        def fake_jobs(_home):
            if jobs_exc:
                raise Unmessbar(jobs_exc)
            return jobs

        def fake_execs(_home):
            if exec_exc:
                raise Unmessbar(exec_exc)
            return execs

        def fake_hb():
            return (None, hb_err) if hb_err else (hb, None)

        keep = {k: g[k] for k in ("io_home", "io_read_jobs",
                                  "io_read_executions", "io_isfile",
                                  "io_isdir", "io_read_text", "io_now",
                                  "io_read_pipeline_hb")}
        g["io_home"] = lambda: home
        g["io_read_jobs"] = fake_jobs
        g["io_read_executions"] = fake_execs
        g["io_isfile"] = lambda p: nk(p) in files
        g["io_isdir"] = lambda p: nk(p) in dirs
        g["io_read_text"] = lambda p: files[nk(p)]
        g["io_now"] = lambda: NOW
        g["io_read_pipeline_hb"] = fake_hb
        buf = _io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = main()
        except Exception as exc:  # noqa: BLE001
            buf.write(f"\nTraceback-ersatz: {exc!r}")
            rc = 99
        finally:
            g.update(keep)
        return rc, buf.getvalue()

    def word(out):
        for line in out.splitlines():
            if line.startswith("ERGEBNIS:"):
                # exaktes erstes Token (Merkregel Ticket 19)
                return line.split()[1]
        return "(kein Ergebniswort)"

    def clean(out):
        return "Traceback" not in out

    print("== cron_health_audit --selftest (Fault Injection, offline) ==")

    rc, out = run([job()])
    t(rc == 0 and word(out) == "CRON_HEALTH_OK",
      "gesunder Geldpfad-Job -> gruen", f"rc={rc} {word(out)}")
    t("Geltungsbereich" in out, "Geltungsbereich wird gedruckt (Ticket 18)")
    t(clean(out), "kein Traceback im Gruen-Fall")

    # -- leere Zielmenge ---------------------------------------------------
    rc, out = run([job(script=None, prompt="irgendwas")])
    t(rc == 1 and word(out) == "CRON_HEALTH_DEFEKT"
      and "KEIN Geldpfad-Job" in out and clean(out),
      "leere Zielmenge ist NICHT gruen (Ticket-16-Merkregel)",
      f"rc={rc} {word(out)}")

    rc, out = run([])
    t(rc == 1 and "KEIN Geldpfad-Job" in out and clean(out),
      "gar keine Jobs -> rot, nicht gruen", f"rc={rc} {word(out)}")

    # -- Bauform -----------------------------------------------------------
    rc, out = run([job(enabled=False)])
    t(rc == 1 and "enabled=False" in out and clean(out),
      "abgeschalteter Geldpfad-Job -> rot", f"rc={rc}")

    rc, out = run([job(no_agent=False)])
    t(rc == 1 and "no_agent=False" in out and clean(out),
      "agentengetriebener Traeger -> rot (Ticket-22-Ursache)", f"rc={rc}")

    # -- Dateien -----------------------------------------------------------
    rc, out = run([job()], files={nk(TARGET): ""})
    t(rc == 1 and "KEIN Geldpfad-Job" in out and clean(out),
      "Loader-Skript geloescht -> rot", f"rc={rc}")

    rc, out = run([job()], files={nk(LOADER): LOADER_TEXT})
    t(rc == 1 and "Zieldatei fehlt" in out and clean(out),
      "Repo-Zieldatei fehlt -> rot", f"rc={rc}")

    # ACHTUNG: os.path.join("Q:", "x") ergibt "Q:x" OHNE Separator (laufwerks-
    # relativ) - das matcht ABSPATH_RE nicht und machte diesen Rot-Fall im
    # ersten Anlauf still gruen. Separator explizit setzen.
    foreign = LOADER_TEXT.replace(ROOT, "Q:" + os.sep + "fremdes-repo")
    rc, out = run([job()], files={nk(LOADER): foreign, nk(TARGET): ""})
    t(rc == 1 and "fremdes Repo" in out and clean(out),
      "Loader zeigt auf fremdes Repo -> rot", f"rc={rc}")

    rc, out = run([job(workdir=None)])
    t(rc == 1 and "workdir nicht gesetzt" in out and clean(out),
      "workdir fehlt -> rot", f"rc={rc}")

    rc, out = run([job(workdir=os.path.join("Q:", "weg"))])
    t(rc == 1 and "workdir existiert nicht" in out and clean(out),
      "workdir zeigt ins Leere -> rot", f"rc={rc}")

    # -- Protokoll ---------------------------------------------------------
    # Ticket-22-Lage: der Job feuert stuendlich, wird aber jedes Mal VOR der
    # Pipeline abgebrochen (Spend-Protection) -> es gibt keinen Heartbeat.
    t22 = {"j1": [("failed", ts(i * 60)) for i in range(1, 144)]}
    rc, out = run([job()], execs=t22, hb_err="Pipeline-Heartbeat fehlt")
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT"
      and "Pipeline-Lauf nicht belegbar" in out and clean(out),
      "Ticket-22-Lage ohne Heartbeat -> unmessbar, NICHT gruen", f"rc={rc}")

    rc, out = run([job()], execs=t22, hb=ts(1200))
    t(rc == 1 and "Liefer-Pipeline meldete zuletzt vor" in out and clean(out),
      "Job feuert, Pipeline meldet seit 20 h nichts -> rot", f"rc={rc}")

    rc, out = run([job()], execs={"j1": []})
    t(rc == 1 and "0 Laeufe protokolliert" in out and clean(out),
      "Job hat nie gefeuert -> rot", f"rc={rc}")

    rc, out = run([job()], execs={"j1": [("completed", ts(3 * 1440))]})
    t(rc == 1 and "der Job feuert nicht" in out and clean(out),
      "letzter Lauf 3 Tage her -> rot (stille Stagnation)", f"rc={rc}")

    # -- Ticket 25: LATCH-Regression ---------------------------------------
    # Genau die reale Lage von 2026-08-07: der Job feuert alle 30 min, die
    # Pipeline liefert (frischer Heartbeat), aber seit 1031 min steht kein
    # 'completed' mehr in der DB - weil dieses Audit den Job rot macht.
    latch = {"j1": [("failed", ts(m)) for m in (5, 35, 65, 95, 125)]
                   + [("completed", ts(1031))]}
    rc, out = run([job()], execs=latch)
    t(rc == 0 and word(out) == "CRON_HEALTH_OK" and clean(out),
      "LATCH: alte Laeufe rot + Pipeline liefert -> gruen (kein Selbstbezug)",
      f"rc={rc} {word(out)}")
    t("kein Kriterium, Selbstbezug" in out,
      "Job-Exitstatus wird ausdruecklich als INFO gekennzeichnet")

    # Gegenprobe: dieselbe Lage, aber die Pipeline meldet NICHT mehr ->
    # der Fix darf einen echten Lieferausfall nicht mitverstecken.
    rc, out = run([job()], execs=latch, hb=ts(1031))
    t(rc == 1 and "Liefer-Pipeline meldete zuletzt vor 1031 min" in out
      and clean(out),
      "LATCH-Gegenprobe: Pipeline steht wirklich -> rot", f"rc={rc}")

    # -- Ticket 25: Scheduler-Stillstand vs Geldpfad-Defekt ----------------
    # Nachtabschaltung: KEIN Job lief 900 min, danach laeuft alles wieder.
    nacht = {"j1": [("completed", ts(900)), ("completed", ts(930))],
             "j2": [("completed", ts(905)), ("completed", ts(935))]}
    rc, out = run([job()], execs=nacht, hb=ts(900))
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT"
      and "nicht dem Geldpfad anlastbar" in out and clean(out),
      "globaler Stillstand -> unmessbar, kein Defekt-Claim gegen den Geldpfad",
      f"rc={rc} {word(out)}")

    # Gegenprobe: NUR der Geldpfad-Job schweigt, andere laufen weiter -> rot.
    allein = {"j1": [("completed", ts(900))],
              "j2": [("completed", ts(m)) for m in (5, 35, 65, 95, 300, 600)]}
    rc, out = run([job()], execs=allein, hb=ts(900))
    t(rc == 1 and "der Job feuert nicht" in out and clean(out),
      "nur der Geldpfad schweigt, andere Jobs laufen -> rot", f"rc={rc}")

    # Stillstand jenseits der 24-h-Zusage ist sehr wohl ein Defekt.
    lang = {"j1": [("completed", ts(30)), ("completed", ts(1600))]}
    rc, out = run([job()], execs=lang)
    t(rc == 1 and "24-h-Zusage aus agb.html § 3 real ungedeckt" in out
      and clean(out),
      "Stillstand > 1440 min -> rot (Zusage war real ungedeckt)", f"rc={rc}")

    # Leeres Fenster: KEIN Lauf irgendeines Jobs liegt in den letzten 2880
    # min. Dann ist der Stillstand NICHT bestimmbar - eine gedruckte "0 min"
    # waere eine erfundene Null (Merkregel: nicht messbar != gemessen 0).
    leer = {"j1": [("completed", ts(5000))]}
    rc, out = run([job()], execs=leer, hb=ts(5000))
    t(rc == 1 and "Scheduler-Stillstand" not in out
      and "der Job feuert nicht" in out and clean(out),
      "leeres Stillstands-Fenster erfindet keine 0 (keine Aussage)",
      f"rc={rc}")

    # -- Ticket 25: Heartbeat-Randfaelle -----------------------------------
    rc, out = run([job()], hb_err="Pipeline-Heartbeat nicht parsebar: x")
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT" and clean(out),
      "kaputter Heartbeat -> unmessbar, nicht gruen", f"rc={rc} {word(out)}")

    rc, out = run([job()], hb="voellig-kein-datum")
    t(rc == 2 and "Zeitstempel unlesbar" in out and clean(out),
      "Heartbeat mit Muell-Zeitstempel -> unmessbar", f"rc={rc}")

    # Echter Defekt schlaegt Unmessbarkeit (Konvention Ticket 17/19).
    rc, out = run([job(enabled=False)], hb_err="Heartbeat fehlt")
    t(rc == 1 and word(out) == "CRON_HEALTH_DEFEKT" and clean(out),
      "Defekt + fehlender Heartbeat -> DEFEKT gewinnt", f"rc={rc} {word(out)}")

    rc, out = run([job(schedule={"kind": "interval", "minutes": 2880})],
                  execs={"j1": [("completed", ts(30))]})
    t(rc == 1 and "24-h-Zusage" in out and clean(out),
      "Intervall > 24 h -> rot (agb.html § 3 ungedeckt)", f"rc={rc}")

    # -- Unmessbarkeit -----------------------------------------------------
    rc, out = run([job()], jobs_exc="jobs.json nicht lesbar: kaputt")
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT" and clean(out),
      "jobs.json unlesbar -> UNGEPRUEFT, kein Defekt-Claim", f"rc={rc}")

    rc, out = run([job()], exec_exc="executions.db fehlt")
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT" and clean(out),
      "Protokoll unlesbar -> UNGEPRUEFT", f"rc={rc}")

    rc, out = run([job(schedule=None)])
    t(rc == 2 and "Intervall nicht ableitbar" in out and clean(out),
      "unbekannte Schedule-Form -> UNGEPRUEFT, nicht gruen", f"rc={rc}")

    rc, out = run([job(no_agent=False)], exec_exc="executions.db fehlt")
    t(rc == 1 and word(out) == "CRON_HEALTH_DEFEKT" and clean(out),
      "echter Defekt schlaegt Unmessbarkeit (Ticket 17)", f"rc={rc}")

    # -- Klassifikation ----------------------------------------------------
    rc, out = run([job(script="weg.py", prompt="ruft request_delivery auf")],
                  files={nk(TARGET): ""})
    t(rc == 1 and "Klassifikation offen" in out
      and "KEIN Geldpfad-Job" in out and clean(out),
      "fehlendes Skript mit Geldpfad-Prompt -> offen + leere Menge rot",
      f"rc={rc} {word(out)}")

    rc, out = run([job(script="weg.py", prompt="nichts damit zu tun")],
                  files={nk(TARGET): ""})
    t(rc == 1 and "kein Geldpfad" in out and clean(out),
      "fremdes fehlendes Skript -> nur protokolliert, nicht als Traeger",
      f"rc={rc}")

    rc, out = run([job(id="agent", script=None, no_agent=False,
                       prompt="lies scripts/request_delivery/x.md"), job()])
    t(rc == 0 and "Nebentraeger" in out and word(out) == "CRON_HEALTH_OK",
      "agentengetriebener Job zaehlt als Nebentraeger, nicht als Traeger",
      f"rc={rc} {word(out)}")

    # -- zwei Traeger ------------------------------------------------------
    # Ticket 25: "0 completed" ist KEIN Defekt-Kriterium mehr (Selbstbezug).
    # Beim zweiten Traeger kommt hinzu, dass es nur EINEN Heartbeat gibt ->
    # [B] kann nicht sagen, WER geliefert hat. Die ehrliche Antwort ist
    # UNGEPRUEFT MIT GENANNTEM GRUND - nicht gruen und kein Defekt-Claim.
    two = {"j1": HEALTHY_EXEC["j1"], "j2": [("failed", ts(10))]}
    rc, out = run([job(), job(id="j2", name="Zweiter")], execs=two)
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT"
      and "nur EIN Pipeline-Heartbeat" in out
      and "nicht traegerscharf" in out and clean(out),
      "zweiter Traeger: [B] nicht traegerscharf -> UNGEPRUEFT mit Grund",
      f"rc={rc} {word(out)}")

    # Die Maskierungs-Schutzwirkung bleibt auf Kriterium [A] erhalten, denn
    # DAS ist traegerscharf: schweigt der zweite Traeger wirklich, muss der
    # gesunde erste ihn nicht verdecken duerfen.
    stumm = {"j1": HEALTHY_EXEC["j1"],
             "j2": [("completed", ts(1400))]}
    rc, out = run([job(), job(id="j2", name="Zweiter")], execs=stumm)
    t(rc == 1 and word(out) == "CRON_HEALTH_DEFEKT"
      and "j2" in out and "der Job feuert nicht" in out and clean(out),
      "gesunder Traeger maskiert wirklich stummen zweiten nicht ([A])",
      f"rc={rc} {word(out)}")

    # -- Ergebniswort exakt ------------------------------------------------
    rc, out = run([job()])
    t(word(out) == "CRON_HEALTH_OK" and "CRON_HEALTH_DEFEKT" not in out,
      "Ergebniswort exakt (kein Praefix-Treffer, Ticket 19)")

    ok = sum(1 for c, _ in results if c)
    print(f"\nSELFTEST {'OK' if ok == len(results) else 'FEHLGESCHLAGEN'}: "
          f"{ok}/{len(results)}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
