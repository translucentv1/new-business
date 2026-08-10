"""Ticket 27, Hauptfrage - wie oft entsteht Falsch-Rot durch Scheduler-Stillstand?

Read-only Messsonde gegen die ECHTE executions.db. Beantwortet die eine Zahl,
an der die Entscheidung haengt: exit!=0 bei UNGEPRUEFT ist nur dann vertretbar,
wenn der Fall SELTEN ist. Wie oft er real vorkommt, war bisher ASSUMED.

Gemessen wird:
  1. Alle Luecken > SCHWELLE Minuten, in denen KEIN EINZIGER Job lief
     (= Rechner/Scheduler aus). Das ist die Ursache des heutigen
     CRON_HEALTH_UNGEPRUEFT.
  2. Wie viele Laeufe des Geldpfad-Traegers unmittelbar NACH so einer Luecke
     lagen - das sind die Laeufe, die unter der heutigen Konvention als
     'failed' in der DB landen, obwohl der Geldpfad gesund ist.
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

TRAEGER = "bfb63346d942"
SCHWELLE = 180.0   # erlaubte Erfolgs-Luecke des Audits (Intervall 30 min * 6)
TAGE = 10


def home():
    h = os.environ.get("HERMES_HOME")
    return h or os.path.join(os.path.expanduser("~"), "AppData", "Local",
                             "hermes")


def parse(ts):
    if not ts:
        return None
    try:
        d = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def main():
    db = os.path.join(home(), "cron", "executions.db")
    if not os.path.exists(db):
        print(f"UNMESSBAR: {db} fehlt")
        return 2
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = [(r[0], parse(r[1])) for r in con.execute(
        "SELECT job_id, claimed_at FROM executions ORDER BY claimed_at")]
    rows = [r for r in rows if r[1]]
    if not rows:
        print("UNMESSBAR: keine Zeilen")
        return 2
    now = datetime.now(timezone.utc)
    ab = now - timedelta(days=TAGE)
    fenster = [r for r in rows if r[1] >= ab]
    print(f"== Ticket 27: Stillstands-Frequenz (letzte {TAGE} Tage) ==")
    print(f"DB        : {db}")
    print(f"Zeilen    : {len(fenster)} im Fenster / {len(rows)} gesamt")
    print(f"jetzt UTC : {now.isoformat(timespec='seconds')}")

    # 1. Luecken, in denen KEIN Job lief.
    luecken = []
    for (ja, ta), (jb, tb) in zip(fenster, fenster[1:]):
        d = (tb - ta).total_seconds() / 60.0
        if d > SCHWELLE:
            luecken.append((ta, tb, d))
    print(f"\n-- Luecken > {SCHWELLE:.0f} min OHNE einen einzigen Job-Lauf: "
          f"{len(luecken)} --")
    for ta, tb, d in luecken:
        print(f"  {ta.isoformat(timespec='minutes')} -> "
              f"{tb.isoformat(timespec='minutes')}  = {d:6.0f} min")
    tage_span = max((fenster[-1][1] - fenster[0][1]).total_seconds()
                    / 86400.0, 1e-9)
    print(f"  Frequenz: {len(luecken)} Stillstaende in {tage_span:.1f} Tagen "
          f"= {len(luecken) / tage_span:.2f} pro Tag")

    # 2. Traegerlaeufe direkt nach einem Stillstand -> heute Falsch-Rot.
    tr = [t for j, t in fenster if j == TRAEGER]
    betroffen = []
    for ta, tb, d in luecken:
        nach = [t for t in tr if tb <= t <= tb + timedelta(minutes=SCHWELLE)]
        if nach:
            betroffen.append((tb, len(nach), d))
    print(f"\n-- Traegerlaeufe im {SCHWELLE:.0f}-min-Schatten eines "
          f"Stillstands (= Falsch-Rot unter heutiger Konvention) --")
    for tb, n, d in betroffen:
        print(f"  nach {d:.0f}-min-Stillstand ab "
              f"{tb.isoformat(timespec='minutes')}: {n} Lauf/Laeufe")
    ges = sum(n for _, n, _ in betroffen)
    print(f"  Summe: {ges} Laeufe / {len(tr)} Traegerlaeufe im Fenster "
          f"= {(100.0 * ges / len(tr)) if tr else 0:.1f} %")
    print(f"  Hochrechnung: {len(luecken) / tage_span:.2f} Falsch-Rot-Anlaesse "
          f"pro Tag = {30 * len(luecken) / tage_span:.0f} pro Monat")
    print("\nHINWEIS: gemessen wird die ABWESENHEIT von Laeufen. Ob der Rechner "
          "aus war oder der Scheduler haengt, unterscheidet die DB nicht.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
