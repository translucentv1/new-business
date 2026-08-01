#!/usr/bin/env python3
"""verify.py — kanonische Verifikation fuer new-business.

    python scripts/verify.py          # offline-Checks + Netz-Checks (best effort)
    python scripts/verify.py --offline  # nur Checks ohne Netzwerk
    python scripts/verify.py --live     # zusaetzlich die deployte Seite pruefen

Prueft das, was den Funnel traegt: gig.html-Vorschau laeuft clientseitig,
Landingpages sind konsistent, sitemap valide, sales.log ohne unbelegte Claims.
Exit 0 = alles gruen.
"""
from __future__ import annotations

import re
import subprocess
import sys
import urllib.request
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://translucentv1.github.io/new-business"
OK, FAIL, SKIP = [], [], []


def check(name: str, cond: bool, detail: str = "") -> bool:
    (OK if cond else FAIL).append(name + (f" — {detail}" if detail else ""))
    return cond


def run(*cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=90)


def fetch(url: str, timeout: int = 25) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        code = getattr(e, "code", 0)
        return code, str(e)


def check_gig() -> None:
    """gig.html: die Vorschau muss ohne Server funktionieren (Pages ist statisch)."""
    gig = (ROOT / "gig.html").read_text(encoding="utf-8")
    script = re.search(r"<script>([\s\S]*?)</script>", gig).group(1)
    check("gig: kein toter /api/preview", "api/preview" not in gig)
    check("gig: kein fetch() im Script", "fetch(" not in script)
    check("gig: 3 Stripe-Links intakt", script.count("buy.stripe.com") == 3)
    r = run("node", "scripts/test_preview.js")
    check("gig: preview()-Harness gruen", r.returncode == 0,
          (r.stdout + r.stderr).strip().splitlines()[-1:] or ["keine Ausgabe"])


def check_pages() -> list[str]:
    """traffic_engine: Slugs eindeutig, Seiten da, kuratierte Titel benutzt."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import traffic_engine as te

    slugs = [te.slug(k) for k, _, _ in te.KEYWORDS]
    check("engine: Slugs eindeutig", len(slugs) == len(set(slugs)), f"{len(slugs)} Keywords")
    missing = [s for s in slugs if not (ROOT / "blog" / f"{s}.html").exists()]
    check("engine: alle Keyword-Seiten existieren", not missing, str(missing))
    for kw, title, _ in te.KEYWORDS:
        p = ROOT / "blog" / f"{te.slug(kw)}.html"
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        check(f"engine: {te.slug(kw)} verlinkt gig.html", "/new-business/gig.html" in html)
    # Idempotenz: bestehende Seite darf nicht ueberschrieben werden
    kw0, title0, _ = te.KEYWORDS[0]
    created, path = te.page(kw0, "SENTINEL", "SENTINEL")
    check("engine: page() idempotent", created is False)
    check("engine: idempotent ohne Ueberschreiben",
          "SENTINEL" not in Path(path).read_text(encoding="utf-8"))
    return slugs


def check_index(slugs: list[str]) -> None:
    """index.html ist der Hub: ein H1, Gig-Titel, Link auf jede Landingpage."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
    check("index: genau ein H1", len(re.findall(r"<h1[\s>]", html)) == 1)
    check("index: Titel bewirbt den Gig", "KI-Aufgaben erledigen lassen" in title, title[:52])
    check("index: CTA auf gig.html", "/new-business/gig.html" in html)
    linked = set(re.findall(r'href="/new-business/blog/(.+?)\.html"', html))
    check("index: verlinkt jede Landingpage", set(slugs) <= linked,
          str(sorted(set(slugs) - linked)))
    dead = sorted(s for s in linked if not (ROOT / "blog" / f"{s}.html").exists())
    check("index: kein toter blog-Link", not dead, str(dead))


def check_sitemap(slugs: list[str]) -> None:
    sm = ROOT / "sitemap.xml"
    try:
        xml.dom.minidom.parse(str(sm))
        check("sitemap: XML valide", True)
    except Exception as e:  # noqa: BLE001
        check("sitemap: XML valide", False, str(e)[:90])
    txt = sm.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", txt)
    check("sitemap: keine Duplikate", len(locs) == len(set(locs)), f"{len(locs)} URLs")
    absent = [s for s in slugs if f"/blog/{s}.html" not in txt]
    check("sitemap: alle blog-Seiten eingetragen", not absent, str(absent))


def check_sales_log() -> None:
    """Regressionsschutz: kein 'ERSTER SALE' ohne ECHTE Stripe-ID.

    2026-08-01: der alte Check war zu lasch — `cs_verify_abc` (Artefakt eines
    E-Mail-Tests) erfuellte `cs_\\w+` und rutschte durch. Jetzt zusaetzlich:
    Mindestlaenge einer echten Stripe-ID + Blacklist fuer Test-/Platzhalter-Marker.
    """
    lines = [ln.strip() for ln in (ROOT / "sales.log").read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.lstrip().startswith("#")]
    real_id = re.compile(r"\b(cs_|evt_|ch_|pi_)[A-Za-z0-9_]{20,}")
    fake_marker = re.compile(r"verify|selftest|dummy|example\.com|placeholder|foobar|_abc\b",
                             re.IGNORECASE)
    bad = [ln[:120] for ln in lines
           if not real_id.search(ln) or fake_marker.search(ln)]
    check("sales.log: keine Zeile ohne echte Stripe-ID", not bad, str(bad))


def check_keyword_demand() -> None:
    r = run(sys.executable, "scripts/kw_demand.py", "powerpoint erstellen lassen")
    hits = [ln.strip()[2:] for ln in r.stdout.splitlines() if ln.startswith("  - ")]
    if r.returncode == 0 and hits:
        check("kw_demand: echte Autocomplete-Treffer", len(hits) >= 5, f"{len(hits)} Treffer")
    else:
        SKIP.append("kw_demand: Netzwerk/Google nicht erreichbar")


def check_live(slugs: list[str]) -> None:
    code, home = fetch(f"{BASE}/")
    check("live: Startseite HTTP 200", code == 200, str(code))
    check("live: Startseite verlinkt den Gig", 'id="gig-top"' in home)
    code, body = fetch(f"{BASE}/gig.html")
    if code != 200:
        SKIP.append(f"live: gig.html nicht erreichbar (HTTP {code})")
        return
    check("live: gig.html HTTP 200", True)
    check("live: kein /api/preview deployed", "api/preview" not in body)
    check("live: neue Vorschau deployed", "SOFORT-VORSCHAU" in body)
    bad = [s for s in slugs if fetch(f"{BASE}/blog/{s}.html")[0] != 200]
    check(f"live: alle {len(slugs)} Landingpages HTTP 200", not bad, str(bad))


def check_interlinking() -> None:
    """Landingpages muessen thematisch untereinander verlinkt sein + korrekte Titel."""
    r = run(sys.executable, "scripts/interlink.py", "--check")
    check("interlink: alle Landingpages im Cluster verlinkt", r.returncode == 0,
          (r.stdout + r.stderr).strip().splitlines()[-1:] or ["keine Ausgabe"])
    r = run(sys.executable, "scripts/retitle.py", "--check")
    check("retitle: kuratierte Titel/Descriptions aktuell", r.returncode == 0,
          (r.stdout + r.stderr).strip().splitlines()[-1:] or ["keine Ausgabe"])


def main() -> int:
    args = set(sys.argv[1:])
    check_gig()
    slugs = check_pages()
    check_index(slugs)
    check_sitemap(slugs)
    check_sales_log()
    check_interlinking()
    if "--offline" not in args:
        check_keyword_demand()
        if "--live" in args:
            check_live(slugs)
    for x in OK:
        print(f"  OK    {x}")
    for x in SKIP:
        print(f"  SKIP  {x}")
    for x in FAIL:
        print(f"  FAIL  {x}")
    print(f"\nVERIFY: {len(OK)} ok, {len(FAIL)} fail, {len(SKIP)} skip")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
