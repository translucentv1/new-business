import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import sale_poller as sp

def test_record_and_lastseen():
    d = tempfile.mkdtemp()
    sp.SALES_LOG = os.path.join(d, "sales.log")
    sp.REINVEST_LOG = os.path.join(d, "reinvest.log")
    sp.record_sale({"ts": 1000, "price": 490, "email": "a@b.c"})
    assert sp._last_seen_ts() == 1000, "last_seen should be 1000"
    sp.reinvest(490)
    assert os.path.exists(sp.REINVEST_LOG), "reinvest not logged"
    print("test_record_and_lastseen PASS")

def test_poll_no_key():
    # ensure no key
    os.environ.pop("GUMROAD_API_KEY", None)
    p = os.path.abspath(os.path.join(os.path.dirname(sp.__file__), "..", ".gumroad_secrets"))
    # no secrets file -> get_key None
    n, det = sp.poll()
    assert n == 0 and det == "NO_KEY", f"expected NO_KEY, got {det}"
    print("test_poll_no_key PASS")

if __name__ == "__main__":
    test_record_and_lastseen()
    test_poll_no_key()
    print("ALL TESTS PASS")
