#!/usr/bin/env python3
"""Selftest fuer scripts/verify.py (Ticket 18).

Beweist, dass verify.py Defekte BEMERKT — nicht nur, dass es gruen sagt.

Vorgehen (Konvention aus auto_fulfill/funnel_check/verify_rtd_chain/
verify_ticket13_live): Fault Injection durch den ECHTEN Einstiegspunkt.
Hier heisst das: eine Sandbox-Kopie des Baums, in der die UNVERAENDERTE
verify.py als Subprozess laeuft. Kein Reimplementat, keine gemockte main() —
mutiert wird immer nur die EINGABE, nie der Pruefer.

Rot-Faelle assertieren die EXAKTE Diagnosezeile (nicht nur ein Stichwort)
und werden zusaetzlich gegen 'Traceback' gefiltert: ein Absturz liefert auch
rc!=0, ist aber keine Diagnose (Exit-Code-Falle).
"""
from __future__ import annotations

import http.server
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COPY_DIRS = ("scripts", "blog")
COPY_FILES = ("gig.html", "index.html", "sitemap.xml", "sales.log")
DEAD_BASE = "https://127.0.0.1:9/new-business"

results: list[tuple[bool, str]] = []


def t(cond: bool, label: str, detail: str = "") -> bool:
    results.append((bool(cond), label + (f" — {detail}" if detail else "")))
    return bool(cond)


def build_sandbox() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="verify_selftest_"))
    for d in COPY_DIRS:
        shutil.copytree(ROOT / d, tmp / d, ignore=shutil.ignore_patterns("__pycache__"))
    for f in COPY_FILES:
        shutil.copy2(ROOT / f, tmp / f)
    return tmp


def run_sandbox(tmp: Path, *args: str, base: str | None = None) -> tuple[int, str]:
    env = dict(os.environ)
    if base:
        env["VERIFY_BASE"] = base
    r = subprocess.run([sys.executable, str(tmp / "scripts" / "verify.py"), *args],
                       capture_output=True, text=True, timeout=300, env=env)
    return r.returncode, r.stdout + r.stderr


# ---------------------------------------------------------------- Mutationen
def m_api_preview(tmp: Path) -> None:
    p = tmp / "gig.html"
    p.write_text(p.read_text(encoding="utf-8").replace("</body>", "<!-- api/preview --></body>"),
                 encoding="utf-8")


def m_fetch_im_script(tmp: Path) -> None:
    p = tmp / "gig.html"
    s = p.read_text(encoding="utf-8")
    p.write_text(s.replace("<script>", "<script>\n/* */ fetch(", 1), encoding="utf-8")


def m_stripe_link_weg(tmp: Path) -> None:
    p = tmp / "gig.html"
    p.write_text(p.read_text(encoding="utf-8").replace("buy.stripe.com", "buy.example.com", 1),
                 encoding="utf-8")


def m_vorschau_regress(tmp: Path) -> None:
    """Echter Regress im Produkt, nicht im Harness: die Vorschau verliert ihre
    Ueberschrift. test_preview.js assertiert auf 'SOFORT-VORSCHAU' (Zeile 57).
    (Ein `process.exit(3)` ANS ENDE von test_preview.js waere wirkungslos —
    Zeile 72 beendet den Prozess vorher. MEASURED: rc blieb 0.)"""
    p = tmp / "gig.html"
    s = p.read_text(encoding="utf-8")
    neu = s.replace("SOFORT-VORSCHAU", "VORSCHAU-KAPUTT")
    if neu == s:
        raise RuntimeError("'SOFORT-VORSCHAU' nicht in gig.html gefunden")
    p.write_text(neu, encoding="utf-8")


def m_blogseite_weg(tmp: Path) -> None:
    (tmp / "blog" / f"{_first_slug()}.html").unlink()


def m_gig_link_weg(tmp: Path) -> None:
    p = tmp / "blog" / f"{_first_slug()}.html"
    p.write_text(p.read_text(encoding="utf-8").replace("/new-business/gig.html", "/nirgendwo"),
                 encoding="utf-8")


def _keywords_ersetzen(tmp: Path, body: str) -> None:
    p = tmp / "scripts" / "traffic_engine.py"
    src = p.read_text(encoding="utf-8")
    m = re.search(r"^KEYWORDS = \[.*?^\]", src, re.DOTALL | re.MULTILINE)
    if not m:
        raise RuntimeError("KEYWORDS-Block in traffic_engine.py nicht gefunden")
    p.write_text(src[:m.start()] + body + src[m.end():], encoding="utf-8")


def m_keywords_geschrumpft(tmp: Path) -> None:
    """Der heute real gefundene Defekt: Pruefflaeche schrumpft still mit."""
    p = tmp / "scripts" / "traffic_engine.py"
    m = re.search(r"^KEYWORDS = \[(.*?)^\]", p.read_text(encoding="utf-8"), re.DOTALL | re.MULTILINE)
    first = m.group(1).strip().splitlines()[0]
    _keywords_ersetzen(tmp, "KEYWORDS = [\n" + first + "\n]")


def m_keywords_leer(tmp: Path) -> None:
    _keywords_ersetzen(tmp, "KEYWORDS = []")


def m_zweites_h1(tmp: Path) -> None:
    p = tmp / "index.html"
    p.write_text(p.read_text(encoding="utf-8").replace("</body>", "<h1>zweit</h1></body>"),
                 encoding="utf-8")


def m_titel_kaputt(tmp: Path) -> None:
    p = tmp / "index.html"
    s = p.read_text(encoding="utf-8")
    p.write_text(re.sub(r"<title>.*?</title>", "<title>Irgendwas</title>", s, flags=re.DOTALL),
                 encoding="utf-8")


def m_alle_bloglinks_weg(tmp: Path) -> None:
    p = tmp / "index.html"
    s = p.read_text(encoding="utf-8")
    p.write_text(s.replace('href="/new-business/blog/', 'href="/woanders/'), encoding="utf-8")


def m_toter_bloglink(tmp: Path) -> None:
    p = tmp / "index.html"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "</body>", '<a href="/new-business/blog/gibtesnicht.html">x</a></body>'),
        encoding="utf-8")


def m_sitemap_kaputt(tmp: Path) -> None:
    p = tmp / "sitemap.xml"
    p.write_text(p.read_text(encoding="utf-8").replace("</urlset>", "<urlset>"), encoding="utf-8")


def m_sitemap_duplikat(tmp: Path) -> None:
    p = tmp / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    first = re.search(r"<url>.*?</url>", s, re.DOTALL).group(0)
    p.write_text(s.replace("</urlset>", first + "</urlset>"), encoding="utf-8")


def m_sitemap_blogseite_weg(tmp: Path) -> None:
    p = tmp / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    slug = _first_slug()
    p.write_text(re.sub(r"<url>(?:(?!</url>).)*?/blog/" + re.escape(slug) + r"\.html.*?</url>",
                        "", s, flags=re.DOTALL), encoding="utf-8")


def m_fake_sale(tmp: Path) -> None:
    p = tmp / "sales.log"
    with p.open("a", encoding="utf-8") as fh:
        fh.write("\n2026-08-05 ERSTER SALE 3.99 EUR cs_verify_abc\n")


def m_kw_demand_stumm(tmp: Path) -> None:
    """Externe Google-Sonde neutralisieren, damit die LIVE-Faelle isoliert sind."""
    (tmp / "scripts" / "kw_demand.py").write_text(
        "import sys\nsys.exit(9)\n", encoding="utf-8")


def m_interlink_rot(tmp: Path) -> None:
    """verify.py delegiert diesen Check an ein Unterskript — meldet es das Rot weiter?"""
    (tmp / "scripts" / "interlink.py").write_text(
        "import sys\nprint('interlink: 3 Seiten ohne Cluster')\nsys.exit(1)\n", encoding="utf-8")


def m_retitle_rot(tmp: Path) -> None:
    (tmp / "scripts" / "retitle.py").write_text(
        "import sys\nprint('retitle: 2 veraltet')\nsys.exit(1)\n", encoding="utf-8")


class _Always404(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_error(404, "nicht da")

    do_HEAD = do_GET

    def log_message(self, *args: object) -> None:
        pass


def start_404_server() -> tuple[socketserver.TCPServer, str]:
    """Deterministischer Live-Defekt ohne Internet: alles antwortet 404."""
    srv = socketserver.TCPServer(("127.0.0.1", 0), _Always404)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


_SLUG_CACHE: list[str] = []


def _first_slug() -> str:
    if not _SLUG_CACHE:
        sys.path.insert(0, str(ROOT / "scripts"))
        import traffic_engine as te
        _SLUG_CACHE.append(te.slug(te.KEYWORDS[0][0]))
    return _SLUG_CACHE[0]


# ------------------------------------------------------------------ Faelle
# (Label, Mutation, Argumente, erwarteter rc, erwartete Diagnosezeile)
ROT_FAELLE = [
    ("api/preview wieder eingebaut", m_api_preview, ("--offline",), 1,
     "FAIL  gig: kein toter /api/preview"),
    ("fetch() im gig-Script", m_fetch_im_script, ("--offline",), 1,
     "FAIL  gig: kein fetch() im Script"),
    ("ein Stripe-Link verschwunden", m_stripe_link_weg, ("--offline",), 1,
     "FAIL  gig: 3 Stripe-Links intakt"),
    ("Vorschau-Regress (Harness wird rot)", m_vorschau_regress, ("--offline",), 1,
     "FAIL  gig: preview()-Harness gruen"),
    ("Blogseite geloescht", m_blogseite_weg, ("--offline",), 1,
     "FAIL  engine: alle Keyword-Seiten existieren"),
    ("Blogseite ohne gig-Link", m_gig_link_weg, ("--offline",), 1,
     f"FAIL  engine: {'{slug}'} verlinkt gig.html"),
    ("KEYWORDS 37 -> 1 (stille Schrumpfung)", m_keywords_geschrumpft, ("--offline",), 1,
     "FAIL  engine: keine ungedeckte Blogseite"),
    ("KEYWORDS leer (Leere-Schleife-Falle)", m_keywords_leer, ("--offline",), 1,
     "FAIL  engine: Keyword-Liste nicht leer"),
    ("zweites H1 auf index", m_zweites_h1, ("--offline",), 1,
     "FAIL  index: genau ein H1"),
    ("index-Titel bewirbt den Gig nicht", m_titel_kaputt, ("--offline",), 1,
     "FAIL  index: Titel bewirbt den Gig"),
    ("index verlinkt keine Landingpage", m_alle_bloglinks_weg, ("--offline",), 1,
     "FAIL  index: verlinkt ueberhaupt Landingpages"),
    ("toter blog-Link auf index", m_toter_bloglink, ("--offline",), 1,
     "FAIL  index: kein toter blog-Link"),
    ("sitemap XML kaputt", m_sitemap_kaputt, ("--offline",), 1,
     "FAIL  sitemap: XML valide"),
    ("sitemap mit Duplikat", m_sitemap_duplikat, ("--offline",), 1,
     "FAIL  sitemap: keine Duplikate"),
    ("Blogseite fehlt in sitemap", m_sitemap_blogseite_weg, ("--offline",), 1,
     "FAIL  sitemap: alle blog-Seiten eingetragen"),
    ("Fake-Sale in sales.log", m_fake_sale, ("--offline",), 1,
     "FAIL  sales.log: keine Zeile ohne echte Stripe-ID"),
    ("interlink-Unterskript rot", m_interlink_rot, ("--offline",), 1,
     "FAIL  interlink: alle Landingpages im Cluster verlinkt"),
    ("retitle-Unterskript rot", m_retitle_rot, ("--offline",), 1,
     "FAIL  retitle: kuratierte Titel/Descriptions aktuell"),
]


def selftest() -> int:
    print("== verify.py --selftest (Fault Injection durch den echten Einstiegspunkt) ==")
    tmp = build_sandbox()
    try:
        pristine = {p: p.read_bytes() for p in tmp.rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts}

        def restore() -> None:
            for p in list(tmp.rglob("*")):
                if p.is_file() and p not in pristine:
                    p.unlink()
            for p, data in pristine.items():
                p.parent.mkdir(parents=True, exist_ok=True)
                if not p.exists() or p.read_bytes() != data:
                    p.write_bytes(data)

        # --- Gruen-Basis ---------------------------------------------------
        rc, out = run_sandbox(tmp, "--offline")
        t(rc == 0, "Gruen-Basis: rc=0", f"rc={rc}")
        t("ERGEBNIS: VERIFY_OK" in out, "Gruen-Basis: VERIFY_OK")
        t("0 fail" in out, "Gruen-Basis: 0 fail")
        t("Traceback" not in out, "Gruen-Basis: kein Traceback")
        t("GELTUNGSBEREICH: lokaler Baum (kein Netz)" in out,
          "Gruen-Basis: Geltungsbereich benannt (Baum != Auslieferung)")
        basis_ok = re.search(r"VERIFY: (\d+) ok", out)
        n_basis = int(basis_ok.group(1)) if basis_ok else -1
        t(n_basis >= 50, "Gruen-Basis: Pruefflaeche vollstaendig", f"{n_basis} Checks")

        # --- Rot-Faelle ----------------------------------------------------
        for label, mutate, args, want_rc, want_line in ROT_FAELLE:
            restore()
            try:
                mutate(tmp)
            except Exception as e:  # noqa: BLE001
                t(False, f"ROT [{label}]: Mutation fehlgeschlagen", str(e)[:80])
                continue
            rc, out = run_sandbox(tmp, *args)
            line = want_line.replace("{slug}", _first_slug())
            hit = any(ln.strip().startswith(line) for ln in out.splitlines())
            t(rc == want_rc and hit and "Traceback" not in out,
              f"ROT [{label}]",
              f"rc={rc} (soll {want_rc}), Diagnose={'ja' if hit else 'NEIN'}, "
              f"Traceback={'JA' if 'Traceback' in out else 'nein'}")

        # --- Echter Live-Defekt (404) muss ROT sein, nicht UNGEPRUEFT ---------
        restore()
        m_kw_demand_stumm(tmp)
        srv, base404 = start_404_server()
        try:
            rc, out = run_sandbox(tmp, "--live", base=base404)
        finally:
            srv.shutdown()
            srv.server_close()
        hit = any(ln.strip().startswith("FAIL  live: Startseite HTTP 200 — HTTP 404")
                  for ln in out.splitlines())
        t(rc == 1 and hit and "ERGEBNIS: VERIFY_DEFEKT" in out and "Traceback" not in out,
          "ROT [live liefert 404]", f"rc={rc} (soll 1), Diagnose={'ja' if hit else 'NEIN'}")

        # --- Drittes Ergebniswort: nicht messbar ---------------------------
        restore()
        m_kw_demand_stumm(tmp)
        rc, out = run_sandbox(tmp, "--live", base=DEAD_BASE)
        no_false_claim = not any(ln.strip().startswith("FAIL  live:") for ln in out.splitlines())
        t(rc == 2 and "ERGEBNIS: VERIFY_UNGEPRUEFT" in out and no_false_claim
          and "Traceback" not in out,
          "UNGEPRUEFT [Netz tot bei --live]",
          f"rc={rc} (soll 2), kein Defekt-Claim={'ja' if no_false_claim else 'NEIN'}")

        # --- Defekt schlaegt Unmessbarkeit ---------------------------------
        restore()
        m_kw_demand_stumm(tmp)
        m_fake_sale(tmp)
        rc, out = run_sandbox(tmp, "--live", base=DEAD_BASE)
        t(rc == 1 and "ERGEBNIS: VERIFY_DEFEKT" in out and "UNGEPRUEFT  live" in out,
          "VORRANG [echter Defekt schlaegt Netzfehler]", f"rc={rc} (soll 1)")

        # --- Akkumulierende Globals (heute gefundener Defekt) --------------
        restore()
        code = ("import sys;sys.argv=['v','--offline'];sys.path.insert(0,r'%s');"
                "import verify;a=verify.main();n1=len(verify.OK);"
                "b=verify.main();n2=len(verify.OK);"
                "print('N1',n1,'N2',n2,'RC',a,b)" % str(tmp / "scripts"))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           timeout=300, cwd=str(tmp))
        mm = re.search(r"N1 (\d+) N2 (\d+) RC (\d) (\d)", r.stdout)
        if mm:
            n1, n2 = int(mm.group(1)), int(mm.group(2))
            t(n1 == n2, "Zweiter main()-Lauf addiert nicht auf", f"{n1} -> {n2}")
        else:
            t(False, "Zweiter main()-Lauf addiert nicht auf", (r.stdout + r.stderr)[-90:])

        # --- Der Pruefer darf den Baum nicht veraendern --------------------
        restore()
        vorher = {p: p.read_bytes() for p in tmp.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts}
        run_sandbox(tmp, "--offline")
        nachher = {p: p.read_bytes() for p in tmp.rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts}
        geaendert = [str(p.relative_to(tmp)) for p in set(vorher) | set(nachher)
                     if vorher.get(p) != nachher.get(p)]
        t(not geaendert, "Pruefer schreibt nicht in den Baum", str(geaendert[:3]))

        # --- Schreibt der Pruefer, wenn die Referenzseite fehlt? -----------
        restore()
        m_blogseite_weg(tmp)
        vor = {p.name for p in (tmp / "blog").glob("*.html")}
        run_sandbox(tmp, "--offline")
        nach = {p.name for p in (tmp / "blog").glob("*.html")}
        t(vor == nach, "Kein SENTINEL-Schreibversuch bei fehlender Seite",
          str(sorted(nach - vor)[:3]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [lbl for ok, lbl in results if not ok]
    for ok, lbl in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {lbl}")
    print(f"\nSELFTEST: {len(results) - len(fails)}/{len(results)} bestanden")
    if fails:
        print("ERGEBNIS: SELFTEST_DEFEKT")
        return 1
    print("ERGEBNIS: SELFTEST_OK")
    return 0


if __name__ == "__main__":
    sys.exit(selftest())
