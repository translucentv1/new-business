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
import os, sys, json, re

from resilient_gateway import ResilientGateway

GATEWAY = ResilientGateway()
CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
MODEL = "tencent/hy3:free (via ResilientGateway reasoning-chain)"


def _call_llm(prompt: str, key: str = None) -> str:
    """Ersetzt den direkten OpenRouter-Call durch den ResilientGateway.
    call_safe() liefert None statt zu crashen, wenn gerade kein Modell
    verfuegbar ist -> Aufrufer kann die Aufgabe ueberspringen/queuen."""
    result = GATEWAY.call_safe(
        task_type="reasoning",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    if result is None:
        # kein Modell verfuegbar -> als leere Antwort signalisieren,
        # fill_book() behandelt das als Skip (kein Crash).
        raise RuntimeError("ResilientGateway: aktuell kein Modell verfuegbar (alle Fallbacks blockiert)")
    return result["choices"][0]["message"]["content"]


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
    chapter_titles = [b["title"] for b in guide["chapters"]]
    prompt = build_prompt(guide["title"], guide["author"], chapter_titles)
    raw = _call_llm(prompt)  # key wird jetzt vom Gateway aus Env gezogen
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
