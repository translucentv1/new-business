"""Tests fuer landingpage_gen.py (TB-6)."""
import unittest, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import landingpage_gen as lg


class TestLanding(unittest.TestCase):
    def test_build_writes_html(self):
        n = lg.build({"11": "https://philippbehnisch.gumroad.com/l/test11"})
        self.assertGreaterEqual(n, 1)
        # index exists
        idx = os.path.join(lg.SITE, "index.html")
        self.assertTrue(os.path.exists(idx))
        # at least one product page
        self.assertTrue(os.path.exists(os.path.join(lg.SITE, "11", "index.html")))

    def test_html_has_title_and_link(self):
        lg.build({"11": "https://philippbehnisch.gumroad.com/l/test11"})
        with open(os.path.join(lg.SITE, "11", "index.html"), encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("<title>", html)
        self.assertIn("https://philippbehnisch.gumroad.com/l/test11", html)
        self.assertIn("og:title", html)

    def test_index_lists_products(self):
        lg.build()
        with open(os.path.join(lg.SITE, "index.html"), encoding="utf-8") as fh:
            idx = fh.read()
        self.assertIn("<li>", idx)


if __name__ == "__main__":
    unittest.main()
