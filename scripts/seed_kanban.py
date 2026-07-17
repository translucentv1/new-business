import sqlite3, time

db = r"C:\Users\phili\AppData\Local\hermes\kanban.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

now = int(time.time())

tickets = [
    ("TB-1", "PD-Quelle scannen (Gutenberg-DE/Wikisource API)",
     "Tracer-Bullet: Skript zieht DE Public-Domain-Texte via API/HTML, extrahiert rohen Text + Metadaten (Titel, Autor, Jahr) nach /new-business/corpus/. VOLLSTANDIGER PFAD: Quelle->Datei. Blockiert durch: nichts."),
    ("TB-2", "PD-Text aufbereiten (Struktur + Begleit-PDF)",
     "Tracer-Bullet: Nimmt Rohtext aus TB-1, Agent strukturiert (Kapitel, Rechtschreibung, Inhaltsverzeichnis, Register), erzeugt PDF + Beschreibung. VOLLSTANDIGER PFAD: Rohtext->Produkt-Asset. Blockiert durch: TB-1."),
    ("TB-3", "Gumroad-Uploader (API Product create/publish)",
     "Tracer-Bullet: Gumroad-REST-Client (app.gumroad.com/api) legt Produkt aus TB-2 an + publish. Braucht GUMROAD_API_KEY (harter Stopp: Nutzer stellt Key). VOLLSTANDIGER PFAD: Asset->live Product URL. Blockiert durch: TB-2."),
    ("TB-4", "Sale-Webhook + Reinvestitions-Logik",
     "Tracer-Bullet: Flask-Endpoint /gumroad/webhook empfangt Sale-Ping (signiert), belegt MEASURED Sale in sales.log, triggert Reinvestition. VOLLSTANDIGER PFAD: Sale->Reinvest. Blockiert durch: TB-3."),
    ("TB-5", "Autonomer Watchdog-Loop (Cron)",
     "Tracer-Bullet: Cron-Skript triggert TB-1->2->3 Pipeline alle Xh, neuer Titel pro Lauf. VOLLSTANDIGER PFAD: Loop-Orchestrierung. Blockiert durch: TB-1,2,3."),
]

for tid, title, body in tickets:
    cur.execute(
        "INSERT OR REPLACE INTO tasks (id, title, body, status, priority, created_at, created_by) VALUES (?,?,?,?,?,?,?)",
        (tid, title, body, "todo", 1, now, "hermes"))
    print("ticket", tid, "written")

conn.commit()
conn.close()
print("DONE", len(tickets), "tickets")
