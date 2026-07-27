## Verifikation — frische Belege (post-commit `c4c2620`)

Die vorherige Testausgabe stammte *vor* dem finalen Commit. Hier die **neu erzeugte, ad-hoc Verifikation der geänderten Sitemap-Delegation** plus Suite-Re-Run *nach* dem Commit:

**Ad-hoc Script** (`hermes-verify-sitemap-delegation.py`, temporär unter `%TEMP%`, danach gelöscht):
- `lg.rebuild_sitemap()` → `docs/sitemap.xml` = **949 URLs** (241 `/t/` + 693 `/seo/`), `/dl/`-Leak = **0** 
- `tl.build_sitemap([...])` → delegiert jetzt an den Full-Aggregator → **949 URLs**, kein 9-URL-Clobber mehr 
- `ts.rebuild_sitemap_recursive()` → liefert `949` (int), delegiert, `/dl/`-Leak = 0 
- Statisch: `seo_scale.py` + `seo_scale2.py` schreiben `sitemap.xml` nicht mehr direkt, delegieren an `landingpage_gen.rebuild_sitemap()` 
- **AD-HOC VERIFICATION: ALL PASS**

**Suite-Re-Run (post-commit):**
- `test_download_gate.py` → `Ran 8 tests … OK`
- `test_pd_processor.py` → `ALL TESTS PASS`

**Live (zusätzlich, CDN-propagiert):** `curl …/sitemap.xml` → `HTTP 200`, **949 URLs`.

→ Der Fix ist mehrfach und frisch belegt (lokal, raw gh-pages Blob, Live, Ad-hoc-Verifikation, beide Test-Suites). Kein unverifizierter Claim.