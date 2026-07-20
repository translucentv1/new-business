#!/usr/bin/env python3
"""Build SEO landing pages for the 7 PromptBase Agent-Skills.

Each page targets a long-tail search query (German + English dev audience)
and links to the PromptBase listing. Until the exact listing slug is known
(the 2 pending are still in review), the buy link points at the PromptBase
search for the skill name, which always resolves once the skill is public.

Output: docs/t/<skill-id>/index.html  (deployed to GitHub Pages on push).
"""
import os, json, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO, "products", "promptbase-agent-skills", "skills")
OUT_DIR = os.path.join(REPO, "docs", "t")

# (skill file, url slug for promptbase search, runtime label, price)
SKILLS = [
    ("ci-pipeline-trier.md", "ci-cd-failure-trier", "ChatGPT Skill", "2.99"),
    ("root-cause-debugger.md", "root-cause-debugger", "Claude Skill", "2.99"),
    ("daily-standup-writer.md", "daily-standup-writer", "ChatGPT Skill", "2.99"),
    ("messy-data-cleaner.md", "messy-csv-cleaner", "ChatGPT Skill", "2.99"),
    ("test-case-generator.md", "test-case-generator", "Claude Skill", "2.99"),
    ("clean-code-reviewer.md", "senior-code-reviewer", "Claude Skill", "2.99"),
    ("commit-message-writer.md", "commit-message-writer", "ChatGPT Skill", "2.99"),
]

def read_body(fname):
    path = os.path.join(SKILLS_DIR, fname)
    raw = open(path, encoding="utf-8").read()
    parts = raw.split("---")
    # frontmatter (1) + body (2+); join rest, strip leading newline
    body = "---".join(parts[2:]).lstrip("\n")
    return body

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def build_page(fname, slug, runtime, price):
    body = read_body(fname)
    # build a readable feature list from the SKILL.md body
    lines = [l for l in body.splitlines() if l.strip()]
    # pick heading + first bullets as "what it does"
    bullets = []
    for l in lines:
        m = re.match(r"^[-*]\s+(.*)", l)
        if m and len(bullets) < 6:
            bullets.append(m.group(1).strip())
    if not bullets:
        bullets = [l.strip() for l in lines if l.strip() and not l.startswith("#")][:5]
    feat_html = "\n".join(f"<li>{esc(b)}</li>" for b in bullets)
    title = f"{slug.replace('-', ' ').title()} — {runtime} (PromptBase)"
    desc = (f"{runtime} Agent-Skill: {bullets[0] if bullets else 'copy-ready SKILL.md'} "
            f"Ready to paste into your agent. $2.99 on PromptBase.")
    search_url = f"https://promptbase.com/search?q={slug}"
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
</head>
<body>
<h1>{esc(title)}</h1>
<p class="lead">{esc(runtime)} Agent-Skill — fertige SKILL.md, sofort in deinen Agenten kopierbar.</p>
<h2>Was das Skill macht</h2>
<ul>
{feat_html}
</ul>
<p class="price">Preis: {price} $ · sofort nutzbar nach Kauf auf PromptBase</p>
<a class="buy" href="{search_url}">Auf PromptBase ansehen &amp; kaufen — {price} $</a>
<p class="back"><a href="/new-business/">Alle Produkte</a></p>
</body>
</html>
"""
    return html, title

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    built = []
    for fname, slug, runtime, price in SKILLS:
        html, title = build_page(fname, slug, runtime, price)
        d = os.path.join(OUT_DIR, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        built.append((slug, title))
    for slug, title in built:
        print(f"BUILT docs/t/{slug}/index.html — {title}")
    print(f"TOTAL: {len(built)} pages")

if __name__ == "__main__":
    main()
