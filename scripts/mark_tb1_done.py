import sqlite3, time
db = r"C:\Users\phili\AppData\Local\hermes\kanban.db"
conn = sqlite3.connect(db)
conn.execute("UPDATE tasks SET status='done', completed_at=? WHERE id='TB-1'", (int(time.time()),))
conn.commit()
conn.close()
print("TB-1 -> done")
