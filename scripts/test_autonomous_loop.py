import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import autonomous_loop as loop

def test_loop_runs_without_key(tmp_path=None):
    # simuliere: kein Key -> Entwurf-Modus, kein Crash
    import importlib
    import gumroad_uploader as gu
    # ensure no key
    os.environ.pop("GUMROAD_API_KEY", None)
    importlib.reload(gu)
    # loop.main should not raise
    loop.main()
    print("test_loop_runs_without_key PASS (no crash, entwurf mode)")

if __name__ == "__main__":
    test_loop_runs_without_key()
    print("ALL TESTS PASS")
