"""TDD seam test for template_gen (TB-22). Asserts real output, not toy."""
import os, sys, json, csv, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import template_gen as tg


class TestTemplateGen(unittest.TestCase):

    def setUp(self):
        # generate all 3 specs + deliverables
        self.out = tg.generate()

    def test_all_specs_generated(self):
        self.assertEqual(set(self.out.keys()),
                         {"finanz-tracker-dach", "kleingewerbe-steuer",
                          "adhs-wochenplaner", "rechnungsvorlage-kleinunternehmer"})

    def test_sheets_has_formula_and_no_placeholder(self):
        p = self.out["finanz-tracker-dach"]
        self.assertTrue(os.path.exists(p))
        with open(p, encoding="utf-8") as f:
            rows = list(csv.reader(f))
        # header + 9 cats + SUMME row
        self.assertGreaterEqual(len(rows), 11)
        last = rows[-1]
        self.assertTrue(last[0] == "SUMME" and last[1].startswith("=SUM"),
                        f"no sum formula: {last}")
        blob = " ".join(" ".join(r) for r in rows)
        self.assertNotIn("XXX", blob)
        self.assertNotIn("ZUSAMMENFASSUNG", blob)

    def test_notion_has_all_sections(self):
        p = self.out["adhs-wochenplaner"]
        txt = open(p, encoding="utf-8").read()
        for sec in ["Wochen-Fokus", "Brain-Dump", "Dopamin-Tasks", "Wochendebrief"]:
            self.assertIn(sec, txt, f"missing section {sec}")
        self.assertNotIn("XXX", txt)

    def test_prices_in_spec(self):
        for sid in self.out:
            spec = json.load(open(os.path.join(tg.TPL_ROOT, sid, "spec.json"), encoding="utf-8"))
            self.assertGreater(spec["price_eur"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
