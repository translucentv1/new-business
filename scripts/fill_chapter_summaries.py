"""TB-19c: Fuelle pro-Kapitel Zusammenfassungen in study_guide.json.

companion_llm fuellt nur die top-level Felder. Die Produktseiten
(landingpage_gen) zeigen aber die pro-Kapitel `summary_placeholder` ->
ohne Fill steht dort "[ZUSAMMENFASSUNG Kapitel N ...]" (Charta-Bug:
kaputtes Vorzeige-Produkt).

Dieses Skript macht 1 LLM-Call pro Buch und liefert eine Liste kurzer
Kapitelzusammenfassungen (basierend auf Titel + Gesamtkontext). Ersetzt
den Platzhalter-Text durch echten Inhalt.

Kein Hard Stop: lokale Verarbeitung, OpenRouter hy3:free.
"""
import os, sys, json, re, glob

from resilient_gateway import ResilientGateway

GATEWAY = ResilientGateway()
CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
MODEL = "tencent/hy3:free (via ResilientGateway reasoning-chain)"


def _call(prompt, key=None):
    result = GATEWAY.call_safe(
        task_type="reasoning",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    if result is None:
        return None
    return result["choices"][0]["message"]["content"]


def _extract_list(text):
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return [l.strip("- ").strip() for l in text.splitlines() if l.strip()]


def fill(bid, key):
    gj = os.path.join(CORPUS, bid, "product", "study_guide.json")
    if not os.path.exists(gj):
        return False, "no guide"
    guide = json.load(open(gj, encoding="utf-8"))
    chapters = guide.get("chapters", [])
    titles = [c.get("title", f"Kapitel {i+1}") for i, c in enumerate(chapters)]
    overall = guide.get("summary", "")
    prompt = (
        f"Werk: '{guide.get('title')}' von {guide.get('author')}.\n"
        f"Gesamtzusammenfassung: {overall}\n\n"
        f"Kapiteluebersicht:\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles[:61])) +
        "\n\nSchreibe fuer JEDES der oben genannten Kapitel EINE kurze Zusammenfassung "
        "(1-2 Saetze, was thematisch passiert). Antworte NUR als JSON-Array von Strings "
        "(exakt so viele Elemente wie Kapitel oben), kein Markdown, keine Erklaerung.\n"
        "Deutsch. Beispiel: [\"Kapitel 1 ...\", \"Kapitel 2 ...\"]"
    )
    raw = _call(prompt)
    if raw is None:
        return False, "gateway: kein Modell verfuegbar (alle Fallbacks blockiert) -> uebersprungen"
    summaries = _extract_list(raw)
    n = min(len(summaries), len(chapters))
    for i in range(n):
        chapters[i]["summary_placeholder"] = summaries[i]
    guide["chapters"] = chapters
    with open(gj, "w", encoding="utf-8") as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)
    return True, f"filled {n}/{len(chapters)} chapter summaries"


if __name__ == "__main__":
    if not (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("NVIDIA_API_KEY")):
        print("NO_KEY: weder OPENROUTER_API_KEY noch NVIDIA_API_KEY gesetzt")
        sys.exit(1)
    bids = sys.argv[1:] or [os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*"))]
    for bid in bids:
        ok, msg = fill(bid)
        print(f"{bid}: {'OK' if ok else 'FAIL'} {msg}")
