"""Ticket 23 - Zustellziel reparieren (AFK, ohne Gateway-Neustart).

Befund (MEASURED): Jobs mit deliver='origin' und origin=None fallen im
Scheduler auf den 'whatsapp home channel' = woertlich 'whatsapp:self' zurueck.
jidDecode('self') ist undefined -> WhatsApp-Bridge antwortet HTTP 500.
Die Bridge ist GESUND: Job 3e7e333151b0 stellt mit vorhandenem origin-Block zu.

Fix: den origin-Block eines nachweislich zustellenden Jobs auf die kaputten
Jobs uebertragen. KEIN neues Ziel erfunden, KEIN Credential im Code -
die Adresse wird zur Laufzeit aus jobs.json gelesen.

Aufruf:
  --dry-run   nur zeigen, was geaendert wuerde (Default)
  --apply     Backup schreiben und aendern
"""
import datetime
import json
import os
import shutil
import sys

HOME = os.environ.get("HERMES_HOME") or os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "hermes"
)
P = os.path.join(HOME, "cron", "jobs.json")


def load():
    with open(P, encoding="utf-8") as fh:
        return json.load(fh)


def job_items(data):
    jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
    if isinstance(jobs, dict):
        return list(jobs.items())
    return [(j.get("id"), j) for j in jobs]


def main(argv):
    apply_ = "--apply" in argv
    data = load()
    items = job_items(data)

    spender = None
    for jid, j in items:
        if j.get("deliver") == "origin" and j.get("origin") and j.get("enabled"):
            spender = (str(jid), j)
            break
    if spender is None:
        print("SPENDER FEHLT: kein aktiver Job mit funktionierendem origin-Block.")
        print("ERGEBNIS: FIX_UNGEPRUEFT (kein belegtes Zustellziel vorhanden)")
        return 2

    sid, sjob = spender
    origin = sjob["origin"]
    ziel = origin.get("chat_id")
    print("Spender (nachweislich zustellend): %s  %s" % (sid, sjob.get("name")))
    print("  platform=%s chat_name=%s" % (origin.get("platform"), origin.get("chat_name")))
    print("  chat_id  = %s...%s (gekuerzt)" % (str(ziel)[:4], str(ziel)[-4:]))

    kaputt = [
        (str(jid), j)
        for jid, j in items
        if j.get("deliver") == "origin" and not j.get("origin")
    ]
    print("\nKaputte Jobs (deliver='origin', origin=None): %d" % len(kaputt))
    for jid, j in kaputt:
        print("  %s  %s" % (jid, (j.get("name") or "")[:50]))
    if not kaputt:
        print("ERGEBNIS: FIX_NICHTS_ZU_TUN")
        return 0

    if not apply_:
        print("\n--dry-run: nichts geaendert. Mit --apply ausfuehren.")
        return 0

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = P + ".bak-t23-" + stamp
    shutil.copy2(P, bak)
    print("\nBackup: %s (%d B)" % (bak, os.path.getsize(bak)))

    for _jid, j in kaputt:
        j["origin"] = json.loads(json.dumps(origin))  # tiefe Kopie
        j["last_delivery_error"] = None

    tmp = P + ".tmp-t23"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, P)

    # Gegenlesen: Datei muss wieder parsen UND die Job-Anzahl muss stimmen
    neu = load()
    n_items = job_items(neu)
    if len(n_items) != len(items):
        print("ABBRUCH: Job-Anzahl veraendert (%d -> %d)" % (len(items), len(n_items)))
        shutil.copy2(bak, P)
        print("Backup zurueckgespielt.")
        return 1
    rest = [
        str(jid)
        for jid, j in n_items
        if j.get("deliver") == "origin" and not j.get("origin")
    ]
    print("Jobs nach dem Schreiben: %d (unveraendert)" % len(n_items))
    print("Noch kaputt: %d %s" % (len(rest), rest))
    print("ERGEBNIS: %s" % ("FIX_OK" if not rest else "FIX_DEFEKT"))
    return 0 if not rest else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
