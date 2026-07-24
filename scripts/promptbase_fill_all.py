"""PromptBase mass-fill runner (autonomous fill, NO publish).

Fills all 7 Agent-Skills (new SKILL.md form) from promptbase_lister.SKILLS into
the open Chrome (CDP port 9223, promptbase.com/sell). Reloads /sell fresh per
skill (resets SPA). Stops before publish — caller says 'go' for publish.

Usage: python scripts/promptbase_fill_all.py
"""
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import promptbase_lister as P
import cdp_helper as c


def fill_one(skill):
    c.navigate_tab("sell", "https://promptbase.com/sell")
    time.sleep(4)
    return P.fill_skill(skill)


def main():
    total = len(P.SKILLS)
    print(f"FILLING {total} skills (new SKILL.md form, no publish)...")
    ok = 0
    for i, sk in enumerate(P.SKILLS):
        print(f"\n=== Skill {i+1}/{total}: {sk['title'][:45]} ===")
        steps = fill_one(sk)
        for s in steps:
            print("  ", s)
            if s.startswith(("SET[", "SEL[")):
                ok += 1
        time.sleep(1)
    print(f"\nDONE. field-sets applied: {ok}. NO PUBLISH CLICKED.")
    print(">>> Awaiting user 'go' for publish.")


if __name__ == "__main__":
    main()
