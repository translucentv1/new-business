#!/usr/bin/env python3
"""Deploy docs/ to gh-pages (root-level) without the Stripe-link gate.

The Agent-Skill landing pages link to PromptBase (not Stripe), so the
stripe_links.json gate in publish_site.py does not apply here. This mirrors
publish_site.export_to_ghpages() but publishes unconditionally.
"""
import os, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(REPO, "docs")
BRANCH = "gh-pages"

def run(cmd, cwd=REPO, check=True):
    print("+ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        if check:
            raise SystemExit(f"CMD FAILED: {' '.join(cmd)}")
    return r

def main():
    tmp = os.path.join(REPO, ".site_export")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)
    for name in os.listdir(SITE):
        src = os.path.join(SITE, name)
        dst = os.path.join(tmp, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    open(os.path.join(tmp, ".nojekyll"), "w").close()

    wt = os.path.join(REPO, ".site_wt")
    if os.path.exists(wt):
        run(["git", "worktree", "remove", "--force", wt], check=False)
    start = "origin/" + BRANCH
    try:
        run(["git", "worktree", "add", "-B", BRANCH, wt, start])
    except SystemExit:
        run(["git", "worktree", "add", "--force", "--detach", wt])
        run(["git", "-C", wt, "checkout", "--orphan", BRANCH])
        run(["git", "-C", wt, "rm", "-rf", "."], check=False)

    for f in os.listdir(wt):
        if f in (".git",):
            continue
        p = os.path.join(wt, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    for name in os.listdir(tmp):
        src = os.path.join(tmp, name)
        dst = os.path.join(wt, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    run(["git", "-C", wt, "add", "-A"])
    st = run(["git", "-C", wt, "status", "--porcelain"], check=False)
    if st.stdout.strip():
        run(["git", "-C", wt, "commit", "-m", "site: publish Agent-Skill landing pages (SEO)"])
        run(["git", "-C", wt, "push", "origin", BRANCH])
        print("PUSHED gh-pages.")
    else:
        print("No changes to publish.")
    run(["git", "worktree", "remove", "--force", wt], check=False)
    shutil.rmtree(tmp, ignore_errors=True)
    run(["git", "fetch", "origin", BRANCH], check=False)
    print("Live: https://translucentv1.github.io/new-business/")

if __name__ == "__main__":
    main()
