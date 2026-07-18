"""Tests fuer pricing.py (ADR-0006). MEASURED-Marge gegen 10%+50c."""
import unittest, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pricing


class TestPricing(unittest.TestCase):
    def test_default_price(self):
        self.assertEqual(pricing.PD_PRICE_CENTS_DEFAULT, 399)

    def test_net_399(self):
        # 399 - (round(399*0.10)=40 + 50) = 399 - 90 = 309
        self.assertEqual(pricing.net_cents(399), 309)

    def test_margin_399(self):
        self.assertAlmostEqual(pricing.net_margin_pct(399), 309 / 399, places=4)
        self.assertGreater(pricing.net_margin_pct(399), 0.75)  # >77%

    def test_net_099(self):
        # 99 - (round(99*0.10)=10 + 50) = 99 - 60 = 39
        self.assertEqual(pricing.net_cents(99), 39)

    def test_free_no_fee(self):
        self.assertEqual(pricing.net_cents(0), 0)
        self.assertEqual(pricing.net_margin_pct(0), 0.0)

    def test_env_override(self):
        os.environ["PD_PRICE_CENTS"] = "299"
        self.assertEqual(pricing.get_price_cents(), 299)
        del os.environ["PD_PRICE_CENTS"]
        self.assertEqual(pricing.get_price_cents(), 399)

    def test_env_garbage_falls_back(self):
        os.environ["PD_PRICE_CENTS"] = "abc"
        self.assertEqual(pricing.get_price_cents(), 399)
        del os.environ["PD_PRICE_CENTS"]


if __name__ == "__main__":
    unittest.main()
