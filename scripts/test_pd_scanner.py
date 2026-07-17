import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from pd_scanner import strip_gutenberg_header

def test_strip_header():
    sample = "*** START OF THE PROJECT GUTENBERG EBOOK ***\nHallo Welt,\ndas ist der Text.\n*** END OF THE PROJECT GUTENBERG EBOOK ***"
    out = strip_gutenberg_header(sample)
    assert "START OF" not in out, "header not stripped"
    assert "END OF" not in out, "footer not stripped"
    assert "Hallo Welt" in out, "body lost"
    print("test_strip_header PASS")

def test_no_markers():
    out = strip_gutenberg_header("Nur Text ohne Marker.")
    assert out == "Nur Text ohne Marker.", "should return as-is"
    print("test_no_markers PASS")

if __name__ == "__main__":
    test_strip_header()
    test_no_markers()
    print("ALL TESTS PASS")
