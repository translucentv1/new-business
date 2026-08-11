"""Ticket 30 - EINMALIGE Reparatur (Ad-hoc-Sonde, KEIN stehendes Tor).

Einordnung nach Ticket 15: einmaliger Reparaturlauf an einem Konfigurationswert
-> braucht keinen --selftest. Das stehende Tor ist cron_delivery_audit.py; DIESES
Skript darf verschwinden, sobald der Wert korrekt ist.

Problem (MEASURED):
  .env: WHATSAPP_HOME_CHANNEL=self
  Der Scheduler nimmt diesen Wert als Fallback, wenn ein Job deliver='origin'
  hat, aber kein origin - und sendet woertlich an whatsapp:self.
  logs: "delivery to whatsapp:self failed: Cannot destructure property 'user'
  of 'jidDecode(...)' as it is undefined" -> HTTP 500.
  hermes-agent/plugins/platforms/whatsapp/adapter.py:1708 belegt die Semantik:
  "Home chat ID for cron delivery" - ein Chat-ID-Wert, KEIN Sentinel.

Fix: den Wert durch die chat_id ersetzen, die nachweislich zustellt (aus einem
Job in jobs.json, der deliver='origin' MIT origin hat).

Sicherheit: .env enthaelt Geheimnisse.
  - Backup VOR dem Schreiben.
  - Es wird ausschliesslich die EINE Zeile ersetzt; danach wird byteweise
    gegengelesen, dass sich genau eine Zeile geaendert hat, sonst Rollback.
  - Der Wert wird NIE ausgegeben (nur Laenge + Praefix).
"""

import datetime
import json
import os
import shutil
import sys

HOME = os.environ.get("HERMES_HOME") or os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "hermes"
)
ENV_PATH = os.path.join(HOME, ".env")
JOBS_PATH = os.path.join(HOME, "cron", "jobs.json")
KEY = "WHATSAPP_HOME_CHANNEL"


def redact(v):
    s = str(v)
    return "<len=%d pre=%s>" % (len(s), s[:4])


def healthy_chat_id():
    """chat_id eines Jobs holen, der deliver='origin' MIT vollstaendigem origin hat."""
    with open(JOBS_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
    items = jobs.items() if isinstance(jobs, dict) else [(j.get("id"), j) for j in jobs]
    for jid, job in items:
        o = job.get("origin")
        if (job.get("enabled") and job.get("deliver") == "origin"
                and isinstance(o, dict)
                and str(o.get("platform", "")).lower().startswith("whatsapp")
                and o.get("chat_id")):
            return str(o["chat_id"]), str(jid)[:12]
    return None, None


def main():
    apply = "--apply" in sys.argv[1:]
    print("== Ticket 30: Fallback-Adresse reparieren ==")
    print("modus      : %s" % ("APPLY" if apply else "DRY-RUN (--apply zum Schreiben)"))

    if not os.path.exists(ENV_PATH):
        print("ERGEBNIS: FIX_UNGEPRUEFT (.env nicht gefunden)")
        return 2

    with open(ENV_PATH, "rb") as fh:
        original = fh.read()
    lines = original.split(b"\n")

    hits = [i for i, ln in enumerate(lines)
            if ln.strip().startswith(KEY.encode() + b"=")]
    print("Treffer    : %d Zeile(n) mit %s" % (len(hits), KEY))
    if len(hits) != 1:
        print("ERGEBNIS: FIX_UNGEPRUEFT (erwartet genau 1 Zeile, gefunden %d)" % len(hits))
        return 2

    idx = hits[0]
    old_value = lines[idx].split(b"=", 1)[1].decode("utf-8", "replace").strip()
    print("Ist-Wert   : %s" % redact(old_value))

    new_value, src_job = healthy_chat_id()
    if not new_value:
        print("ERGEBNIS: FIX_UNGEPRUEFT (kein Job mit nachweislich zustellendem origin)")
        return 2
    print("Soll-Wert  : %s (aus Job %s, gleiche Adresse wie die MEASURED"
          " zustellende)" % (redact(new_value), src_job))

    if old_value == new_value:
        print("\nERGEBNIS: FIX_NICHTS_ZU_TUN")
        return 0

    if not apply:
        print("\nERGEBNIS: FIX_DRY_RUN (nichts geschrieben)")
        return 0

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = "%s.bak-t30-%s" % (ENV_PATH, stamp)
    shutil.copy2(ENV_PATH, backup)
    print("Backup     : %s (%d B)" % (os.path.basename(backup), os.path.getsize(backup)))

    new_lines = list(lines)
    # Zeilenende der ORIGINALZEILE erhalten: die Datei ist durchgehend CRLF
    # (MEASURED 537/537). Ein rohes b"\n" haette eine gemischte Zeile erzeugt.
    eol = b"\r" if lines[idx].endswith(b"\r") else b""
    new_lines[idx] = KEY.encode() + b"=" + new_value.encode("utf-8") + eol
    with open(ENV_PATH, "wb") as fh:
        fh.write(b"\n".join(new_lines))

    # Gegenlesen: exakt EINE Zeile darf sich geaendert haben.
    with open(ENV_PATH, "rb") as fh:
        after = fh.read().split(b"\n")
    if len(after) != len(lines):
        shutil.copy2(backup, ENV_PATH)
        print("ROLLBACK: Zeilenzahl %d -> %d" % (len(lines), len(after)))
        return 1
    changed = [i for i in range(len(lines)) if lines[i] != after[i]]
    print("geaendert  : %d Zeile(n) (Zeile %d)" % (len(changed), idx + 1))
    if changed != [idx]:
        shutil.copy2(backup, ENV_PATH)
        print("ROLLBACK: unerwartete Aenderungen in %s" % changed[:5])
        return 1

    print("\nERGEBNIS: FIX_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
