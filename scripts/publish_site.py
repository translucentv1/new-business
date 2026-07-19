"""Publish site to GitHub Pages (root-level on gh-pages branch).

Pipeline (autonomous, no prompt):
  1) Rebuild landing pages from corpus + stripe_links.json (Stripe buy buttons).
  2) Only publish if >=1 Stripe link exists (never push placeholder-only pages
     over the live site).
  3) Export docs/ to a clean root-level gh-pages worktree and push.

GitHub Pages serves the branch root, so <id>/index.html and index.html go to
the top of the gh-pages tree (not under docs/). Only public landing pages are
published; secrets and raw corpus text are excluded.
"""
import os, sys, shutil, subprocess, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(REPO, "docs")
LINKS = os.path.join(REPO, "stripe_links.json")
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


def rebuild_pages():
    sys.path.insert(0, HERE)
    import landingpage_gen as lg
    return lg.build()


def _have_links():
    if not os.path.exists(LINKS):
        return False
    try:
        return len(json.load(open(LINKS, encoding="utf-8"))) > 0
    except (ValueError, OSError):
        return False


def export_to_ghpages():
    import json
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
    # Checkout gh-pages into a worktree (start from origin/gh-pages if present).
    start = "origin/" + BRANCH
    try:
        run(["git", "worktree", "add", "-B", BRANCH, wt, start])
    except SystemExit:
        run(["git", "worktree", "add", "--force", "--detach", wt])
        run(["git", "-C", wt, "checkout", "--orphan", BRANCH])
        # clean so orphan starts empty
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
        run(["git", "-C", wt, "commit", "-m", "site: publish Stripe landing pages (root-level, fulfillment)"])
        run(["git", "-C", wt, "push", "origin", BRANCH])
        print("PUSHED gh-pages.")
    else:
        print("No changes to publish.")
    run(["git", "worktree", "remove", "--force", wt], check=False)
    shutil.rmtree(tmp, ignore_errors=True)
    # Pull latest gh-pages ref locally so future runs see it.
    run(["git", "fetch", "origin", BRANCH], check=False)


def main():
    n = rebuild_pages()
    print(f"Rebuilt {n} pages.")
    # TB-24: build template landingpages + deliverables so they ship in this publish
    try:
        import template_landing, deliverable_gen
        tpl_root = os.path.join(REPO, "products", "templates")
        for t in sorted(
            os.path.basename(p) for p in glob.glob(os.path.join(tpl_root, "*"))
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "spec.json"))
        ):
            deliverable_gen.build_template_deliverable(t)
        tl = template_landing.build_all()
        print(f"Built {len(tl)} template pages.")
    except Exception as e:
        print(f"template build skipped: {e}")
    if not _have_links():
        print("NO_LINKS: stripe_links.json empty/fehlt -> Site NICHT gepusht "
              "(waere Platzhalter). Erst Stripe-Links erstellen, dann erneut "
              "ausfuehren.")
        return
    export_to_ghpages()
    print("Live-Check: https://translucentv1.github.io/new-business/")


if __name__ == "__main__":
    main()
