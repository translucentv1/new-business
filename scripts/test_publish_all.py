"""Tests for publish_all.py: enable(), is_payment_error(), payment-gated main().
No real API calls -- httpx is mocked."""
import unittest, sys, os
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(__file__))
import publish_all as pa

PAYMENT_MSG = ("You must connect at least one payment method before you can "
               "publish this product for sale")


class FakeResp:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text or str(self._json)

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class TestIsPaymentError(unittest.TestCase):
    def test_matches(self):
        self.assertTrue(pa.is_payment_error(PAYMENT_MSG))

    def test_no_match(self):
        self.assertFalse(pa.is_payment_error("some other error"))
        self.assertFalse(pa.is_payment_error(""))
        self.assertFalse(pa.is_payment_error(None))


class TestEnable(unittest.TestCase):
    def test_enable_ok(self):
        with patch("publish_all.httpx.put", return_value=FakeResp(200, {"success": True})):
            ok, detail = pa.enable("pid1", "key1")
        self.assertTrue(ok)

    def test_enable_payment_error(self):
        with patch("publish_all.httpx.put",
                    return_value=FakeResp(200, {"success": False, "message": PAYMENT_MSG})):
            ok, detail = pa.enable("pid1", "key1")
        self.assertFalse(ok)
        self.assertTrue(pa.is_payment_error(detail))

    def test_enable_req_err_no_crash(self):
        with patch("publish_all.httpx.put", side_effect=RuntimeError("boom")):
            ok, detail = pa.enable("pid1", "key1")
        self.assertFalse(ok)
        self.assertIn("REQ_ERR", detail)


class TestMainPaymentGate(unittest.TestCase):
    def test_main_exits_clean_on_payment_error(self):
        prods = [{"id": "p1", "published": False, "short_url": "x"}]
        with patch("publish_all.gu.get_key", return_value="key1"), \
             patch("publish_all.list_products", return_value=prods), \
             patch("publish_all.enable", return_value=(False, PAYMENT_MSG)) as m_enable, \
             patch("publish_all.gu.publish") as m_publish:
            pa.main()  # must not raise
        m_enable.assert_called_once()
        m_publish.assert_not_called()  # returned before reaching MISSING loop

    def test_main_no_key_no_crash(self):
        with patch("publish_all.gu.get_key", return_value=None), \
             patch("publish_all.list_products") as m_list:
            pa.main()
        m_list.assert_not_called()

    def test_main_publishes_missing_when_connected(self):
        with patch("publish_all.gu.get_key", return_value="key1"), \
             patch("publish_all.list_products", return_value=[]), \
             patch("publish_all.gu.publish", return_value=(True, "DRAFT pid=abc price=399")), \
             patch("publish_all.enable", return_value=(True, "ok")) as m_enable:
            pa.main()
        self.assertEqual(m_enable.call_count, len(pa.MISSING))


if __name__ == "__main__":
    unittest.main()
