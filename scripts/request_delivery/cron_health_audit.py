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

import collections
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
    """job_id -> Liste (status, timestamp-string, gestartet). Read-only.

    Ticket 28: das dritte Feld trennt einen Lauf, der WIRKLICH GESTARTET ist
    (started_at gesetzt), von einem bloss BEANSPRUCHTEN (status='claimed',
    started_at=NULL). MEASURED 2026-08-10 01:45Z gegen die echte executions.db:
    der Traeger bfb63346d942 hatte 219 Zeilen, davon 2 ohne started_at - und
    genau so eine Zeile war die letzte, als das Audit Falsch-Rot meldete.
    NACHGEMESSEN 2026-08-10 06:20Z (Momentaufnahme, die DB waechst): 222 Zeilen
    des Traegers, davon 1 ohne started_at (repo-weit 2). Die Zahlen sind
    datiert, nicht dauerhaft - der Ausfallmodus ist es, worauf es ankommt. Ein Lauf,
    der nie startete, kann keinen Pipeline-Heartbeat schreiben; ihn als
    verpasste Gelegenheit zu zaehlen reproduziert das Falsch-Rot exakt.
    """
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
                "finished_at), started_at FROM executions"
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise Unmessbar(f"executions.db nicht lesbar: {exc}") from exc
    for job_id, status, ts, started_at in rows:
        out.setdefault(job_id, []).append((status, ts, started_at is not None))
    return out


def row_parts(row):
    """(status, ts, gestartet) aus einer Protokollzeile.

    Ticket 28: Alt-Form (status, ts) bleibt lesbar und gilt als GESTARTET -
    so bedeuten die 57 bestehenden Selftest-Faelle weiterhin genau das, was
    sie bisher bedeuteten (echte Laeufe), und nur die neuen Faelle setzen das
    dritte Feld. Der PRODUKTIVE Leser oben liefert es immer mit; dass er das
    tut, prueft ein eigener Selftest-Fall gegen eine echte SQLite-Datei
    (Merkregel: neuer Parameter mit Default = stiller Ausfall).
    """
    if len(row) >= 3:
        return row[0], row[1], bool(row[2])
    return row[0], row[1], True


def io_read_signale(home):
    """job_id -> Liste (status, error-Text). Read-only, WAL-schonend.

    Ticket 27: getrennt von io_read_executions(), damit die GETESTETE
    Urteilslogik unveraendert bleibt - diese Zeilen sind reine INFO und
    duerfen nie in ein Urteil einfliessen (Latch-Regel, Ticket 25).
    """
    path = os.path.join(home, "cron", "executions.db")
    if not os.path.isfile(path):
        raise Unmessbar(f"executions.db fehlt: {path}")
    uri = "file:///" + path.replace("\\", "/") + "?mode=ro"
    out = {}
    try:
        con = sqlite3.connect(uri, uri=True, timeout=10)
        try:
            rows = con.execute(
                "SELECT job_id, status, COALESCE(error, '') FROM executions"
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise Unmessbar(f"executions.db nicht lesbar: {exc}") from exc
    for job_id, status, err in rows:
        out.setdefault(job_id, []).append((status, err))
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


def global_stillstand(execs, now, bekannte_ids=None):
    """Groesste Zeitspanne im Fenster, in der KEIN EINZIGER Job gefeuert hat.

    Trennt \"der Geldpfad-Job ist tot\" von \"der ganze Scheduler stand\"
    (Rechner/Gateway aus). Ohne diese Trennung wird eine Nachtabschaltung als
    Geldpfad-Defekt gemeldet - MEASURED 2026-08-07: 15 h ohne einen einzigen
    Lauf irgendeines Jobs, danach 5x CRON_HEALTH_DEFEKT gegen eine gesunde
    Pipeline. -> (Minuten|None, Zahl ignorierter Fremdzeilen).

    Ticket 27: gezaehlt werden NUR Laeufe von Jobs, die in jobs.json wirklich
    stehen. Eine verwaiste Zeile - geloeschter Job oder eine Wegwerf-Sonde, die
    per source='direct' in executions.db geschrieben wurde (MEASURED
    2026-08-08: job_id 't27probe0001', 17:51, exit 3) - sieht sonst aus wie
    Scheduler-Aktivitaet und VERKLEINERT die gemessene Luecke. Fehlerrichtung
    = Falsch-Gruen genau bei Ausfallmodus C (Scheduler/Rechner tot), also die
    teure Richtung. Bleibt nach dem Filter nichts uebrig, ist das Ergebnis
    None (\"keine Aussage\"), NICHT 0.
    """
    if not execs:
        return None, 0
    grenze = now - timedelta(minutes=STILLSTAND_FENSTER_MIN)
    stamps = []
    fremd = 0
    for jid, rows in execs.items():
        if bekannte_ids is not None and jid not in bekannte_ids:
            fremd += len(rows)
            continue
        for row in rows:
            t = parse_ts(row_parts(row)[1])
            if t and t >= grenze:
                stamps.append(t)
    if not stamps:
        return None, fremd     # nichts im Fenster -> keine Aussage (nicht 0!)
    stamps.sort()
    # Nur echte Luecken ZWISCHEN Laeufen und die Luecke bis jetzt zaehlen.
    # Der Fensterrand zaehlt NICHT - sonst meldet eine frische DB Stillstand.
    luecke = (now - stamps[-1]).total_seconds() / 60.0
    for a, b in zip(stamps, stamps[1:]):
        luecke = max(luecke, (b - a).total_seconds() / 60.0)
    return luecke, fremd


# -- Ticket 27, Hauptfrage: WACH-UHR VERWORFEN (2026-08-10) ---------------
# Ein Vortick hatte hier wach_minuten() stehen: statt Wanduhr-Alter sollten
# nur "Minuten mit belegbar laufendem Scheduler" gegen die Toleranz gehalten
# werden, damit eine Nachtabschaltung GRUEN statt UNGEPRUEFT ergibt.
# NEU AUSGEFUEHRT statt uebernommen (Merkregel) -> der committete Selftest war
# damit ROT (50/57). Vier der sieben roten Faelle waren FALSCH-GRUEN auf dem
# Geldpfad, also die teuerste Fehlerrichtung:
#   * Heartbeat 1031 min alt, Job feuert alle 30 min -> rc=0: Lieferung tot,
#     Audit gruen (Wach-Summe 125 min < Toleranz 180 min).
#   * nur der Geldpfad schweigt 900 min, ein anderer Job laeuft -> rc=0.
#   * ein wirklich stummer zweiter Traeger wurde vom gesunden ersten maskiert.
#   * Geisterzeilen fremder job_ids lieferten das Wach-Alibi, weil main() den
#     Parameter bekannte_ids NIE durchreichte (Wiring-Defekt: Funktion da,
#     Aufrufer setzt sie nicht).
# Entwurfsfehler: die Wach-Summe entsteht aus FREMDEN Laeufen, ist bei duenner
# Beleglage klein, und "wenig Wachzeit" fiel in den GRUEN-Zweig statt in
# "unmessbar". Bis ein Entwurf ohne Falsch-Gruen vorliegt, urteilt wieder der
# stillstand_deckt-Test aus Ticket 25 (Nachtabschaltung -> UNGEPRUEFT).
# Belege: tickets/27-signalkanal-defekt-vs-unmessbar.md, Nachfolger Ticket 28.


# -- Ticket 27: den einzigen Signalkanal lesbar machen ---------------------
# ZWEITE MESSUNG 2026-08-09 (_probe_signalkanal_t27.py / _probe_signalzeit_t27.py,
# gegen die echte executions.db): von den 148 'failed'-Zeilen des Geldpfad-
# Traegers sind nur 8 ein SKRIPT-Urteil (7x exit 1, 1x exit 2). 136 sind
# "RuntimeError: Skipped to prevent unintended spend" - der Runner brach VOR
# dem Skript ab, das Urteil kam nie zustande; letzte solche Zeile
# 2026-08-06T05:04, also Alt-Bestand der Agenten-Aera. Diese Klasse darf
# deshalb NICHT als Skript-Defekt gelesen werden - sie sagt ueber den
# Geldpfad genau nichts.
# MEASURED 2026-08-09 gegen die echte executions.db: der Runner kennt fuer
# beendete Laeufe nur 'completed' / 'failed' (+ 'unknown', das er NUR bei
# Scheduler-Neustart setzt) - ein rc=1 (Defekt) und ein rc=3 (unmessbar)
# liegen als IDENTISCHE 'failed'-Zeile in der DB. Der Exitcode ueberlebt
# aber WOERTLICH im error-Text ("Script exited with code N"), MEASURED fuer
# die Codes 1, 2 und 3. Der Kanal trennt beides also - nur las es niemand.
# Diese Funktion ist der Leser. Reine INFO: sie faellt NIE ein Urteil.
EXIT_RE = re.compile(r"^Script exited with code (\d+)")

# Konvention des Geldpfads. MEASURED 2026-08-09: in der ganzen DB kommen genau
# die Codes 1 (166x), 2 (73x) und 3 (1x) vor - kein weiterer. 2 und 3 heissen
# beide "unmessbar": 2 in den Verifikations-Skripten und im Audit selbst,
# 3 in cron_auto_fulfill.py/rtd_health_watchdog.py.
SIGNAL_KONVENTION = {
    1: "DEFEKT (exit 1)",
    2: "unmessbar (exit 2)",
    3: "unmessbar (exit 3)",
    4: "Nebenring defekt, Geldpfad NICHT betroffen (exit 4)",
}
# Runner-Abbruch: das Skript lief NIE, es gibt kein Urteil ueber den Geldpfad.
RUNNER_ABBRUCH = (
    ("Skipped to prevent unintended spend", "Spend-Guard"),
    ("Model '", "Modell fehlt"),
    ("getaddrinfo failed", "DNS/Netz"),
    ("Context length exceeded", "Kontext"),
    ("HTTP 429", "Rate-Limit"),
)


def dekodiere_signale(rows):
    """[(status, error)] -> (Counter der Klassen, Liste auffaelliger Codes).

    Klassen sind bewusst grob und erschoepfend - jede Zeile landet in genau
    einer, sonst taeuscht die Summe Vollstaendigkeit vor (Teil-Vollstaen-
    digkeits-Falle, Ticket 13/15/17/20).
    """
    klassen = collections.Counter()
    auffaellig = []
    for status, err in rows:
        err = err or ""
        if status == "completed":
            klassen["completed"] += 1
            continue
        m = EXIT_RE.match(err)
        if m:
            code = int(m.group(1))
            name = SIGNAL_KONVENTION.get(code)
            if name is None:
                name = f"KONVENTIONSBRUCH (exit {code})"
                auffaellig.append(code)
            klassen[name] += 1
        elif status == "unknown":
            klassen["Scheduler-Neustart (kein Skript-Urteil)"] += 1
        elif status in ("claimed", "running"):
            klassen["laeuft/haengt"] += 1
        else:
            grund = next((g for marker, g in RUNNER_ABBRUCH if marker in err),
                         "sonstiges")
            klassen[f"RUNNER-ABBRUCH {grund} (Skript lief NIE)"] += 1
    return klassen, auffaellig


def signal_zeile(rows):
    """Eine INFO-Zeile mit der dekodierten Aufschluesselung, oder None."""
    if not rows:
        return None
    klassen, _ = dekodiere_signale(rows)
    teile = [f"{v}x {k}" for k, v in klassen.most_common()
             if k != "completed"]
    if not teile:
        return "      davon nicht-completed: keine"
    return "      dekodiert (Ticket 27, INFO): " + ", ".join(teile)


def check_traeger(job, path, text, execs, now, defects, unknown, out,
                  hb_ts=None, hb_err=None, stillstand=None, signale=None,
                  signal_err=None):
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
    parts = [row_parts(r) for r in rows]
    done = [parse_ts(ts) for st, ts, _ in parts if st == "completed"]
    done = [d for d in done if d]
    attempts = [parse_ts(ts) for _, ts, _ in parts]
    attempts = [a for a in attempts if a]
    # Ticket 28: Laeufe, die WIRKLICH gestartet sind (started_at gesetzt).
    starts = [parse_ts(ts) for _, ts, gestartet in parts if gestartet]
    starts = [s for s in starts if s]
    n_nie_gestartet = sum(1 for _, _, gestartet in parts if not gestartet)
    n_fail = sum(1 for st, _, _ in parts if st not in ("completed",))
    out.append(f"      Laeufe    = {len(rows)} gesamt / "
               f"{len(done)} completed / {n_fail} nicht-completed")
    if n_fail:
        # Ticket 27: die Zahl allein wirft echte Defekte, unmessbare Laeufe
        # und Runner-Abbrueche (Skript lief nie) in EINEN Topf. Hier wird sie
        # aufgeschluesselt - INFO, kein Urteil.
        if signale is None:
            out.append("      dekodiert (Ticket 27, INFO): NICHT GELESEN "
                       f"({signal_err or 'kein Grund genannt'})")
        else:
            zeile = signal_zeile(signale.get(jid, []))
            out.append(zeile if zeile else
                       "      dekodiert (Ticket 27, INFO): keine "
                       "Protokollzeilen zu diesem Job")
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
    if toleranz is None or hb_age <= toleranz:
        return

    # -- Ticket 28: VERPASSTE GELEGENHEITEN statt gezaehlter Zeit ----------
    # Alt (Ticket 25): entlastet wurde nur, wenn der globale Stillstand das
    # Heartbeat-Alter auf die MINUTE deckte (stillstand >= hb_age - 1).
    # MEASURED 2026-08-10: Stillstand 784 min, Heartbeat 793 min alt - 8 min
    # Differenz genuegten fuer einen Defekt-Claim gegen eine kerngesunde
    # Lieferung (der Heartbeat wurde 9 min VOR Beginn der Abschaltung
    # geschrieben, das ist der Normalfall, nicht die Ausnahme).
    # Neu wird nicht Zeit gegen Zeit gehalten, sondern gefragt: hatte die
    # Pipeline seit dem Heartbeat ueberhaupt eine GELEGENHEIT zu melden?
    # Gelegenheit = ein eigener Lauf, der WIRKLICH GESTARTET ist. Eine Zeile
    # 'claimed' mit started_at=NULL ist keine - sie kann per Konstruktion
    # keinen Heartbeat schreiben (genau die Zeile stand im realen Fall oben).
    verpasst = [s for s in starts if (s - hb).total_seconds() > 60]
    nie_gestartet_seit_hb = sum(
        1 for _, ts, gestartet in parts
        if not gestartet and (parse_ts(ts) or hb) > hb)
    if verpasst:
        # Deckt Falsch-Gruen-Fall 1 aus Ticket 27 ab: Job feuert alle 30 min,
        # Pipeline meldet seit 1031 min nicht -> die Lieferung steht wirklich.
        defects.append(
            f"{tag}: Liefer-Pipeline meldete zuletzt vor {hb_age:.0f} min, "
            f"erlaubt waeren {toleranz:.0f} min - seither sind "
            f"{len(verpasst)} Laeufe wirklich GESTARTET, ohne zu melden "
            f"- die Lieferung steht")
        return
    if hb_age > MAX_PROMISE_MIN:
        # Harte Grenze, damit "keine Gelegenheit" kein Dauerfreibrief wird:
        # jenseits der 24-h-Zusage aus agb.html § 3 ist die Lieferung
        # nachweislich ueberfaellig - egal, wer sie verhindert hat.
        defects.append(
            f"{tag}: Liefer-Pipeline meldete zuletzt vor {hb_age:.0f} min "
            f"(> {MAX_PROMISE_MIN} min) - seither ist zwar kein Lauf "
            f"gestartet ({nie_gestartet_seit_hb} beansprucht/nie gestartet), "
            f"aber die 24-h-Zusage aus agb.html § 3 ist damit real ungedeckt")
        return
    stillstand_txt = (f"{stillstand:.0f} min Scheduler-Stillstand"
                      if stillstand is not None else "Stillstand unbekannt")
    unknown.append(
        f"{tag}: Pipeline meldete zuletzt vor {hb_age:.0f} min - seither ist "
        f"KEIN eigener Lauf wirklich GESTARTET "
        f"({nie_gestartet_seit_hb} beansprucht/nie gestartet, "
        f"{stillstand_txt}), sie hatte also keine Gelegenheit zu melden "
        f"-> nicht dem Geldpfad anlastbar")


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
    attempts = [parse_ts(row_parts(r)[1]) for r in rows]
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
    # Ticket 27, Nebenfrage B: ZWEI Defektlisten statt einer. Bis hierher
    # schrieb check_waechter() in dieselbe Liste wie check_traeger() - ein
    # toter ZWEITER RING erzeugte damit rc=1, und Etappe [3] in
    # cron_auto_fulfill machte daraus RTD_FULFILL_DEFEKT: ein Defekt-Vorwurf
    # gegen den GELDPFAD, obwohl die Lieferung sauber lief (real geschehen
    # 2026-08-08 05:41). Das ist die Klasse "Nebenmessung vergiftet das
    # Hauptsignal" aus Ticket 24. Getrennt wird nach BETROFFENEM, nicht nach
    # Schweregrad: 'defects' = Geldpfad, 'ring_defects' = Ueberwachung.
    defects, ring_defects, unknown, out = [], [], [], []

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

    # Ticket 27: die error-Texte separat lesen (reine INFO, nie ein Urteil).
    # MEASURED 2026-08-09: die Leserfunktion existierte schon, main() rief sie
    # NIE auf - der Live-Lauf druckte deshalb dauerhaft "nicht lesbar", obwohl
    # die Texte lesbar sind. Selftest gruen, Produktivpfad tot. Deshalb wird
    # der Grund jetzt mitgefuehrt: "nicht gelesen" != "nicht lesbar".
    try:
        signale = io_read_signale(home)
        signal_err = None
    except Unmessbar as exc:
        signale = None
        signal_err = str(exc)

    traeger, waechter, neben, offen, info = classify(jobs, home)
    n_en = sum(1 for j in jobs if j.get("enabled"))
    print(f"Jobs            : {len(jobs)} gesamt, {n_en} enabled")
    print(f"Geldpfad-Traeger (abgeleitet, nicht hartkodiert): {len(traeger)}")
    print(f"Waechter (2. Ring, Ticket 25): {len(waechter)}")

    now = io_now()
    # Ticket 27: nur Jobs zaehlen, die jobs.json wirklich kennt (Fremd-/
    # Sondenzeilen in executions.db duerfen keinen Stillstand zudecken).
    bekannte_ids = {j.get("id") for j in jobs}
    stillstand, fremdzeilen = (global_stillstand(execs, now, bekannte_ids)
                               if execs else (None, 0))
    hb_ts, hb_err = io_read_pipeline_hb()
    if fremdzeilen:
        print(f"Protokollzeilen ohne Job in jobs.json (ignoriert, Ticket 27): "
              f"{fremdzeilen}")
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
                      hb_ts=hb_ts, hb_err=hb_err, stillstand=stillstand,
                      signale=signale, signal_err=signal_err)
    for job, path, text in waechter:
        check_waechter(job, path, text, execs, now, ring_defects, unknown, out,
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
        print(f"DEFEKTE GELDPFAD ({len(defects)}):")
        for d in defects:
            print(f"  ! {d}")
    if ring_defects:
        print(f"DEFEKTE NEBENRING ({len(ring_defects)}) - Ueberwachung, "
              f"NICHT die Lieferung:")
        for d in ring_defects:
            print(f"  !~ {d}")
    if unknown:
        print(f"UNMESSBAR ({len(unknown)}):")
        for u in unknown:
            print(f"  ? {u}")

    # Reihenfolge: echter Defekt > unmessbar > OK (Merkregel Ticket 17/19)
    if defects:
        print(f"ERGEBNIS: CRON_HEALTH_DEFEKT ({len(defects)} Defekt(e), "
              f"{len(traeger)} Geldpfad-Traeger geprueft)")
        return 1
    # Ticket 27: ein toter Nebenring ist ein GEMESSENER Defekt - also weder
    # gruen (rc=0 waere Falsch-Gruen auf die Ueberwachung) noch "unmessbar"
    # (rc=2 waere gelogen, er ist ja gemessen) noch ein Geldpfad-Vorwurf
    # (rc=1 waere Falsch-Rot auf die Lieferung). Er bekommt die eigene Zahl.
    if ring_defects:
        print(f"ERGEBNIS: CRON_HEALTH_NEBENRING_DEFEKT ({len(ring_defects)} "
              f"Defekt(e) am 2. Ring - die Lieferung selbst ist unauffaellig)")
        return 4
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
            exec_exc=None, home=HOME, hb="__frisch__", hb_err=None,
            signale=None, signale_exc=None):
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

        def fake_signale(_home):
            if signale_exc:
                raise Unmessbar(signale_exc)
            return {} if signale is None else signale

        def fake_hb():
            return (None, hb_err) if hb_err else (hb, None)

        keep = {k: g[k] for k in ("io_home", "io_read_jobs",
                                  "io_read_executions", "io_isfile",
                                  "io_isdir", "io_read_text", "io_now",
                                  "io_read_pipeline_hb", "io_read_signale")}
        g["io_home"] = lambda: home
        g["io_read_jobs"] = fake_jobs
        g["io_read_executions"] = fake_execs
        g["io_read_signale"] = fake_signale
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
    # Ticket 27: j2 muss in jobs.json STEHEN, sonst zaehlt sein Puls nicht
    # (Fremdzeilen werden ignoriert) - sonst prueft der Fall etwas anderes,
    # als sein Name sagt. script=None + Prompt ohne Geldpfad-Token => von
    # classify() folgenlos uebersprungen, aber als Job bekannt.
    anderer = job(id="j2", name="irgendein anderer Job", script=None,
                  prompt="taeglicher Report")
    # Nachtabschaltung: KEIN Job lief 900 min, danach laeuft alles wieder.
    nacht = {"j1": [("completed", ts(900)), ("completed", ts(930))],
             "j2": [("completed", ts(905)), ("completed", ts(935))]}
    rc, out = run([job(), anderer], execs=nacht, hb=ts(900))
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT"
      and "nicht dem Geldpfad anlastbar" in out and clean(out),
      "globaler Stillstand -> unmessbar, kein Defekt-Claim gegen den Geldpfad",
      f"rc={rc} {word(out)}")

    # Gegenprobe: NUR der Geldpfad-Job schweigt, andere laufen weiter -> rot.
    allein = {"j1": [("completed", ts(900))],
              "j2": [("completed", ts(m)) for m in (5, 35, 65, 95, 300, 600)]}
    rc, out = run([job(), anderer], execs=allein, hb=ts(900))
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

    # -- Ticket 27: Fremdzeilen in executions.db duerfen nicht mitzaehlen ---
    # Wegwerf-Sonden/geloeschte Jobs schreiben Zeilen mit einer job_id, die
    # jobs.json nicht kennt (MEASURED 2026-08-08: 't27probe0001', source=
    # 'direct'). Sie faelschen den Scheduler-Puls in BEIDE Richtungen.
    geist_nacht = {"j1": [("completed", ts(900)), ("completed", ts(930))],
                   "zzz_sonde": [("failed", ts(m)) for m in (5, 35, 65)]}
    rc, out = run([job()], execs=geist_nacht, hb=ts(900))
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT"
      and "nicht dem Geldpfad anlastbar" in out and clean(out),
      "Fremdzeilen tarnen keine Nachtabschaltung (kein Falsch-Rot)",
      f"rc={rc} {word(out)}")
    t("Protokollzeilen ohne Job in jobs.json (ignoriert, Ticket 27): 3" in out,
      "ignorierte Fremdzeilen werden gezaehlt und gedruckt")

    geist_lang = {"j1": [("completed", ts(30)), ("completed", ts(1600))],
                  "zzz_sonde": [("failed", ts(800))]}
    rc, out = run([job()], execs=geist_lang)
    t(rc == 1 and "24-h-Zusage aus agb.html § 3 real ungedeckt" in out
      and clean(out),
      "Fremdzeile deckt echten >1440-min-Stillstand nicht zu (kein "
      "Falsch-Gruen)", f"rc={rc}")

    nur_geist = {"zzz_sonde": [("completed", ts(5)), ("completed", ts(35))]}
    rc, out = run([job()], execs=nur_geist, hb=ts(5000))
    t(rc != 0 and "Scheduler-Stillstand" not in out and clean(out),
      "nur Fremdzeilen -> keine erfundene Stillstands-Zahl, nicht gruen",
      f"rc={rc} {word(out)}")

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

    # -- Ticket 27: Signalkanal dekodieren (durch die ECHTE main()) --------
    # Der Fall, an dem der Vortick scheiterte: die Leserfunktion existierte,
    # main() rief sie nie auf -> live stand dauerhaft "nicht lesbar" da,
    # obwohl die Texte lesbar sind. Diese Faelle laufen deshalb ALLE durch
    # main(), nie gegen dekodiere_signale() direkt.
    misch = {"j1": [("completed", ts(10)), ("failed", ts(40)),
                    ("failed", ts(70)), ("failed", ts(100)),
                    ("failed", ts(130)), ("unknown", ts(160))]}
    sig = {"j1": [
        ("completed", ""),
        ("failed", "Script exited with code 1\nstdout:\n[1] Pipeline"),
        ("failed", "Script exited with code 3\nstdout:\n[2] Live-Check"),
        ("failed", "RuntimeError: Skipped to prevent unintended spend: "
                   "global inference cost limit"),
        ("failed", "Script exited with code 7\nstdout:\n?"),
        ("unknown", "Scheduler restarted after this execution's owner"),
    ]}
    rc, out = run([job()], execs=misch, signale=sig)
    t("1x DEFEKT (exit 1)" in out and "1x unmessbar (exit 3)" in out
      and clean(out),
      "DEFEKT und unmessbar sind im Protokoll UNTERSCHEIDBAR (Ticket 27)",
      f"rc={rc}")
    t("NICHT GELESEN" not in out and "nicht lesbar" not in out,
      "Verdrahtung: main() liest die error-Texte wirklich "
      "(Regression 2026-08-09)")
    t("1x RUNNER-ABBRUCH Spend-Guard (Skript lief NIE)" in out,
      "Runner-Abbruch wird NICHT als Skript-Defekt gelesen (136 reale Zeilen)")
    t("1x KONVENTIONSBRUCH (exit 7)" in out,
      "unbekannter Exitcode heisst Konventionsbruch, nicht stillschweigend ok")
    t("1x Scheduler-Neustart (kein Skript-Urteil)" in out,
      "Scheduler-Neustart ist kein Skript-Urteil")
    t(word(out) == "CRON_HEALTH_OK",
      "die Dekodierung ist INFO und aendert das Urteil NICHT (Latch-Regel)",
      f"{word(out)}")

    # nicht lesbar != nicht gelesen: der Grund muss im Klartext dastehen,
    # und Unlesbarkeit darf keinen Defekt-Claim erzeugen.
    rc, out = run([job()], execs=misch, signale_exc="executions.db gesperrt")
    t("NICHT GELESEN (executions.db gesperrt)" in out
      and word(out) == "CRON_HEALTH_OK" and clean(out),
      "unlesbare error-Texte: Grund benannt, kein Defekt-Claim",
      f"rc={rc} {word(out)}")

    # -- Ticket 27, Nebenfrage B: Nebenring-Defekt != Geldpfad-Defekt ------
    # BEFUND 2026-08-09: check_waechter() hatte in 48 Selftest-Faellen NULL
    # Abdeckung - die gesamte Urteilslogik des 2. Rings war ungetestet, und
    # dass sie in dieselbe defects-Liste schrieb wie der Traeger, fiel keinem
    # Test auf. Genau diese Kopplung machte am 2026-08-08 05:41 den sauber
    # liefernden Geldpfad-Job rot.
    WD = os.path.join(HOME, "scripts", "rtd_health_watchdog.py")
    # Der Text muss request_delivery + cron_health_audit nennen, aber NICHT
    # das Fulfill-Token - sonst klassifiziert classify() ihn als Traeger.
    WD_TEXT = ('TARGET = os.path.join("request_delivery",\n'
               '                      "cron_health_audit.py")\n')

    def wd(**kw):
        base = dict(id="w1", name="RTD Cron Watchdog (2. Ring)", enabled=True,
                    no_agent=True, script="rtd_health_watchdog.py",
                    workdir=ROOT, prompt="",
                    schedule={"kind": "interval", "minutes": 30})
        base.update(kw)
        return base

    wd_files = {LOADER: LOADER_TEXT, TARGET: "", WD: WD_TEXT}

    # Gesunder Ring: er wird ueberhaupt als WAECHTER erkannt und stoert nicht.
    beide_ok = {"j1": [("completed", ts(10))], "w1": [("completed", ts(10))]}
    rc, out = run([job(), wd()], execs=beide_ok, files=wd_files)
    t(rc == 0 and word(out) == "CRON_HEALTH_OK" and "[WAECHTER]" in out
      and clean(out),
      "gesunder 2. Ring wird als WAECHTER klassifiziert und bleibt gruen",
      f"rc={rc} {word(out)}")

    # NUR der Ring ist defekt (abgeschaltet), die Lieferung laeuft sauber.
    rc, out = run([job(), wd(enabled=False)], execs=beide_ok, files=wd_files)
    t(rc == 4 and word(out) == "CRON_HEALTH_NEBENRING_DEFEKT" and clean(out),
      "nur der 2. Ring defekt -> eigener rc=4, KEIN Geldpfad-Defekt",
      f"rc={rc} {word(out)}")
    t("DEFEKTE NEBENRING" in out and "DEFEKTE GELDPFAD" not in out,
      "der Defekt wird dem Nebenring zugeschrieben, nicht dem Geldpfad")
    t("die Lieferung selbst ist unauffaellig" in out,
      "das Ergebniswort sagt ausdruecklich, dass die Lieferung sauber ist")

    # Ring tot (0 Laeufe) - der klassische Fall vom 2026-08-08 05:41.
    nur_traeger = {"j1": [("completed", ts(10))]}
    rc, out = run([job(), wd()], execs=nur_traeger, files=wd_files)
    t(rc == 4 and word(out) == "CRON_HEALTH_NEBENRING_DEFEKT"
      and "hat aber nie gefeuert" in out and clean(out),
      "nie gefeuerter Waechter -> rc=4 statt Geldpfad-Vorwurf (Fall 08-08 05:41)",
      f"rc={rc} {word(out)}")

    # Beide defekt: der Geldpfad-Vorwurf hat Vorrang, er ist das teurere Signal.
    rc, out = run([job(enabled=False), wd(enabled=False)], execs=beide_ok,
                  files=wd_files)
    t(rc == 1 and word(out) == "CRON_HEALTH_DEFEKT" and clean(out),
      "Traeger UND Ring defekt -> Geldpfad gewinnt (rc=1), Ring geht nicht unter",
      f"rc={rc} {word(out)}")
    t("DEFEKTE NEBENRING" in out and "DEFEKTE GELDPFAD" in out,
      "beide Defektlisten werden gedruckt, auch wenn nur eine das rc bestimmt")

    # Ring-Defekt schlaegt 'unmessbar': gemessen ist mehr wert als nicht messbar.
    rc, out = run([job(), wd(enabled=False)], execs=beide_ok, files=wd_files,
                  hb_err="Heartbeat fehlt")
    t(rc == 4 and word(out) == "CRON_HEALTH_NEBENRING_DEFEKT" and clean(out),
      "gemessener Ring-Defekt schlaegt UNGEPRUEFT (Merkregel T17/19)",
      f"rc={rc} {word(out)}")

    # Die neue Zahl muss die Signal-Konvention kennen, sonst meldet der
    # Decoder sie als Konventionsbruch (Ticket 27, Hauptfrage).
    t(SIGNAL_KONVENTION.get(4, "").startswith("Nebenring defekt"),
      "exit 4 ist in der Signal-Konvention hinterlegt, kein Konventionsbruch",
      f"{SIGNAL_KONVENTION.get(4)}")

    # == Ticket 28: Falsch-Rot nach Abschaltung, ohne Falsch-Gruen ==========
    # Alle folgenden Faelle nutzen die 3-Tupel-Form (status, ts, gestartet).
    # Die 57 Faelle darueber bleiben 2-Tupel und bedeuten unveraendert
    # "wirklich gelaufen" (row_parts-Default) - deshalb muessen sie gruen
    # bleiben; sie sind die Messlatte, nicht dieser Block.

    # (1) DER KONSERVIERTE REALFALL, MEASURED 2026-08-10 01:45Z:
    #     Rechner 784 min aus, Heartbeat 793 min alt (9 min vor Beginn der
    #     Abschaltung geschrieben), letzte DB-Zeile 'claimed' mit
    #     started_at=NULL vor 9 min. Die alte Fassung meldete hier
    #     CRON_HEALTH_DEFEKT gegen eine kerngesunde Lieferung.
    real28 = {"j1": [("completed", ts(793), True),
                     ("completed", ts(823), True),
                     ("claimed", ts(9), False)]}
    rc, out = run([job()], execs=real28, hb=ts(793))
    t(rc != 1 and "die Lieferung steht" not in out and clean(out),
      "T28-Realfall (784/793/9 min, claimed+started_at=NULL): KEIN "
      "Defekt-Claim gegen den Geldpfad mehr", f"rc={rc} {word(out)}")
    t(word(out) == "CRON_HEALTH_UNGEPRUEFT"
      and "keine Gelegenheit zu melden" in out,
      "T28-Realfall heisst UNGEPRUEFT, nicht OK (Gruen waere ein "
      "Gesundheits-Claim ohne frischen Beleg)", f"{word(out)}")
    t("1 beansprucht/nie gestartet" in out,
      "die nie gestartete Zeile wird als solche benannt, nicht als Lauf")

    # (2) MESSLATTE aus Ticket 27, Falsch-Gruen-Fall 1: der Job feuert alle
    #     30 min WIRKLICH, die Pipeline meldet seit 1031 min nicht. Die
    #     verworfene Wach-Uhr gab hier rc=0. Muss rot bleiben.
    tot = {"j1": [("failed", ts(m), True)
                  for m in range(5, 1031, 30)]}
    rc, out = run([job()], execs=tot, hb=ts(1031))
    t(rc == 1 and "wirklich GESTARTET, ohne zu melden" in out
      and "die Lieferung steht" in out and clean(out),
      "Falsch-Gruen-Messlatte 1: gestartete Laeufe ohne Heartbeat -> DEFEKT",
      f"rc={rc} {word(out)}")

    # (3) EIN einziger wirklich gestarteter Lauf nach dem Heartbeat reicht
    #     fuer den Defekt - die Gelegenheit ist die Untergrenze, nicht eine
    #     Mehrheit.
    einer = {"j1": [("completed", ts(500), True),
                    ("failed", ts(20), True)]}
    rc, out = run([job()], execs=einer, hb=ts(500))
    t(rc == 1 and "seither sind 1 Laeufe wirklich GESTARTET" in out
      and clean(out),
      "eine einzige verpasste Gelegenheit genuegt fuer DEFEKT", f"rc={rc}")

    # (4) DAUERHAFT beanspruchte, nie gestartete Laeufe: der Runner laesst die
    #     Lieferung nie los. Das ist NICHT gruen - aber auch kein Skript-
    #     Defekt (Ticket-27-Klasse "Skript lief NIE").
    klemmt = {"j1": [("claimed", ts(m), False) for m in (10, 40, 70, 100)]
                    + [("completed", ts(400), True)]}
    rc, out = run([job()], execs=klemmt, hb=ts(400))
    t(rc == 2 and word(out) == "CRON_HEALTH_UNGEPRUEFT"
      and "4 beansprucht/nie gestartet" in out and clean(out),
      "Runner beansprucht dauernd, startet nie -> unmessbar, NICHT gruen",
      f"rc={rc} {word(out)}")

    # (5) ... aber jenseits der 24-h-Zusage wird daraus ein Defekt. Sonst
    #     waere "keine Gelegenheit" ein Dauerfreibrief fuer eine Lieferung,
    #     die seit Tagen nichts liefert.
    klemmt_lang = {"j1": [("claimed", ts(10), False),
                          ("completed", ts(1500), True)]}
    rc, out = run([job()], execs=klemmt_lang, hb=ts(1500))
    t(rc == 1 and "24-h-Zusage aus agb.html § 3 ist damit real ungedeckt"
      in out and clean(out),
      "keine Gelegenheit, aber > 1440 min stumm -> DEFEKT (kein Freibrief)",
      f"rc={rc} {word(out)}")

    # (6) ZEITSTEMPEL-JITTER: der Lauf, der den Heartbeat schreibt, wird vom
    #     Runner gestartet und schreibt Sekunden spaeter - liegen Runner-Uhr
    #     und Heartbeat-Uhr minimal auseinander, sieht der Start SPAETER aus
    #     als der Heartbeat. Ohne Karenz waere jeder gesunde Lauf sofort rot.
    selbst = {"j1": [("completed", ts(299.5), True)]}
    rc, out = run([job()], execs=selbst, hb=ts(300))
    t(rc != 1 and "die Lieferung steht" not in out and clean(out),
      "30 s Uhr-Jitter machen aus dem meldenden Lauf keine verpasste "
      "Gelegenheit", f"rc={rc} {word(out)}")

    # (7) VERDRAHTUNG (Merkregel: neuer Default = stiller Ausfall). Alle
    #     Faelle oben injizieren das dritte Feld. Hier laeuft der PRODUKTIVE
    #     Leser gegen eine ECHTE SQLite-Datei mit dem realen Schema - wenn er
    #     started_at nicht mitliest, gilt jede claimed-Zeile wieder als Lauf.
    import sqlite3 as _sq
    import tempfile
    _tmpdir = tempfile.mkdtemp(prefix="t28db")
    _crondir = os.path.join(_tmpdir, "cron")
    os.makedirs(_crondir, exist_ok=True)
    _db = os.path.join(_crondir, "executions.db")
    _con = _sq.connect(_db)
    _con.execute("CREATE TABLE executions (id INTEGER, job_id TEXT, "
                 "source TEXT, process_id TEXT, pid INTEGER, "
                 "process_started_at TEXT, status TEXT, claimed_at TEXT, "
                 "started_at TEXT, finished_at TEXT, error TEXT)")
    _con.execute("INSERT INTO executions VALUES (1,'j1','sched',NULL,NULL,"
                 "NULL,'completed','2026-08-10T04:00:00+02:00',"
                 "'2026-08-10T04:00:01+02:00','2026-08-10T04:00:05+02:00',"
                 "NULL)")
    _con.execute("INSERT INTO executions VALUES (2,'j1','sched',NULL,NULL,"
                 "NULL,'claimed','2026-08-10T06:04:12+02:00',NULL,NULL,NULL)")
    _con.commit()
    _con.close()
    try:
        _gelesen = io_read_executions(_tmpdir)
        _rows = [row_parts(r) for r in _gelesen.get("j1", [])]
    except Exception as exc:  # noqa: BLE001
        _rows = [("EXC", str(exc), True)]
    t([r[2] for r in _rows] == [True, False],
      "Verdrahtung: der PRODUKTIVE Leser liefert started_at wirklich mit "
      "(echte SQLite-Datei, reales Schema)", f"{_rows}")
    t(_rows and _rows[1][1] == "2026-08-10T06:04:12+02:00",
      "die nie gestartete Zeile behaelt claimed_at als Zeitstempel "
      "(Kriterium [A] verliert nichts)", f"{_rows[-1] if _rows else None}")
    try:
        os.remove(_db)
        os.rmdir(_crondir)
        os.rmdir(_tmpdir)
    except OSError:
        pass

    ok = sum(1 for c, _ in results if c)
    print(f"\nSELFTEST {'OK' if ok == len(results) else 'FEHLGESCHLAGEN'}: "
          f"{ok}/{len(results)}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
