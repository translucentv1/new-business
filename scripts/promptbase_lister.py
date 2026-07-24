"""PromptBase Agent-Skill Lister via CDP (autonomous fill, user-confirmed publish).

UPDATED 2026-07-24: PromptBase /sell now uses the structured SKILL.md form
(no more flat "Agent Skill" item-type select). Fields (index-free by
placeholder):
  input[0]  Skill name            (ph: 'my-cool-skill')
  input[1]  When to use           (ph: 'Use when the user asks to...')
  input[2]  Overview (# markdown) (ph: '# Overview...')
  input[3]  Tools                 (ph: 'Read, Edit, Bash')
  input[4]  Example prompt        (ph: 'Split this branch into reviewable PRs')
  input[5]  Example response      (ph: 'Sure! I analysed...')
  select[0] ChatGPT model version (gpt-5.5)
Price is set in a later step (publish flow); this module only fills step 1.

The final Publish click is GATED: caller must pass confirm_publish=True AND
the user must have said "go".
"""
import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_helper as c


# 7 Agent Skills mapped to the new SKILL.md-style form
SKILLS = [
    {
        "name": "commit-message-writer",
        "title": "Commit Message Writer — Clean Git Commits (ChatGPT Skill)",
        "when": "Use when the user has staged git changes, a diff, or a changed-file list and needs a conventional, review-ready commit message.",
        "overview": "# Overview\n\nTurns any git diff or changed-file list into a conventional, review-ready commit. Auto-detects feat/fix/refactor/docs/test/chore/perf, writes an imperative subject (<=50 chars), adds a why-body only when needed, and suggests splitting mixed changes. Matches DE/EN.",
        "tools": "Read, Bash, Git",
        "example_prompt": "Write a commit for these staged changes:\n- src/auth.ts: added JWT refresh\n- tests: covered rotation",
        "example_response": "fix(auth): rotate JWT refresh tokens on expiry\n\nAdds silent refresh before 401s reach the client. Covered by auth.rotation.test.ts.",
        "model": "gpt-5.5",
    },
    {
        "name": "ci-pipeline-trier",
        "title": "CI/CD Failure Trier — Why Your Build Broke (Claude Skill)",
        "when": "Use when a CI/CD pipeline failed (GitHub Actions, GitLab CI, etc.) and the user pastes the raw log.",
        "overview": "# Overview\n\nIsolates the FIRST red line from CI noise, classifies it (build/test/lint/deploy/infra), explains it, and gives the minimal fix plus a prevention line. Flaky runs are named, not masked by bigger timeouts. Secrets redacted.",
        "tools": "Read, Bash, WebFetch",
        "example_prompt": "GitHub Actions failed:\n<log with 200 lines, error at step 'test'>",
        "example_response": "FAIL at step 'test': vitest exited 1 — 1 test timed out (auth.test.ts). Not a flake: it's a real timeout. Fix: raise test timeout to 10s. Prevention: add per-test timeout in vitest config.",
        "model": "gpt-5.5",
    },
    {
        "name": "root-cause-debugger",
        "title": "Root-Cause Debugger — Find The Bug (Claude Skill)",
        "when": "Use when the user pastes an error, stack trace, or a 'works locally, not in prod' report.",
        "overview": "# Overview\n\n4 phases: reproduce, localize, hypothesize, verify. Output: SYMPTOM / ROOT CAUSE / EVIDENCE / NEXT CHECK / FIX. Suspect vs known is labeled. No code edits before the hypothesis is testable.",
        "tools": "Read, Bash, Grep",
        "example_prompt": "Prod error: 'Cannot read properties of undefined (reading id)' on checkout",
        "example_response": "SYMPTOM: undefined.id on checkout.\nROOT CAUSE: cart line item missing SKU after partial migration.\nEVIDENCE: line 142 maps sku only if variant set.\nFIX: default sku in cart reducer.",
        "model": "gpt-5.5",
    },
    {
        "name": "daily-standup-writer",
        "title": "Daily Standup Writer — Standup From Commits (ChatGPT Skill)",
        "when": "Use when the user has git commits, a diff, or messy bullets and needs a tight daily standup.",
        "overview": "# Overview\n\nTurns raw commits/diff/bullets into a standup: GESTERN / HEUTE / BLOCKER, each 1-3 bullets, outcome-led not activity-led, under 120 words. Matches DE/EN.",
        "tools": "Read, Bash, Git",
        "example_prompt": "My commits today: fix login, refactor api, wip docs",
        "example_response": "GESTERN: Login race fixed, API refactored.\nHEUTE: Docs, start billing webhook.\nBLOCKER: none.",
        "model": "gpt-5.5",
    },
    {
        "name": "messy-data-cleaner",
        "title": "Messy CSV Cleaner — Dedupe, Fix, Normalize (ChatGPT Skill)",
        "when": "Use when the user pastes a dirty CSV/table that needs cleaning before analysis.",
        "overview": "# Overview\n\nCleans a dirty CSV: trim, unify casing, parse dates to ISO, coerce numbers, drop exact duplicates, flag near-dups. Returns issues found, cleaned data, and a tool-agnostic recipe (pandas/Excel/SQL). Uncertain values flagged, never overwritten.",
        "tools": "Read, Bash, Python",
        "example_prompt": "Clean this CSV:\nname,date,price\nBob,01/02/24,1.000\nbob,2024-02-01,1000",
        "example_response": "Issues: mixed date formats, dup 'Bob' (case), '1.000' vs '1000'. Cleaned: 1 row, date=2024-02-01, price=1000.",
        "model": "gpt-5.5",
    },
    {
        "name": "test-case-generator",
        "title": "Test Case Generator — Edge Cases & Coverage (Claude Skill)",
        "when": "Use when the user pastes a function, endpoint, or feature spec and needs runnable test cases.",
        "overview": "# Overview\n\nGenerates test cases: happy path, edge cases (null/boundary/unicode), failure modes (bad input, timeout, 5xx). Each prioritized P0/P1/P2 in given/when/then, ending with a coverage-gap note. One assertion per case.",
        "tools": "Read, Bash, Grep",
        "example_prompt": "Function: divide(a,b) returns a/b",
        "example_response": "P0: given 6,3 -> 2. P1: given 1,0 -> throws. P1: given 0,5 -> 0. P2: given 'a',2 -> throws (type). Gap: negative bases untested.",
        "model": "gpt-5.5",
    },
    {
        "name": "clean-code-reviewer",
        "title": "Senior Code Reviewer — Bugs Before Ship (Claude Skill)",
        "when": "Use when the user pastes a diff, PR, or snippet for review.",
        "overview": "# Overview\n\nReviews like a strict senior: (1) Correctness (2) Security (3) Edge cases (4) Clarity. Output: [PASS 1-4] SEVERITY — file:line — fix, ending in VERDICT: ship | ship-with-fixes | block. Smallest fix preferred, never guesses.",
        "tools": "Read, Bash, Grep",
        "example_prompt": "Review this PR diff:\n+ def get(u): return db[u.id]",
        "example_response": "[PASS 1-3] INFO — get(): no None-check on u. [PASS 4] WARN — no guard. VERDICT: ship-with-fixes — add `if not u: return None`.",
        "model": "gpt-5.5",
    },
]


def _set_input_by_placeholder(idx, value):
    return c.eval_tab("sell", """
(function(idx,val){
  var els=[...document.querySelectorAll('input[type=text],textarea')].filter(e=>e.placeholder||e.tagName==='TEXTAREA');
  var e=els[idx];
  if(!e) return 'NO_INPUT_IDX:'+idx+'/'+els.length;
  var proto=Object.getOwnPropertyDescriptor(
    e.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype,'value').set;
  proto.call(e,val);
  e.dispatchEvent(new Event('input',{bubbles:true}));
  e.dispatchEvent(new Event('change',{bubbles:true}));
  return 'SET['+idx+']='+e.value.slice(0,20);
})(%d,%r)
""" % (idx, repr(value)))


def _set_select_by_text(idx, text):
    return c.eval_tab("sell", """
(function(idx,txt){
  var s=document.querySelectorAll('select')[idx];
  if(!s) return 'NO_SELECT:'+idx;
  txt=(txt||'').toLowerCase().trim();
  for(var j=0;j<s.options.length;j++){
    var ot=(s.options[j].text||'').toLowerCase().trim();
    var ov=(s.options[j].value||'').toLowerCase().trim();
    if(ot===txt || ov===txt || ot.indexOf(txt)>=0 || ov.indexOf(txt)>=0){
      var proto=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;
      proto.call(s, s.options[j].value);
      s.dispatchEvent(new Event('change',{bubbles:true}));
      return 'SEL['+idx+']='+s.value;
    }
  }
  return 'OPT_NOT_FOUND:'+idx+':/'+s.options.length+' opts='+[...s.options].map(o=>o.text).join('|');
})(%d,%r)
""" % (idx, repr(text)))


def fill_skill(skill):
    """Fill the structured SKILL.md form for one skill. NO clicks. Returns steps."""
    r = []
    r.append(_set_input_by_placeholder(0, skill["name"]))
    r.append(_set_input_by_placeholder(1, skill["when"]))
    r.append(_set_input_by_placeholder(2, skill["overview"]))
    r.append(_set_input_by_placeholder(3, skill["tools"]))
    r.append(_set_input_by_placeholder(4, skill["example_prompt"]))
    r.append(_set_input_by_placeholder(5, skill["example_response"]))
    # model select LAST — SPA rebuilds it after input events, so set after all inputs
    time.sleep(1)
    r.append(_set_select_by_text(0, skill["model"]))
    return r


def main():
    # DRY RUN: fill first skill only, print steps, NO publish
    c.navigate_tab("sell", "https://promptbase.com/sell")
    time.sleep(4)
    steps = fill_skill(SKILLS[0])
    print("DRY-RUN (Skill 1):", SKILLS[0]["title"])
    for s in steps:
        print("  ", s)
    print("\n>>> NO PUBLISH CLICKED. Awaiting user 'go' for publish.")


if __name__ == "__main__":
    main()
