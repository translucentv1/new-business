"""Regressionstest fuer TB-13-Repair (corruptes Bundle 25913).

Schutz: nach dem Repair muss 25913
  1) korrekte Meta (Tales of Folk and Fairies / Katharine Pyle) haben,
  2) als Maerchensammlung mit 14 Tales (nicht 1 Kapitel) strukturiert sein,
  3) KEINEN PG-Leak (pgdp.net / project gutenberg / gutenberg-tm) enthalten,
  4) vom Deliverable-Gate als NICHT-corrupt erkannt werden.

Gegen echte Dateien, keine Spielzeug-Strings (Charta: Ergebnis pruefen).
"""
import os, sys, json, re, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import deliverable_gen as dg

BOOK = "25913"
PROD = os.path.join(HERE, "..", "corpus", BOOK, "product")


class TestRepair25913(unittest.TestCase):
    def test_meta_correct(self):
        meta = json.load(open(os.path.join(PROD, "meta.json"), encoding="utf-8"))
        self.assertEqual(meta["title"], "Tales of Folk and Fairies")
        self.assertEqual(meta["author"], "Katharine Pyle")

    def test_root_meta_correct(self):
        root = json.load(open(os.path.join(HERE, "..", "corpus", BOOK, "meta.json"), encoding="utf-8"))
        self.assertEqual(root["title"], "Tales of Folk and Fairies")
        self.assertEqual(root["author"], "Katharine Pyle")

    def test_fourteen_tales(self):
        meta = json.load(open(os.path.join(PROD, "meta.json"), encoding="utf-8"))
        self.assertEqual(meta["chapters"], 14)

    def test_no_pg_leak(self):
        content = open(os.path.join(PROD, "content.md"), encoding="utf-8").read()
        self.assertNotRegex(content, r"project gutenberg|gutenberg-tm|pgdp\.net",
                            "PG-Leak (project gutenberg / pgdp.net) in content.md")

    def test_not_corrupt(self):
        content = open(os.path.join(PROD, "content.md"), encoding="utf-8").read()
        self.assertFalse(dg.is_corrupt(content), "25913 darf nicht mehr als corrupt gelten")

    def test_study_guide_fourteen(self):
        sg = json.load(open(os.path.join(PROD, "study_guide.json"), encoding="utf-8"))
        self.assertEqual(sg["chapter_count"], 14)
        self.assertEqual(sg["title"], "Tales of Folk and Fairies")
        # Geruest muss 14 Kapitel-Bloecke haben (Fuellung ist separater, optionaler Schritt).
        self.assertEqual(len(sg["chapters"]), 14)


if __name__ == "__main__":
    unittest.main()
