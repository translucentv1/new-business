"""Test: Download-Gate (ADR-0013 / Spec 2026-07-18-download-gate).

Asserts observable behaviour against REAL product content (not toy strings),
following the style/strictness of scripts/test_pd_processor.py.

Covers:
  - Preview (public landing page) contains TOC + first chapter BODY, but NOT
    the full book text (no leak of a fixed string from the last chapter).
  - Download deliverable (docs/dl/<hash>/<slug>.html) exists per product, is
    self-contained (no http(s):// asset link, no <script src), contains the
    full text, and is reachable only via its obscure hashed path.
  - The hash path is deterministic from book_id+salt.
  - robots.txt Disallows /dl/; sitemap.xml lists NO /dl/ entry.
  - No public page links to /dl/ (gate not bypassed by internal links).
"""
import os, re, sys, json, glob, subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CORPUS = os.path.join(REPO, "corpus")
SITE = os.path.join(REPO, "docs")
SYS_PATH = HERE
if SYS_PATH not in sys.path:
    sys.path.insert(0, SYS_PATH)


def _product_ids():
    return sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*"))
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "product", "meta.json"))
    )


def _corrupt_ids():
    from deliverable_gen import is_corrupt
    out = []
    for bid in _product_ids():
        p = os.path.join(CORPUS, bid, "product", "content.md")
        if os.path.exists(p) and is_corrupt(open(p, encoding="utf-8").read()):
            out.append(bid)
    return out


def _last_chapter_marker(content):
    """A string from the LAST chapter body, used to detect full-text leak.

    We pick a non-trivial sentence fragment from the final '## ' chapter so
    that the TOC list (which only contains chapter TITLES, e.g. 'Kapitel 24')
    does NOT false-positive. We use an actual body sentence fragment.
    """
    lines = content.splitlines()
    # find last '## ' heading
    last_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if re.match(r"^##\s", lines[i]):
            last_idx = i
            break
    if last_idx is None:
        return ""
    # grab a fragment from the body after that heading (first real paragraph)
    tail = "\n".join(lines[last_idx:])
    # pull a few words from a later non-empty line
    for ln in lines[last_idx + 1:]:
        ln = ln.strip()
        if len(ln) > 30:
            return ln[:40]
    return tail[:40]


class DownloadGateTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure deliverables + previews are built (idempotent; cheap).
        import landingpage_gen
        landingpage_gen.build()

    def test_corrupt_bundles_excluded(self):
        # ADR-0013 quality guard: is_corrupt() must flag PG boilerplate and
        # chapter-less content. We test the predicate deterministically rather
        # than relying on a live corrupt fixture (25913 was repaired in TB-13).
        from deliverable_gen import is_corrupt
        self.assertTrue(
            is_corrupt("This edition still carries a Project Gutenberg credit line."),
            "is_corrupt must flag Project Gutenberg boilerplate",
        )
        self.assertTrue(
            is_corrupt("# Title\n\nA single paragraph with no chapter headings at all."),
            "is_corrupt must flag content without '## ' chapters",
        )
        # Healthy state: NONE of the current real bundles is corrupt. If a PG
        # line or broken structure sneaks back in, this assertion fails -> the
        # regression is caught before anything ships.
        corrupt = _corrupt_ids()
        self.assertEqual(corrupt, [], "unexpected corrupt bundle in current corpus")
        for bid in corrupt:
            # Defensive: a corrupt bundle must never produce a deliverable.
            dp = deliverable_path(bid) if "deliverable_path" in dir() else None
            dl_dir = os.path.join(SITE, "dl")
            if os.path.isdir(dl_dir):
                for root, _, files in os.walk(dl_dir):
                    for f in files:
                        with open(os.path.join(root, f), encoding="utf-8") as fh:
                            self.assertNotIn(
                                open(os.path.join(CORPUS, bid, "product", "content.md"),
                                     encoding="utf-8").read()[:200],
                                fh.read(),
                                f"corrupt bundle {bid} leaked into a deliverable"
                            )

    def test_preview_not_full_text(self):
        corrupt = set(_corrupt_ids())
        for bid in _product_ids():
            if bid in corrupt:
                continue  # placeholder preview, not asserted for leak
            content = open(os.path.join(CORPUS, bid, "product", "content.md"),
                           encoding="utf-8").read()
            marker = _last_chapter_marker(content)
            self.assertTrue(marker, f"{bid}: no last-chapter body fragment found")
            prev = open(os.path.join(SITE, bid, "index.html"), encoding="utf-8").read()
            self.assertNotIn(
                marker, prev,
                f"LEAK: preview for {bid} contains full-text body fragment {marker!r}"
            )

    def test_preview_has_real_content(self):
        # ADR-0018 changed the product to a Lese-Begleiter: filled products show
        # a companion teaser ("Was dich erwartet"), unfilled ones fall back to the
        # ADR-0013 book preview ("Inhaltsverzeichnis"). Both are valid; what must
        # NEVER happen is an empty "wird gerade erstellt" placeholder (1342 had
        # this bug). Assert real content + no placeholder.
        corrupt = set(_corrupt_ids())
        placeholder = "wird gerade erstellt"
        for bid in _product_ids():
            if bid in corrupt:
                continue
            prev = open(os.path.join(SITE, bid, "index.html"), encoding="utf-8").read()
            self.assertNotIn(placeholder, prev, f"{bid}: preview is empty placeholder")
            self.assertTrue(
                ("Inhaltsverzeichnis" in prev) or ("Was dich erwartet" in prev),
                f"{bid}: preview has neither TOC nor companion teaser",
            )

    def test_deliverable_exists_self_contained_full(self):
        corrupt = set(_corrupt_ids())
        from deliverable_gen import deliverable_path
        for bid in _product_ids():
            if bid in corrupt:
                # corrupt bundles must NOT have a deliverable
                dp = deliverable_path(bid)
                self.assertFalse(
                    os.path.exists(dp),
                    f"{bid}: corrupt bundle must not produce a deliverable at {dp}"
                )
                continue
            dp = deliverable_path(bid)
            self.assertTrue(os.path.exists(dp), f"{bid}: deliverable missing at {dp}")
            html = open(dp, encoding="utf-8").read()
            self.assertNotRegex(html, r'https?://', f"{bid}: deliverable has external URL")
            self.assertNotIn('<script src', html, f"{bid}: deliverable has <script src")
            content = open(os.path.join(CORPUS, bid, "product", "content.md"),
                           encoding="utf-8").read()
            marker = _last_chapter_marker(content)
            self.assertIn(marker, html, f"{bid}: deliverable missing full-text {marker!r}")

    def test_deliverable_epub_exists_and_linked(self):
        # ADR-0013 Tier-2: jedes gesunde Produkt bekommt ein EPUB im selben
        # (nicht verlinkten) Gate-Verzeichnis, und das HTML-Deliverable verlinkt
        # es relativ (kein /dl/, kein http://), damit Kaeufer es post-purchase
        # als echtes eBook (Kindle/Apple Books/Tolino) laden koennen.
        corrupt = set(_corrupt_ids())
        from epub_gen import epub_path
        for bid in _product_ids():
            if bid in corrupt:
                continue
            ep = epub_path(bid)
            self.assertTrue(os.path.exists(ep), f"{bid}: EPUB deliverable missing at {ep}")
            raw = open(ep, "rb").read()
            self.assertIn(b"application/epub+zip", raw,
                          f"{bid}: EPUB mimetype entry missing")
            # HTML-Deliverable muss relativ aufs EPUB zeigen, nicht external.
            from deliverable_gen import deliverable_path
            html = open(deliverable_path(bid), encoding="utf-8").read()
            self.assertIn("EPUB-Version herunterladen", html,
                          f"{bid}: deliverable missing EPUB download link")
            self.assertIn(".epub", html, f"{bid}: deliverable missing .epub href")
            self.assertNotRegex(html, r'https?://', f"{bid}: EPUB link must be relative, not external")

    def test_hash_deterministic(self):
        from deliverable_gen import download_hash, _load_salt
        salt = _load_salt()
        for bid in _product_ids():
            a = download_hash(bid, salt)
            b = download_hash(bid, salt)
            self.assertEqual(a, b, f"{bid}: hash not deterministic")
            self.assertEqual(len(a), 16, f"{bid}: hash not 16 hex chars")

    def test_gate_not_in_robots_or_sitemap(self):
        rob = open(os.path.join(SITE, "robots.txt"), encoding="utf-8").read()
        self.assertIn("Disallow: /dl/", rob, "robots.txt missing Disallow /dl/")
        sm = open(os.path.join(SITE, "sitemap.xml"), encoding="utf-8").read()
        self.assertNotIn("/dl/", sm, "sitemap.xml must NOT list /dl/")

    def test_no_public_link_to_dl(self):
        for bid in _product_ids():
            prev = open(os.path.join(SITE, bid, "index.html"), encoding="utf-8").read()
            self.assertNotIn("/dl/", prev, f"{bid}: public page links to /dl/ gate")
        idx = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
        self.assertNotIn("/dl/", idx, "index links to /dl/ gate")


if __name__ == "__main__":
    unittest.main(verbosity=2)
