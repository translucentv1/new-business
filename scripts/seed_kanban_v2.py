"""Seed kanban.db with tracer-bullet tickets for the price+distribution+uploader loop.
Schema kept minimal and explicit (learned pitfall: don't assume columns)."""
import sqlite3, os, time

DB = os.path.join(os.path.dirname(__file__), "..", "kanban.db")
con = sqlite3.connect(DB)
c = con.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS tickets(
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    spec TEXT,
    status TEXT DEFAULT 'todo',
    blocked_by TEXT,
    created_at INTEGER
)""")

now = int(time.time())
tickets = [
    ("TB-3b", "Uploader auf Presign-Flow umschreiben",
     "gumroad_uploader.py: publish() nutzt presign->S3-PUT->complete->attach (ADR-0008). "
     "Preis PD_PRICE_CENTS default 399 (ADR-0006). Sauberer NO_KEY-Stopp bleibt. "
     "Test: mock-freier Unit-Test der payload-Bildung + Preis-Konstante.", "todo", "", now),
    ("TB-6", "Landingpage-Generator (SEO, statisches HTML)",
     "Je Produkt eine statische HTML-Landingpage (Titel, Autor, Beschreibung, Gumroad-Link, "
     "SEO meta/OG-tags, 'kostenlos lesen'-Longtail). Output docs/site/<id>.html + index.html. "
     "GitHub Pages-fähig. Test: HTML enthält Titel, Gumroad-Link, og:title.", "todo", "TB-3b", now),
    ("TB-7", "Preis-Konstante zentral + im Loop verdrahten",
     "PD_PRICE_CENTS in einem Modul (fee/pricing), von uploader + landingpage genutzt. "
     "Test asserts netto-Marge bei 399 gegen MEASURED 10%+50c.", "todo", "", now),
]
for t in tickets:
    c.execute("INSERT OR REPLACE INTO tickets(id,title,spec,status,blocked_by,created_at) VALUES(?,?,?,?,?,?)", t)
con.commit()
for row in c.execute("SELECT id,title,status,blocked_by FROM tickets ORDER BY id"):
    print(row)
con.close()
print("SEEDED", DB)
