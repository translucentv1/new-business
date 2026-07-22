"""Lightweight persistent memory for Hermes (local, free, Gemini embeddings).

No torch/unstructured — just litellm + sqlite. Cold start ~3s.
Data lives in cognee_data/memory.db (gitignored).

Usage:
    memory.py remember "some fact"
    memory.py recall "what do we know about X"
    memory.py forget            # wipe all
    memory.py forget <id>       # delete one
    memory.py list              # show stored entries
"""
import os, sys, json, sqlite3, time, hashlib, math

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "cognee_data")
DB = os.path.join(DATA_DIR, "memory.db")

HM = os.environ.get("HERMES_HOME", os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes"))
KEY = ""
try:
    with open(os.path.join(HM, ".env")) as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                KEY = line.split("=", 1)[1].strip().strip('"')
except Exception:
    pass

EMBED_MODEL = "gemini/gemini-embedding-001"
EMBED_DIMS = 3072  # gemini-embedding-001 actual dimension (measured)


def _embed(texts):
    import litellm
    resp = litellm.embedding(model=EMBED_MODEL, input=texts, api_key=KEY)
    return [d["embedding"] for d in resp["data"]]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _init():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created REAL NOT NULL,
            source TEXT
        )"""
    )
    con.commit()
    return con


def remember(text, source="hermes"):
    text = text.strip()
    if not text:
        return None
    con = _init()
    try:
        vec = _embed([text])[0]
        mid = hashlib.sha1(text.encode()).hexdigest()[:16]
        con.execute(
            "INSERT OR REPLACE INTO memories (id, text, embedding, created, source) VALUES (?,?,?,?,?)",
            (mid, text, json.dumps(vec).encode(), time.time(), source),
        )
        con.commit()
        return mid
    finally:
        con.close()


def recall(query, top_k=5):
    con = _init()
    try:
        qvec = _embed([query])[0]
        rows = con.execute("SELECT id, text, embedding, source FROM memories").fetchall()
        scored = []
        for mid, text, blob, source in rows:
            vec = json.loads(blob.decode())
            scored.append((_cosine(qvec, vec), mid, text, source))
        scored.sort(reverse=True)
        return [{"id": m, "text": t, "score": round(s, 3), "source": s}
                for s, m, t, s2 in scored[:top_k] if s > 0.0]
    finally:
        con.close()


def forget(mid=None):
    con = _init()
    try:
        if mid:
            con.execute("DELETE FROM memories WHERE id=?", (mid,))
            n = con.total_changes
        else:
            con.execute("DELETE FROM memories")
            n = con.total_changes
        con.commit()
        return n
    finally:
        con.close()


def list_all():
    con = _init()
    try:
        rows = con.execute("SELECT id, text, source, created FROM memories ORDER BY created DESC").fetchall()
        return [{"id": r[0], "text": r[1], "source": r[2], "created": r[3]} for r in rows]
    finally:
        con.close()


def main():
    if len(sys.argv) < 2:
        print("usage: memory.py [remember|recall|forget|list] [args]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "remember":
        text = " ".join(sys.argv[2:])
        mid = remember(text)
        print(f"remembered id={mid}" if mid else "empty text")
    elif cmd == "recall":
        q = " ".join(sys.argv[2:])
        for r in recall(q):
            print(f"[{r['score']}] {r['text']}")
    elif cmd == "forget":
        if len(sys.argv) > 2:
            print(f"deleted {forget(sys.argv[2])}")
        else:
            print(f"wiped {forget()} entries")
    elif cmd == "list":
        for r in list_all():
            print(f"{r['id']} ({r['source']}): {r['text'][:80]}")
    else:
        print(f"unknown {cmd}")


if __name__ == "__main__":
    main()
