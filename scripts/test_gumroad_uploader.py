import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from gumroad_uploader import build_payload

def test_build_payload_default_free():
    # nutzt corpus/11 vorhandenes Bundle
    p, prod = build_payload("11")
    assert p["name"], "name missing"
    assert "Public Domain" in p["description"], "desc should mention PD"
    assert p["price"] == 0, f"default price should be 0 (free/NYP), got {p['price']}"
    assert p["published"] is True, "should publish"
    assert os.path.isdir(prod), "product dir missing"
    print("test_build_payload_default_free PASS")

def test_build_payload_price_env():
    os.environ["PD_PRICE_CENTS"] = "490"
    p, _ = build_payload("11")
    assert p["price"] == 490, f"env price override failed: {p['price']}"
    del os.environ["PD_PRICE_CENTS"]
    print("test_build_payload_price_env PAS")

if __name__ == "__main__":
    test_build_payload_default_free()
    test_build_payload_price_env()
    print("ALL TESTS PASS")
