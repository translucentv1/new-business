"""
TB-19b: Companion-LLM-Filler (ADR-0018).

Fuelt study_guide.json pro Buch mit ECHTEM Inhalt (keine Platzhalter mehr):
- Kurzzusammenfassung des Werks
- Figurenliste (Name: Rolle)
- Zeit/Setting
- 5 Diskussionsfragen
- 30-Tage-Leseplan

Aufruf: 1 LLM-Call pro Buch (effizient). Nutzt OpenRouter (hy3:free) per direktem
HTTP-Call. Kein Hard Stop (lokale Verarbeitung, kein Account/kein Geld).

Nur die STRUKTUR wird hier geparst; der LLM liefert JSON zurueck. Tests mocken den
HTTP-Call (keine echte API im Testlauf, Charta: Tests muessen ohne externen Dienst gruen sein).
"""
import os, sys, json, re, urllib.request, urllib.error

HERMES_ENV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                          "AppData", "Local", "hermes", ".env"))
CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
MODEL = "tencent/hy3:free"


def _get_key():
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    if os.path.exists(HERMES_ENV):
        for line in open(HERMES_ENV, encoding="utf-8", errors="ignore"):
            if line.strip().startswith("OPENROUTER_API_KEY="):
                return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _call_llm(prompt: str, key: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    """Parst LLM-Antwort: entweder reiner JSON oder ```json ... ``` Block."""
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    text = text.strip()
    if not text.startswith("{"):
        # finde erste { bis letzte }
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e >= 0:
            text = text[s:e + 1]
    return json.loads(text)


def build_prompt(title: str, author: str, chapter_titles: list) -> str:
    ch = "\n".join(f"- {c}" for c in chapter_titles[:40])
    return (
        f"Du bist Literatur-Experte. Analysiere das Werk '{title}' von {author}.\n"
        f"Kapiteluebersicht (Auszug):\n{ch}\n\n"
        "Antworte NUR mit einem JSON-Objekt (kein Markdown, keine Erklaerung) mit genau diesen Keys:\n"
        '{"summary": "<3-5 Saetze Gesamtzusammenfassung>",\n'
        ' "characters": ["<Name>: <Rolle>", ...],\n'
        ' "setting": "<Zeit und Ort>",\n'
        ' "questions": ["<Frage 1>", ... 5 Stueck],\n'
        ' "reading_plan": ["<Tag 1>: ...", ... 30 Tage, ~1 Kapitel/Tag]}\n'
        "Deutsch. Praezise. Kein Geschwaetz."
    )


def fill_book(book_id: str, key: str = None) -> dict:
    prod = os.path.join(CORPUS, book_id, "product")
    guide_path = os.path.join(prod, "study_guide.json")
    if not os.path.exists(guide_path):
        raise FileNotFoundError(f"study_guide.json fehlt fuer {book_id} (TB-19 zuerst)")
    guide = json.load(open(guide_path, encoding="utf-8"))
    key = key or _get_key()
    if not key:
        raise RuntimeError("Kein OPENROUTER_API_KEY verfuegbar (Hard-Stop: Key fehlt)")
    chapter_titles = [b["title"] for b in guide["chapters"]]
    prompt = build_prompt(guide["title"], guide["author"], chapter_titles)
    raw = _call_llm(prompt, key)
    llm = _extract_json(raw)
    # merge: nur die vom LLM gelieferten Felder uebernehmen
    for k in ("summary", "characters", "setting", "questions", "reading_plan"):
        if k in llm:
            guide[k] = llm[k]
    guide["filled"] = True
    guide["filled_with"] = MODEL
    with open(guide_path, "w", encoding="utf-8") as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)
    return guide


if __name__ == "__main__":
    bid = sys.argv[1] if len(sys.argv) > 1 else "1342"
    g = fill_book(bid)
    print(f"filled {bid}: summary_len={len(g.get('summary',''))} chars, "
          f"chars={len(g.get('characters',[]))}, questions={len(g.get('questions',[]))}")
