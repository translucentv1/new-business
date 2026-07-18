"""Tests for autonomous_sell_loop.py -- cpc/pa/sp all mocked, no real API calls."""
import unittest, sys, os
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(__file__))
import autonomous_sell_loop as asl


class TestAutonomousSellLoop(unittest.TestCase):
    def test_wait_state_skips_publish_and_poll(self):
        with patch("autonomous_sell_loop.cpc.check", return_value=(False, "WAIT_FOR_PAYMENT: ...")), \
             patch("autonomous_sell_loop.pa.main") as m_pub, \
             patch("autonomous_sell_loop.sp.poll") as m_poll:
            asl.main()
        m_pub.assert_not_called()
        m_poll.assert_not_called()

    def test_ready_state_runs_publish_then_poll(self):
        with patch("autonomous_sell_loop.cpc.check", return_value=(True, "PAYMENT_CONNECTED")), \
             patch("autonomous_sell_loop.pa.main") as m_pub, \
             patch("autonomous_sell_loop.sp.poll", return_value=(0, "poll ok, 0 new sales")) as m_poll:
            asl.main()
        m_pub.assert_called_once()
        m_poll.assert_called_once()


if __name__ == "__main__":
    unittest.main()
