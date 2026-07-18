"""Tests fuer gumroad_uploader.py (TB-3b, ADR-0006/0008).
Kein echter API-Call — nur payload-Bildung + NO_KEY-Stopp."""
import unittest, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import gumroad_uploader as gu


class TestUploader(unittest.TestCase):
    def test_build_payload_default_price(self):
        p, prod = gu.build_payload("11")
        self.assertTrue(p["name"], "name missing")
        self.assertIn("Public Domain", p["description"])
        self.assertEqual(p["price"], 399, f"default price should be 399 (ADR-0006), got {p['price']}")
        self.assertNotIn("published", p, "payload must not carry 'published' (publish via /enable now)")
        self.assertTrue(os.path.isdir(prod))

    def test_build_payload_price_env(self):
        os.environ["PD_PRICE_CENTS"] = "490"
        p, _ = gu.build_payload("11")
        self.assertEqual(p["price"], 490)
        del os.environ["PD_PRICE_CENTS"]

    def test_no_key_hard_stop(self):
        # Ensure no key is found: temporarily hide env + secrets
        old = os.environ.pop("GUMROAD_API_KEY", None)
        sec = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".gumroad_secrets"))
        bak = sec + ".bak"
        moved = False
        if os.path.exists(sec):
            os.rename(sec, bak); moved = True
        try:
            ok, det = gu.publish("11")
            self.assertFalse(ok)
            self.assertIn("NO_KEY", det)
        finally:
            if moved:
                os.rename(bak, sec)
            if old is not None:
                os.environ["GUMROAD_API_KEY"] = old

    def test_missing_bundle(self):
        ok, det = gu.publish("does-not-exist-999")
        # with a key present it will hit BUNDLE_ERR; without key NO_KEY. Either is a clean refusal.
        self.assertFalse(ok)
        self.assertTrue("BUNDLE_ERR" in det or "NO_KEY" in det)


if __name__ == "__main__":
    unittest.main()
