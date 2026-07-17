import sqlite3, time
db = r"C:\Users\phili\AppData\Local\hermes\kanban.db"
conn = sqlite3.connect(db)
conn.execute("UPDATE tasks SET status='done', completed_at=? WHERE id='TB-4'", (int(time.time()),))
conn.execute("UPDATE tasks SET status='done', completed_at=? WHERE id='TB-5'", (int(time.time()),))
conn.commit(); conn.close()
print("TB-4, TB-5 -> done")
