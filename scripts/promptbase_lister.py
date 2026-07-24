"""PromptBase Agent-Skill Lister via CDP (autonomous fill, user-confirmed publish).

UPDATED 2026-07-24 (fix 2): the live /sell form has 9 fields (not 6). The
previous version omitted Example #2 (user+agent) and Setup instructions, which
left the form INVALID (red "Please add 2 examples" + "Please provide
information to a buyer" errors). This version fills ALL 9 fields + model select.

Form field map (index-free by placeholder):
  input[0] Skill name            (ph: 'my-cool-skill')
  input[1] When to use           (ph: 'Use when the user asks to...')
  input[2] Overview (# markdown) (ph: '# Overview...')
  input[3] Tools                 (ph: 'Read, Edit, Bash')
  input[4] Example 1 prompt      (ph: 'Split this branch into reviewable PRs')
  input[5] Example 1 response    (ph: 'Sure! I analysed...')
  input[6] Example 2 prompt      (ph: 'Split this branch into reviewable PRs')
  input[7] Example 2 response    (ph: 'Sure! I analysed...')
  input[8] Setup instructions    (ph: 'Install at ~/.cursor/skills/...')
  select[0] ChatGPT model version (gpt-5.5)

The final Publish click is GATED: user must say 'go', and the wizard also needs
Payout-Enable (user bank data) which is NOT autonomous.
"""
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_helper as c


SKILLS = [
    {
        "name": "commit-message-writer",
        "title": "Commit Message Writer — Clean Git Commits (ChatGPT Skill)",
        "when": "Use when the user has staged git changes, a diff, or a changed-file list and needs a conventional, review-ready commit message.",
        "overview": "# Overview\n\nTurns any git diff or changed-file list into a conventional, review-ready commit. Auto-detects feat/fix/refactor/docs/test/chore/perf, writes an imperative subject (<=50 chars), adds a why-body only when needed, and suggests splitting mixed changes. Matches DE/EN.",
        "tools": "Read, Bash, Git",
        "example1_prompt": "Write a commit for these staged changes:\n- src/auth.ts: added JWT refresh\n- tests: covered token rotation",
        "example1_response": "fix(auth): rotate JWT refresh tokens on expiry\n\nAdds silent refresh before 401s reach the client. Covered by auth.rotation.test.ts.",
        "example2_prompt": "Commit these: renamed utils, fixed typo in README",
        "example2_response": "chore(utils): rename helpers for clarity\ndocs: fix README typo",
        "setup": "Install as a Cursor/Claude skill. Save SKILL.md to ~/.cursor/skills/commit-message-writer/SKILL.md (or your agent's skills dir), then reference it in your agent config. Needs Git + Read/Bash access to your repo.",
        "model": "gpt-5.5",
    },
    {
        "name": "ci-pipeline-trier",
        "title": "CI/CD Failure Trier — Why Your Build Broke (Claude Skill)",
        "when": "Use when a CI/CD pipeline failed (GitHub Actions, GitLab CI, etc.) and the user pastes the raw log.",
        "overview": "# Overview\n\nIsolates the FIRST red line from CI noise, classifies it (build/test/lint/deploy/infra), explains it, and gives the minimal fix plus a prevention line. Flaky runs are named, not masked by bigger timeouts. Secrets redacted.",
        "tools": "Read, Bash, WebFetch",
        "example1_prompt": "GitHub Actions failed:\n<log with 200 lines, error at step 'test'>",
        "example1_response": "FAIL at step 'test': vitest exited 1 — 1 test timed out (auth.test.ts). Not a flake: it's a real timeout. Fix: raise test timeout to 10s. Prevention: add per-test timeout in vitest config.",
        "example2_prompt": "GitLab CI: deploy job failed, error 'permission denied'",
        "example2_response": "FAIL at 'deploy': SSH key missing deploy scope. Fix: add CI_DEPLOY_KEY with write access. Prevention: pin key to the deploy user only.",
        "setup": "Save SKILL.md to your agent skills dir (~/.cursor/skills/ci-pipeline-trier/). Needs Read + Bash + WebFetch. Point it at your CI log URL or paste the raw log.",
        "model": "gpt-5.5",
    },
    {
        "name": "root-cause-debugger",
        "title": "Root-Cause Debugger — Find The Bug (Claude Skill)",
        "when": "Use when the user pastes an error, stack trace, or a 'works locally, not in prod' report.",
        "overview": "# Overview\n\n4 phases: reproduce, localize, hypothesize, verify. Output: SYMPTOM / ROOT CAUSE / EVIDENCE / NEXT CHECK / FIX. Suspect vs known is labeled. No code edits before the hypothesis is testable.",
        "tools": "Read, Bash, Grep",
        "example1_prompt": "Prod error: 'Cannot read properties of undefined (reading id)' on checkout",
        "example1_response": "SYMPTOM: undefined.id on checkout.\nROOT CAUSE: cart line item missing SKU after partial migration.\nEVIDENCE: line 142 maps sku only if variant set.\nFIX: default sku in cart reducer.",
        "example2_prompt": "Local works, staging 500 on upload",
        "example2_response": "SYMPTOM: 500 on upload in staging only.\nROOT CAUSE: staging S3 bucket missing CORS rule.\nEVIDENCE: preflight OPTIONS returns 403.\nFIX: add CORS allow-origin for the app domain.",
        "setup": "Save SKILL.md to your agent skills dir. Needs Read + Bash + Grep. Works on any stack — paste the stack trace or error message.",
        "model": "gpt-5.5",
    },
    {
        "name": "daily-standup-writer",
        "title": "Daily Standup Writer — Standup From Commits (ChatGPT Skill)",
        "when": "Use when the user has git commits, a diff, or messy bullets and needs a tight daily standup.",
        "overview": "# Overview\n\nTurns raw commits/diff/bullets into a standup: GESTERN / HEUTE / BLOCKER, each 1-3 bullets, outcome-led not activity-led, under 120 words. Matches DE/EN.",
        "tools": "Read, Bash, Git",
        "example1_prompt": "My commits today: fix login, refactor api, wip docs",
        "example1_response": "GESTERN: Login race fixed, API refactored.\nHEUTE: Docs, start billing webhook.\nBLOCKER: none.",
        "example2_prompt": "Standup from: finished auth, started search, blocked on API key",
        "example2_response": "GESTERN: Auth completed.\nHEUTE: Search indexing.\nBLOCKER: Waiting on prod API key from infra.",
        "setup": "Save SKILL.md to your agent skills dir. Needs Git + Read/Bash access to the repo for commit context.",
        "model": "gpt-5.5",
    },
    {
        "name": "messy-data-cleaner",
        "title": "Messy CSV Cleaner — Dedupe, Fix, Normalize (ChatGPT Skill)",
        "when": "Use when the user pastes a dirty CSV/table that needs cleaning before analysis.",
        "overview": "# Overview\n\nCleans a dirty CSV: trim, unify casing, parse dates to ISO, coerce numbers, drop exact duplicates, flag near-dups. Returns issues found, cleaned data, and a tool-agnostic recipe (pandas/Excel/SQL). Uncertain values flagged, never overwritten.",
        "tools": "Read, Bash, Python",
        "example1_prompt": "Clean this CSV:\nname,date,price\nBob,01/02/24,1.000\nbob,2024-02-01,1000",
        "example1_response": "Issues: mixed date formats, dup 'Bob' (case), '1.000' vs '1000'. Cleaned: 1 row, date=2024-02-01, price=1000.",
        "example2_prompt": "Normalize: ' yes ', 'YES', 'No ', 'no'",
        "example2_response": "Issues: casing + whitespace. Cleaned: ['yes','yes','no','no'] -> boolean column.",
        "setup": "Save SKILL.md to your agent skills dir. Needs Read + Python/Bash for the cleaning recipe. Paste raw CSV or point at a file.",
        "model": "gpt-5.5",
    },
    {
        "name": "test-case-generator",
        "title": "Test Case Generator — Edge Cases & Coverage (Claude Skill)",
        "when": "Use when the user pastes a function, endpoint, or feature spec and needs runnable test cases.",
        "overview": "# Overview\n\nGenerates test cases: happy path, edge cases (null/boundary/unicode), failure modes (bad input, timeout, 5xx). Each prioritized P0/P1/P2 in given/when/then, ending with a coverage-gap note. One assertion per case.",
        "tools": "Read, Bash, Grep",
        "example1_prompt": "Function: divide(a,b) returns a/b",
        "example1_response": "P0: given 6,3 -> 2. P1: given 1,0 -> throws. P1: given 0,5 -> 0. P2: given 'a',2 -> throws (type). Gap: negative bases untested.",
        "example2_prompt": "Endpoint: GET /users/:id returns user or 404",
        "example2_response": "P0: valid id -> 200 + user. P0: missing id -> 404. P1: id=-1 -> 404. P1: id=0 -> 404. Gap: auth on the endpoint untested.",
        "setup": "Save SKILL.md to your agent skills dir. Needs Read + Grep. Paste a function signature, endpoint, or spec.",
        "model": "gpt-5.5",
    },
    {
        "name": "clean-code-reviewer",
        "title": "Senior Code Reviewer — Bugs Before Ship (Claude Skill)",
        "when": "Use when the user pastes a diff, PR, or snippet for review.",
        "overview": "# Overview\n\nReviews like a strict senior: (1) Correctness (2) Security (3) Edge cases (4) Clarity. Output: [PASS 1-4] SEVERITY — file:line — fix, ending in VERDICT: ship | ship-with-fixes | block. Smallest fix preferred, never guesses.",
        "tools": "Read, Bash, Grep",
        "example1_prompt": "Review this PR diff:\n+ def get(u): return db[u.id]",
        "example1_response": "[PASS 1-3] INFO — get(): no None-check on u. [PASS 4] WARN — no guard. VERDICT: ship-with-fixes — add `if not u: return None`.",
        "example2_prompt": "Review: + password = input('pw')  # stored in var",
        "example2_response": "[PASS 2] HIGH — password in plaintext var, never hashed, risk of leak in logs/memory. VERDICT: block — hash with bcrypt, never store raw.",
        "setup": "Save SKILL.md to your agent skills dir. Needs Read + Grep + Bash. Paste a diff, PR link, or snippet.",
        "model": "gpt-5.5",
    },
]


def _wait_for_inputs(min_n=9, timeout=20):
    """Poll until the active /sell form has >= min_n placeholder inputs."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        n = c.eval_tab("sell", """
(function(){
  var els=[...document.querySelectorAll('input[type=text],textarea')].filter(e=>e.placeholder||e.tagName==='TEXTAREA');
  return els.length;
})()
""")
        try:
            if int(n) >= min_n:
                return int(n)
        except (ValueError, TypeError):
            pass
        time.sleep(1)
    return 0


def _select_step1(item_type="Agent Skill", gen="Text", price="$2.99"):
    """Step 1/4: pick item type + generation + price, then click Next: Prompt.
    Returns a status string."""
    r = c.eval_tab("sell", """
(function(itemType, gen, price){
  function pick(selIdx, txt){
    var s=document.querySelectorAll('select')[selIdx];
    if(!s) return 'NO_SEL:'+selIdx;
    txt=(txt||'').toLowerCase().trim();
    for(var j=0;j<s.options.length;j++){
      var ot=(s.options[j].text||'').toLowerCase().trim();
      if(ot.indexOf(txt)>=0){ var p=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set; p.call(s,s.options[j].value); s.dispatchEvent(new Event('change',{bubbles:true})); return 'SEL'+selIdx+'='+s.value; }
    }
    return 'OPTNF:'+selIdx;
  }
  var a=pick(0,itemType);   // item type -> Agent Skill
  var b=pick(1,gen);        // generation -> Text
  var d=pick(3,price);      // price -> $2.99
  // click "Next: Prompt" button
  var btns=[...document.querySelectorAll('button,div.action-button,a')];
  for(var e of btns){ if((e.innerText||'').indexOf('Next')>=0){ e.click(); return a+'|'+b+'|'+d+'|CLICKED_NEXT'; } }
  return a+'|'+b+'|'+d+'|NO_NEXT_BTN';
})(%r,%r,%r)
""" % (item_type, gen, price))
    return r


def fill_skill(skill):
    """Full autonomous fill of one Agent Skill: Step1 (type+price) -> Next ->
    wait for 9-field skill form -> fill all 9 + model. NO publish click.
    Returns [status_string]."""
    c.navigate_tab("sell", "https://promptbase.com/sell")
    time.sleep(3)
    step1 = _select_step1()
    time.sleep(3)
    # wait for the 9-field skill form to appear
    n = _wait_for_inputs(9, timeout=20)
    if n < 9:
        return ["STEP1_ONLY inputs=" + str(n) + " step1=" + step1]
    sk_json = json.dumps({
        "name": skill["name"], "when": skill["when"], "overview": skill["overview"],
        "tools": skill["tools"],
        "example1_prompt": skill["example1_prompt"], "example1_response": skill["example1_response"],
        "example2_prompt": skill["example2_prompt"], "example2_response": skill["example2_response"],
        "setup": skill["setup"], "model": skill["model"],
    })
    res = c.eval_tab("sell", """
(function(sk){
  function setEl(el,val){
    var proto=Object.getOwnPropertyDescriptor(
      el.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype,'value').set;
    proto.call(el,val);
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  }
  function setSel(selIdx,txt){
    var s=document.querySelectorAll('select')[selIdx];
    if(!s) return 'NO_SELECT:'+selIdx;
    txt=(txt||'').toLowerCase().trim();
    for(var j=0;j<s.options.length;j++){
      var ot=(s.options[j].text||'').toLowerCase().trim();
      var ov=(s.options[j].value||'').toLowerCase().trim();
      if(ot===txt||ov===txt||ot.indexOf(txt)>=0||ov.indexOf(txt)>=0){
        var p=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;
        p.call(s,s.options[j].value);
        s.dispatchEvent(new Event('change',{bubbles:true}));
        return 'SEL='+s.value;
      }
    }
    return 'OPT_NOT_FOUND:'+selIdx;
  }
  var els=[...document.querySelectorAll('input[type=text],textarea')].filter(e=>e.placeholder||e.tagName==='TEXTAREA');
  if(els.length<9) return 'TOO_FEW_INPUTS:'+els.length;
  setEl(els[0], sk.name);
  setEl(els[1], sk.when);
  setEl(els[2], sk.overview);
  setEl(els[3], sk.tools);
  setEl(els[4], sk.example1_prompt);
  setEl(els[5], sk.example1_response);
  setEl(els[6], sk.example2_prompt);
  setEl(els[7], sk.example2_response);
  setEl(els[8], sk.setup);
  var selRes = setSel(0, sk.model);
  return 'OK fields='+els.length+' name='+els[0].value.slice(0,20)+' | '+selRes;
})(%s)
""" % sk_json)
    return [step1 + " || " + res]


def validate_form():
    """Return red error messages currently visible on the form (empty list = valid)."""
    txt = c.eval_tab("sell", "document.body.innerText")
    import re
    # crude: lines that look like validation errors
    errs = [l.strip() for l in (txt or "").split("\n")
            if l.strip().lower().startswith(("please ", "error", "required", "must "))]
    return errs


def main():
    c.navigate_tab("sell", "https://promptbase.com/sell")
    time.sleep(4)
    res = fill_skill(SKILLS[0])
    print("DRY-RUN (Skill 1):", SKILLS[0]["title"])
    print("  ", res[0])
    errs = validate_form()
    print("  FORM ERRORS:", errs if errs else "NONE")
    print("\n>>> NO PUBLISH CLICKED. Awaiting user 'go' for publish.")


if __name__ == "__main__":
    main()
