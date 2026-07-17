import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import sale_webhook as wh

def test_verify_signature():
    os.environ["GUMROAD_WEBHOOK_SECRET"] = "testsecret"
    import hmac, hashlib
    body = b'{"price":490}'
    sig = hmac.new(b"testsecret", body, hashlib.sha256).hexdigest()
    assert wh.verify_signature(body, sig) is True, "valid sig rejected"
    assert wh.verify_signature(body, "wrong") is False, "bad sig accepted"
    # cleanup
    del os.environ["GUMROAD_WEBHOOK_SECRET"]
    import importlib
    importlib.reload(wh)
    print("test_verify_signature PASS")

def test_handle_ping_logs(tmp_path=None):
    # sale log + reinvest log werden geschrieben
    old = wh.SALES_LOG
    import tempfile
    d = tempfile.mkdtemp()
    wh.SALES_LOG = os.path.join(d, "sales.log")
    wh.REINVEST_LOG = os.path.join(d, "reinvest.log")
    ok, msg = wh.handle_ping({"price": 490, "email": "x@y.z"})
    assert ok, "handle_ping failed"
    assert os.path.exists(wh.SALES_LOG), "sale not logged"
    assert os.path.exists(wh.REINVEST_LOG), "reinvest not logged"
    lines = open(wh.REINVEST_LOG, encoding="utf-8").read().strip().splitlines()
    assert "490" in lines[0], "reinvest amount wrong"
    wh.SALES_LOG = old
    print("test_handle_ping_logs PASS")

if __name__ == "__main__":
    test_verify_signature()
    test_handle_ping_logs()
    print("ALL TESTS PASS")
