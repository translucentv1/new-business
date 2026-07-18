"""Tests fuer companion_llm.py (TB-19b) — MOCK ohne echten API-Call (Charta: Tests ohne externen Dienst)."""
import unittest, sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import companion_llm as cl


FAKE_JSON = json.dumps({
    "summary": "Ein Klassiker über Liebe und Vorurteil.",
    "characters": ["Elizabeth Bennet: Protagonistin", "Mr. Darcy: Aristokrat"],
    "setting": "England, frühes 19. Jh.",
    "questions": ["F1?", "F2?", "F3?", "F4?", "F5?"],
    "reading_plan": ["Tag 1: Kapitel 1", "Tag 2: Kapitel 2"],
})


class FakeResp:
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def read(self):
        return json.dumps({"choices": [{"message": {"content": "```json\n" + FAKE_JSON + "\n```"}}]}).encode()


def fake_urlopen(req, timeout=0):
    return FakeResp()


class TestCompanionLLM(unittest.TestCase):
    def setUp(self):
        cl.urllib.request.urlopen = fake_urlopen

    def test_extract_json_codeblock(self):
        t = cl._extract_json("bla\n```json\n" + FAKE_JSON + "\n```\nende")
        self.assertEqual(t["summary"], "Ein Klassiker über Liebe und Vorurteil.")

    def test_extract_json_bare(self):
        t = cl._extract_json(FAKE_JSON)
        self.assertEqual(len(t["characters"]), 2)

    def test_fill_book_writes_merged_guide(self):
        # temp guide-datei mit Minimal-Struktur, fill_book mit fake key
        d = tempfile.mkdtemp()
        gid = os.path.join(d, "study_guide.json")
        json.dump({"book_id": "X", "title": "T", "author": "A",
                   "chapter_count": 1, "chapters": [{"nr": 1, "title": "1. Kapitel I",
                   "word_count": 10, "summary_placeholder": "[P]", "questions_placeholder": "[Q]"}],
                   "companion_sections": []}, open(gid, "w", encoding="utf-8"))
        orig_corpus = cl.CORPUS
        try:
            cl.CORPUS = d  # fill_book sucht corpus/<id>/product/study_guide.json
            os.makedirs(os.path.join(d, "X", "product"), exist_ok=True)
            os.replace(gid, os.path.join(d, "X", "product", "study_guide.json"))
            g = cl.fill_book("X", key="fake-key")
            self.assertTrue(g.get("filled"))
            self.assertEqual(len(g["questions"]), 5)
            self.assertIn("summary", g)
        finally:
            cl.CORPUS = orig_corpus


if __name__ == "__main__":
    unittest.main()
