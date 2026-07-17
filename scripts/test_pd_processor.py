import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from pd_processor import split_chapters, build_index

def test_split_chapters():
    text = "Front matter here.\nChapter 1. The Beginning\nAlice fell down.\nChapter 2. The Garden\nShe grew.\n"
    ch = split_chapters(text)
    assert len(ch) >= 2, "should detect 2 chapters + front"
    assert ch[0][0] == "Vorspann", f"front expected, got {ch[0][0]}"
    assert ch[1][0] == "1", f"chap1 num, got {ch[1][0]}"
    assert "Alice fell" in ch[1][2], "body lost"
    print("test_split_chapters PASS")

def test_build_index():
    ch = [("Vorspann", "", "x"), ("1", "The Beginning", "y"), ("2", "The Garden", "z")]
    idx = build_index(ch)
    # enumerate starts at 1 -> Vorspann is entry 1, The Beginning entry 2
    assert "1. Vorspann" in idx, "index missing front"
    assert "2. The Beginning" in idx, "index missing chap1"
    assert "3. The Garden" in idx, "index missing chap2"
    print("test_build_index PASS")

if __name__ == "__main__":
    test_split_chapters()
    test_build_index()
    print("ALL TESTS PASS")
