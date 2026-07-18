"""Tests for check_payment_connected.py -- no real API calls, pa.* mocked."""
import unittest, sys, os
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(__file__))
import check_payment_connected as cpc

PAYMENT_MSG = ("You must connect at least one payment method before you can "
               "publish this product for sale")


class TestCheck(unittest.TestCase):
    def test_no_key(self):
        with patch("check_payment_connected.gu.get_key", return_value=None):
            ok, detail = cpc.check()
        self.assertFalse(ok)
        self.assertEqual(detail, "NO_KEY")

    def test_no_drafts_treated_as_ready(self):
        with patch("check_payment_connected.gu.get_key", return_value="k"), \
             patch("check_payment_connected.pa.list_products",
                   return_value=[{"id": "p1", "published": True}]):
            ok, detail = cpc.check()
        self.assertTrue(ok)

    def test_payment_not_connected(self):
        with patch("check_payment_connected.gu.get_key", return_value="k"), \
             patch("check_payment_connected.pa.list_products",
                   return_value=[{"id": "p1", "published": False}]), \
             patch("check_payment_connected.pa.enable", return_value=(False, PAYMENT_MSG)):
            ok, detail = cpc.check()
        self.assertFalse(ok)
        self.assertIn("WAIT_FOR_PAYMENT", detail)

    def test_payment_connected(self):
        with patch("check_payment_connected.gu.get_key", return_value="k"), \
             patch("check_payment_connected.pa.list_products",
                   return_value=[{"id": "p1", "published": False}]), \
             patch("check_payment_connected.pa.enable", return_value=(True, "ok")):
            ok, detail = cpc.check()
        self.assertTrue(ok)

    def test_probe_other_failure_not_treated_as_payment(self):
        with patch("check_payment_connected.gu.get_key", return_value="k"), \
             patch("check_payment_connected.pa.list_products",
                   return_value=[{"id": "p1", "published": False}]), \
             patch("check_payment_connected.pa.enable", return_value=(False, "rate limited")):
            ok, detail = cpc.check()
        self.assertFalse(ok)
        self.assertIn("PROBE_FAIL", detail)


if __name__ == "__main__":
    unittest.main()
