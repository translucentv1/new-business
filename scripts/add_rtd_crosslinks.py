"""Add a cross-link to rtd.html (Request-to-Delivery landing) on every
tracked index.html page. Idempotent: skips pages already carrying the marker.

Link is absolute to the GitHub Pages base path (/new-business/rtd.html),
matching the convention already used in t/ template pages.
"""
import subprocess
import sys

MARKER = 'id="rtd-crosslink"'
SNIPPET = ('<p id="rtd-crosslink" style="margin-top:2em;padding-top:1em;'
           'border-top:1px solid #eee;font-size:.9rem">'
           'Nicht gefunden, was du suchst? '
           '<a href="/new-business/rtd.html">Individuelles Deliverable anfragen '
           '(Study-Guide, Template, Text) &rarr;</a></p>\n')

# Old blog pages carry a placeholder TMG note ("[DEIN NAME]...") -> replace
# with links to the real Impressum/AGB pages.
OLD_TMG = ('<div class="note">Anbieter i.S.d. § 5 TMG: [DEIN NAME], [STRASSE], '
           '[PLZ ORT], Deutschland.\nUmsatzsteuer-ID folgt. Impressum/AGB vor '
           'öffentlichem Launch vervollständigen.</div>')
LEGAL = ('<div class="note"><a href="/new-business/impressum.html">Impressum</a>'
         ' &middot; <a href="/new-business/agb.html">AGB</a></div>')

def main():
    files = subprocess.check_output(
        ["git", "ls-files", "*.html"], text=True).splitlines()
    targets = [f for f in files
               if f.endswith("index.html") or f.startswith("blog/")]
    added, skipped, nofoot = 0, 0, []
    for f in targets:
        try:
            html = open(f, encoding="utf-8").read()
        except UnicodeDecodeError:
            html = open(f, encoding="utf-8", errors="replace").read()
        changed = False
        if OLD_TMG in html:
            html = html.replace(OLD_TMG, LEGAL)
            changed = True
        if MARKER in html:
            if changed:
                open(f, "w", encoding="utf-8", newline="").write(html)
                added += 1
            else:
                skipped += 1
            continue
        if "</body>" not in html:
            nofoot.append(f)
            continue
        html = html.replace("</body>", SNIPPET + "</body>", 1)
        open(f, "w", encoding="utf-8", newline="").write(html)
        added += 1
    print(f"targets={len(targets)} added={added} already={skipped} no_body_tag={len(nofoot)}")
    for f in nofoot[:10]:
        print("  NO </body>:", f)
    return 0

if __name__ == "__main__":
    sys.exit(main())
