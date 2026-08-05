#!/usr/bin/env python3
"""verify.py — kanonische Verifikation fuer new-business.

    python scripts/verify.py            # Baum-Checks + Netzproben (best effort)
    python scripts/verify.py --offline  # nur Checks ohne Netzwerk
    python scripts/verify.py --live     # zusaetzlich die deployte Seite pruefen
    python scripts/verify.py --selftest # beweist, dass dieser Pruefer Defekte BEMERKT

Prueft das, was den Funnel traegt: gig.html-Vorschau laeuft clientseitig,
Landingpages sind konsistent, sitemap valide, sales.log ohne unbelegte Claims.

Ergebnisworte (Ticket 18):
    VERIFY_OK          rc=0  alles Gepruefte gruen
    VERIFY_DEFEKT      rc=1  mindestens ein Check rot
    VERIFY_UNGEPRUEFT  rc=2  nichts rot, aber etwas war nicht messbar (z.B. Netz)
Ein echter Defekt schlaegt Unmessbarkeit: rc=1 gewinnt gegen rc=2.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.request
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = os.environ.get("VERIFY_BASE", "https://translucentv1.github.io/new-business")
OK: list[str] = []
FAIL: list[str] = []
SKIP: list[str] = []
UNMEASURED: list[str] = []


def _reset() -> None:
    """Ticket 18: die Listen sind modulglobal. Ohne Reset addiert ein zweiter
    main()-Aufruf im selben Prozess auf den ersten drauf (MEASURED: 56 -> 112 ok)."""
    for lst in (OK, FAIL, SKIP, UNMEASURED):
        lst.clear()


def check(name: str, cond: bool, detail: str | list = "") -> bool:
    if isinstance(detail, list):
        detail = "; ".join(str(d) for d in detail)
    (OK if cond else FAIL).append(name + (f" — {detail}" if detail else ""))
    return cond


def unmeasured(name: str, detail: str = "") -> None:
    """Nicht messbar ist weder gruen noch ein Defekt-Claim."""
    UNMEASURED.append(name + (f" — {detail}" if detail else ""))


def run(*cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=90)


def _tail(r: subprocess.CompletedProcess) -> str:
    lines = (r.stdout + r.stderr).strip().splitlines()
    return lines[-1][:120] if lines else "keine Ausgabe"


def fetch(url: str, timeout: int = 25) -> tuple[int, str]:
    """Rueckgabe (status, body). status 0 = Netzfehler, NICHT 'Seite kaputt'."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        code = getattr(e, "code", 0)
        return code, str(e)


def check_gig() -> None:
    """gig.html: die Vorschau muss ohne Server funktionieren (Pages ist statisch)."""
    gig = (ROOT / "gig.html").read_text(encoding="utf-8")
    m = re.search(r"<script>([\s\S]*?)</script>", gig)
    if not m:
        check("gig: Script-Block vorhanden", False, "kein <script> in gig.html")
        return
    check("gig: Script-Block vorhanden", True)
    script = m.group(1)
    check("gig: kein toter /api/preview", "api/preview" not in gig)
    check("gig: kein fetch() im Script", "fetch(" not in script)
    check("gig: 3 Stripe-Links intakt", script.count("buy.stripe.com") == 3,
          f"{script.count('buy.stripe.com')} gefunden")
    r = run("node", "scripts/test_preview.js")
    check("gig: preview()-Harness gruen", r.returncode == 0, _tail(r))


def check_pages() -> list[str]:
    """traffic_engine: Slugs eindeutig, Seiten da, kuratierte Titel benutzt."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import traffic_engine as te

    # Leere Eingabe MUSS rot sein (Ticket 16) und darf nicht abstuerzen:
    # der Alt-Stand lief bei leerer Liste in te.KEYWORDS[0] -> IndexError.
    if not check("engine: Keyword-Liste nicht leer", len(te.KEYWORDS) > 0, "0 Keywords"):
        return []
    slugs = [te.slug(k) for k, _, _ in te.KEYWORDS]
    check("engine: Slugs eindeutig", len(slugs) == len(set(slugs)), f"{len(slugs)} Keywords")

    blog_dir = ROOT / "blog"
    disk = sorted(p.stem for p in blog_dir.glob("*.html"))
    check("engine: blog/ nicht leer", len(disk) > 0, f"{len(disk)} Seiten")

    missing = [s for s in slugs if not (blog_dir / f"{s}.html").exists()]
    check("engine: alle Keyword-Seiten existieren", not missing, str(missing[:5]))

    # Ticket 17/18: Zielmenge aus der Quelle ABLEITEN, beide Richtungen.
    # Ohne das schrumpft die Pruefflaeche still mit der Keyword-Liste mit
    # (MEASURED am Alt-Stand: KEYWORDS 37 -> 1 ergab "20 ok, 0 fail", rc=0).
    uncovered = sorted(set(disk) - set(slugs))
    check("engine: keine ungedeckte Blogseite", not uncovered,
          f"{len(uncovered)} Seiten ohne Keyword: {uncovered[:5]}")

    for kw, _title, _ in te.KEYWORDS:
        p = blog_dir / f"{te.slug(kw)}.html"
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8")
        check(f"engine: {te.slug(kw)} verlinkt gig.html", "/new-business/gig.html" in html)

    # Idempotenz: bestehende Seite darf nicht ueberschrieben werden.
    # Nur pruefen, wenn die Seite existiert — sonst wuerde der PRUEFER eine
    # SENTINEL-Seite in den Baum schreiben.
    kw0 = te.KEYWORDS[0][0]
    p0 = blog_dir / f"{te.slug(kw0)}.html"
    if p0.exists():
        created, path = te.page(kw0, "SENTINEL", "SENTINEL")
        check("engine: page() idempotent", created is False)
        check("engine: idempotent ohne Ueberschreiben",
              "SENTINEL" not in Path(path).read_text(encoding="utf-8"))
    else:
        check("engine: page() idempotent", False,
              "Referenzseite fehlt — nicht geprueft, kein Schreibversuch")
    return slugs


def check_index(slugs: list[str]) -> None:
    """index.html ist der Hub: ein H1, Gig-Titel, Link auf jede Landingpage."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    tm = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    title = tm.group(1) if tm else ""
    check("index: Titel vorhanden", bool(tm))
    check("index: genau ein H1", len(re.findall(r"<h1[\s>]", html)) == 1)
    check("index: Titel bewirbt den Gig", "KI-Aufgaben erledigen lassen" in title, title[:52])
    check("index: CTA auf gig.html", "/new-business/gig.html" in html)
    linked = set(re.findall(r'href="/new-business/blog/(.+?)\.html"', html))
    check("index: verlinkt ueberhaupt Landingpages", len(linked) > 0, f"{len(linked)} Links")
    check("index: verlinkt jede Landingpage", set(slugs) <= linked,
          str(sorted(set(slugs) - linked)[:5]))
    dead = sorted(s for s in linked if not (ROOT / "blog" / f"{s}.html").exists())
    check("index: kein toter blog-Link", not dead, str(dead[:5]))


def check_sitemap(slugs: list[str]) -> None:
    sm = ROOT / "sitemap.xml"
    try:
        xml.dom.minidom.parse(str(sm))
        check("sitemap: XML valide", True)
    except Exception as e:  # noqa: BLE001
        check("sitemap: XML valide", False, str(e)[:90])
    txt = sm.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", txt)
    check("sitemap: nicht leer", len(locs) > 0, f"{len(locs)} URLs")
    check("sitemap: keine Duplikate", len(locs) == len(set(locs)), f"{len(locs)} URLs")
    absent = [s for s in slugs if f"/blog/{s}.html" not in txt]
    check("sitemap: alle blog-Seiten eingetragen", not absent, str(absent[:5]))


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
    check("sales.log: keine Zeile ohne echte Stripe-ID", not bad, str(bad[:3]))


def check_keyword_demand() -> None:
    r = run(sys.executable, "scripts/kw_demand.py", "powerpoint erstellen lassen")
    hits = [ln.strip()[2:] for ln in r.stdout.splitlines() if ln.startswith("  - ")]
    if r.returncode == 0 and hits:
        check("kw_demand: echte Autocomplete-Treffer", len(hits) >= 5, f"{len(hits)} Treffer")
    else:
        SKIP.append("kw_demand: Netzwerk/Google nicht erreichbar (externe Sonde, kein Tor)")


def check_live(slugs: list[str]) -> None:
    """LIVE-Auslieferung. Netzfehler (Status 0) = ungeprueft, NICHT 'Seite kaputt'."""
    code, home = fetch(f"{BASE}/")
    if code == 0:
        unmeasured("live: Startseite nicht erreichbar", f"Netzfehler, {BASE}")
        unmeasured("live: alle Landingpages", "wegen Netzfehler nicht geprueft")
        return
    check("live: Startseite HTTP 200", code == 200, f"HTTP {code}")
    check("live: Startseite verlinkt den Gig", 'id="gig-top"' in home)
    code, body = fetch(f"{BASE}/gig.html")
    if code == 0:
        unmeasured("live: gig.html nicht erreichbar", "Netzfehler")
        return
    if code != 200:
        check("live: gig.html HTTP 200", False, f"HTTP {code}")
        return
    check("live: gig.html HTTP 200", True)
    check("live: kein /api/preview deployed", "api/preview" not in body)
    check("live: neue Vorschau deployed", "SOFORT-VORSCHAU" in body)
    codes = {s: fetch(f"{BASE}/blog/{s}.html")[0] for s in slugs}
    net = sorted(s for s, c in codes.items() if c == 0)
    bad = sorted(s for s, c in codes.items() if c not in (0, 200))
    check(f"live: alle {len(slugs)} Landingpages HTTP 200", not bad, str(bad[:5]))
    if net:
        unmeasured("live: Landingpages mit Netzfehler", f"{len(net)}: {net[:5]}")


def check_interlinking() -> None:
    """Landingpages muessen thematisch untereinander verlinkt sein + korrekte Titel."""
    r = run(sys.executable, "scripts/interlink.py", "--check")
    check("interlink: alle Landingpages im Cluster verlinkt", r.returncode == 0, _tail(r))
    r = run(sys.executable, "scripts/retitle.py", "--check")
    check("retitle: kuratierte Titel/Descriptions aktuell", r.returncode == 0, _tail(r))


def main() -> int:
    _reset()
    args = set(sys.argv[1:])
    if "--offline" in args:
        scope = "lokaler Baum (kein Netz)"
    elif "--live" in args:
        scope = f"lokaler Baum + LIVE-Auslieferung ({BASE})"
    else:
        scope = "lokaler Baum + Netzproben (Auslieferung NICHT geprueft, dafuer --live)"

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
    for x in UNMEASURED:
        print(f"  UNGEPRUEFT  {x}")
    for x in FAIL:
        print(f"  FAIL  {x}")
    print(f"\nGELTUNGSBEREICH: {scope}")
    print(f"VERIFY: {len(OK)} ok, {len(FAIL)} fail, {len(SKIP)} skip, "
          f"{len(UNMEASURED)} ungeprueft")
    if FAIL:
        print("ERGEBNIS: VERIFY_DEFEKT")
        return 1
    if UNMEASURED:
        print("ERGEBNIS: VERIFY_UNGEPRUEFT")
        return 2
    print("ERGEBNIS: VERIFY_OK")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        from _verify_selftest import selftest

        sys.exit(selftest())
    sys.exit(main())
