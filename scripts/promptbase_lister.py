"""PromptBase Agent-Skill Lister via CDP (autonomous, user-confirmed publish).

Flow per listing (from LISTING-TEXTE.md, all $2.99 Sprint-Preis):
  Step 1/3 Prompt Details: item type=Agent Skill, generation=Text,
    model, name, description, price.
  Step 2/3 Upload SKILL.md.
  Step 3/3 Preview/Publish.

This module ONLY fills + navigates. The final Publish click is gated:
caller must pass confirm_publish=True AND the user must have said "go".

React-compatible input setter: React ignores el.value=, so we use the
native value setter + dispatch an 'input' event.
"""
import json, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_helper as c


LISTINGS = [
    {"title": "Commit Message Writer — Clean Git Commits (ChatGPT Skill)",
     "model": "ChatGPT", "type": "Agent Skill", "gen": "Text",
     "cat": "Git / Productivity", "price": "2.99",
     "tags": "commit message, git commit, conventional commits, git, chatgpt skill, productivity, PR",
     "desc": "Turn any git diff or changed-file list into a conventional, review-ready commit. Auto-detects feat/fix/refactor/docs/test/chore/perf, writes an imperative subject (<=50 chars), adds a why-body only when needed, and suggests splitting mixed changes. Matches DE/EN. Commercial use included. Money-back via PromptBase.",
     "skill": "commit-message-writer"},
    {"title": "CI/CD Failure Trier — Why Your Build Broke (Claude Skill)",
     "model": "Claude", "type": "Agent Skill", "gen": "Text",
     "cat": "DevOps / CI", "price": "2.99",
     "tags": "ci cd, github actions, gitlab ci, devops, build failed, pipeline, claude skill",
     "desc": "Paste a failed CI log (GitHub Actions, GitLab CI, etc.) and get the real failure isolated from the noise. Finds the FIRST red line, classifies it (build/test/lint/deploy/infra), explains it, and gives the minimal fix plus a prevention line. Flaky runs are named, not masked by bigger timeouts. Secrets in logs are redacted. Commercial use included. Money-back via PromptBase.",
     "skill": "ci-pipeline-trier"},
    {"title": "Root-Cause Debugger — Find The Bug (Claude Skill)",
     "model": "Claude", "type": "Agent Skill", "gen": "Text",
     "cat": "Debugging / Engineering", "price": "2.99",
     "tags": "debugging, root cause, stack trace, bug, claude skill, engineering, error",
     "desc": "Paste an error, stack trace, or 'works locally, not in prod' report and get the actual cause — not a guess. 4 phases: reproduce, localize, hypothesize, verify. Output is uniform: SYMPTOM / ROOT CAUSE / EVIDENCE / NEXT CHECK / FIX. Suspect vs known is labeled. No code edits before the hypothesis is testable. Commercial use included. Money-back via PromptBase.",
     "skill": "root-cause-debugger"},
    {"title": "Daily Standup Writer — Standup From Commits (ChatGPT Skill)",
     "model": "ChatGPT", "type": "Agent Skill", "gen": "Text",
     "cat": "Writing / Productivity", "price": "2.99",
     "tags": "standup, daily standup, status update, productivity, chatgpt skill, meeting, writing",
     "desc": "Turn raw git commits, a diff, or messy bullets into a tight standup in seconds. Output: GESTERN / HEUTE / BLOCKER, each 1-3 bullets, outcome-led not activity-led, under 120 words. Matches your language (DE/EN). Great for Slack, Jira, daily sync. Commercial use included. Money-back guarantee via PromptBase.",
     "skill": "daily-standup-writer"},
    {"title": "Messy CSV Cleaner — Dedupe, Fix, Normalize (ChatGPT Skill)",
     "model": "ChatGPT", "type": "Agent Skill", "gen": "Text",
     "cat": "Data / Productivity", "price": "2.99",
     "tags": "csv cleaner, data cleaning, dedupe, normalize, chatgpt skill, data, excel",
     "desc": "Paste a dirty CSV/table and get it analysis-ready: trim, unify casing, parse dates to ISO, coerce numbers, drop exact duplicates, flag near-dups. Returns issues found, cleaned data, and a tool-agnostic recipe (pandas/Excel/SQL). Uncertain values are flagged, never overwritten. Shows before/after row counts. Commercial use included. Money-back via PromptBase.",
     "skill": "messy-data-cleaner"},
    {"title": "Test Case Generator — Edge Cases & Coverage (Claude Skill)",
     "model": "Claude", "type": "Agent Skill", "gen": "Text",
     "cat": "Testing / QA", "price": "2.99",
     "tags": "test cases, edge cases, unit test, qa, testing, claude skill, coverage",
     "desc": "Paste a function, endpoint, or feature spec and get runnable test cases: happy path, edge cases (null/boundary/unicode), and failure modes (bad input, timeout, 5xx). Every case is prioritized P0/P1/P2 in a given/when/then format, ending with a coverage-gap note. No filler, one assertion per case. Commercial use included. Money-back via PromptBase.",
     "skill": "test-case-generator"},
    {"title": "Senior Code Reviewer — Bugs Before Ship (Claude Skill)",
     "model": "Claude", "type": "Agent Skill", "gen": "Text",
     "cat": "Review / Coding", "price": "2.99",
     "tags": "code review, bug, security, pull request, claude skill, coding, qa",
     "desc": "A drop-in Claude Skill that reviews your code like a strict senior engineer. Paste a diff, PR, or snippet and get a structured 4-pass review: (1) Correctness — logic bugs, off-by-one, null/undefined, wrong types (2) Security — injection, auth bypass, secret leaks, unsafe eval (3) Edge cases — empty/huge input, concurrency, network failure (4) Clarity — naming, dead code, readability. Output is uniform: [PASS 1-4] SEVERITY — file:line — fix, ending in a VERDICT: ship | ship-with-fixes | block. No fluff, smallest fix preferred, never guesses. Commercial use included. Money-back guarantee via PromptBase.",
     "skill": "clean-code-reviewer"},
]


def _set_select(idx, opt_idx):
    """Set SELECT[idx] to its option at opt_idx (robust against text quirks)."""
    return c.eval_tab("sell", """
(function(idx,oi){
  var s=document.querySelectorAll('select')[idx];
  if(!s) return 'NO_SELECT:'+idx;
  if(oi<0 || oi>=s.options.length) return 'BAD_IDX:'+idx+':'+oi+'/'+s.options.length;
  var proto=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;
  proto.call(s, s.options[oi].value);
  s.dispatchEvent(new Event('change',{bubbles:true}));
  return 'SEL['+idx+']='+s.value;
})(%d,%d)
""" % (idx, opt_idx))


def _set_input(idx, value):
    return c.eval_tab("sell", """
(function(idx,val){
  var els=document.querySelectorAll('input[type=text],textarea');
  var e=els[idx];
  if(!e) return 'NO_INPUT_IDX:'+idx;
  var proto=Object.getOwnPropertyDescriptor(
    e.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype,'value').set;
  proto.call(e,val);
  e.dispatchEvent(new Event('input',{bubbles:true}));
  e.dispatchEvent(new Event('change',{bubbles:true}));
  return 'SET['+idx+']='+e.value.slice(0,20);
})(%d,%r)
""" % (idx, repr(value)))


def _model_opt_index(model):
    """After selecting Agent Skill, find the model option index by text."""
    res = c.eval_tab("sell", """
(function(m){
  var s=document.querySelectorAll('select')[1];
  if(!s) return -1;
  for(var j=0;j<s.options.length;j++){
    if(s.options[j].text.toLowerCase().indexOf(m.toLowerCase())>=0) return j;
  }
  return -1;
})(%r)
""" % repr(model))
    try:
        return int(res)
    except (ValueError, TypeError):
        return -1


def fill_step1(listing):
    """Fill Prompt Details (step 1/3). Returns verification snapshot. NO clicks."""
    r = []
    r.append(_set_select(0, 2))            # item type = Agent Skill (opt idx 2)
    time.sleep(2)                          # SPA reveals runtime/model select
    # model/runtime select (index 1 after Agent Skill chosen): hardcode known mapping
    # options: ["Select runtime","ChatGPT Skill","Claude Skill","Cursor Skill","OpenClaw Skill"]
    model_idx = {"ChatGPT": 1, "Claude": 2}.get(listing["model"], -1)
    if model_idx >= 0:
        r.append(_set_select(1, model_idx))
    else:
        r.append("MODEL_OPT_NOT_FOUND:" + listing["model"])
    r.append(_set_input(0, listing["title"]))
    r.append(_set_input(1, listing["desc"]))
    r.append(_set_select(2, 1))            # price = $2.99 (opt idx 1)
    time.sleep(1)
    snap = c.eval_tab("sell", """
(function(){
  var s=[...document.querySelectorAll('select')].map(x=>x.value);
  var ins=[...document.querySelectorAll('input[type=text],textarea')].map(x=>x.value.slice(0,25));
  return JSON.stringify({selects:s, inputs:ins});
})()""")
    return snap, r


if __name__ == "__main__":
    # DRY RUN for listing 1 only — fills, prints snapshot, NO publish
    c.navigate_tab("sell", "https://promptbase.com/sell")
    time.sleep(4)
    snap = fill_step1(LISTINGS[0])
    print("STEP1 DRY-RUN SNAPSHOT (Listing 1):")
    print(snap)
    print("\n>>> NO PUBLISH CLICKED. Awaiting user 'go' for publish.")
