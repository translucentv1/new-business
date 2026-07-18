"""Tests fuer study_guide_gen.py (TB-19) — gegen ECHTE Kapitelstruktur (Charta: Ergebnis pruefen)."""
import unittest, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import study_guide_gen as sg


class TestStudyGuide(unittest.TestCase):
    def test_real_book_splits_chapters(self):
        # Pride and Prejudice (1342) hat laut Quelle ~61 Kapitel
        g = sg.build_guide("1342")
        self.assertGreater(g["chapter_count"], 30, "P&P sollte >30 Kapitel haben")
        self.assertEqual(g["title"], "Pride and Prejudice")
        # jeder Block hat word_count >= 0 und Platzhalter
        for b in g["chapters"]:
            self.assertIn("summary_placeholder", b)
            self.assertIn("questions_placeholder", b)
            self.assertGreaterEqual(b["word_count"], 0)

    def test_single_chapter_no_crash(self):
        # Realistische Ein-Kapitel-Eingabe im echten Format '<zahl>. <Titel>'
        fake = "1. Kapitel 1\nHallo Welt. Das ist der einzige Abschnitt."
        ch = sg.detect_chapters(fake)
        self.assertEqual(len(ch), 1)
        self.assertIn("Hallo Welt", ch[0][1])

    def test_no_chapters_text(self):
        # Gemein-Eingabe: gar kein Kapitelmarker (Roman als ein Block)
        plain = "Es war einmal. Ende."
        ch = sg.detect_chapters(plain)
        # kein '<zahl>. Titel' Marker -> leere Liste (kein Kapitel erkannt)
        self.assertIsInstance(ch, list)
        self.assertEqual(len(ch), 0)

    def test_write_produces_json(self):
        p, g = sg.write_guide("1342")
        self.assertTrue(os.path.exists(p))
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        self.assertEqual(d["book_id"], "1342")
        self.assertIn("companion_sections", d)


if __name__ == "__main__":
    unittest.main()
