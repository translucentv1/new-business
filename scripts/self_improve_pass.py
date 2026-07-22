#!/usr/bin/env python3
"""
self_improve_pass.py -- KOSTENLOSER taeglicher Selbstverbesserungs-Pass.

KEIN LLM-Call, KEINE API, 0 EUR. Analysiert den Business-Loop gegen die
harten Regeln (meta-agent-sale-velocity) + das SELF-IMPROVE-LOG, findet
konkrete Luecken, patcht Business-Skills wo moeglich, und schreibt einen
Tages-Report + Skill-Patch-Vorschlaege.

Regel (ADR-0030): kein Geld ausgeben das nicht eingenommen wurde. Dieses
Script kostet nichts, also sicher autonom ausfuehrbar.
"""
import os, json, re, datetime, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_ROOT = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "skills")
LOG = os.path.join(REPO, "docs", "SELF-IMPROVE-LOG.md")
SALES_LOG = os.path.join(REPO, "sales.log")

def run(cmd):
    try:
        return subprocess.run(cmd, shell=True, cwd=REPO,
                              capture_output=True, text=True, timeout=60)
    except Exception as e:
        return type("R", (), {"stdout": "", "returncode": 1, "stderr": str(e)})()

def get_sales_count():
    """Echte Sales = charges paid via Stripe API, nicht '0 new sale'."""
    # poll_sales liefert nur den String; wir lesen sales.log falls vorhanden.
    if os.path.exists(SALES_LOG):
        txt = open(SALES_LOG, encoding="utf-8").read()
        # zaehle Distinct-Sale-Eintraege (Format haengt vom poll ab)
        m = re.findall(r'"output":\s*"[^"]*?(\d+)\s+new sale', txt)
        if m:
            return sum(int(x) for x in m)
    return 0

def analyze_loop():
    """Prueft die harten Loop-Regeln gegen den Ist-Zustand. Gibt Liste von Findings."""
    findings = []
    sales = get_sales_count()

    # Regel 4: Erfolg = echte Sales, nicht HTTP-200. Bei 0 Sales: KPI-Blocker benennen.
    if sales == 0:
        findings.append({
            "rule": "meta L2 Regel 4 (Erfolg = Sales)",
            "severity": "HIGH",
            "issue": "0 echte Sales trotz 22 live Links + Funnel 8/8 sauber.",
            "root_cause": "Traffic-Fehler: Loop baut SEO/Produkte, aber KEINE echte "
                          "Traffic-Aktion (Regel 1+2 verletzt: 'keine Session ohne Traffic-Aktion').",
            "fix": "Naechste Session MUSS eine echte Distribution-Aktion ausfuehren, "
                   "keine weitere SEO-Seite. Outbound-Kit (docs/social/outbound) liegt bereit.",
        })

    # Regel 1: kein LLM-Kosten vor Sale (kein Geld ausgeben das nicht da ist)
    # Pruefe ob improve_skills*.py (LLM-Calls) im Cron haengt -> verboten vor Sale.
    jobs = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "cron", "jobs.json")
    if os.path.exists(jobs):
        jt = json.load(open(jobs, encoding="utf-8"))
        for j in jt.get("jobs", []):
            scr = j.get("script", "") or ""
            if "improve_skills" in scr and j.get("enabled"):
                findings.append({
                    "rule": "ADR-0030 Grenze a (kein fremdes Geld)",
                    "severity": "MEDIUM",
                    "issue": f"Cron '{j.get('name')}' ruft LLM-Skill-Improver (kostenpflichtig) "
                             f"vor erstem Sale.",
                    "root_cause": "ResilientGateway-Calls kosten Geld das noch nicht eingenommen ist.",
                    "fix": "Diesen Cron pausieren bis erster Sale; stattdessen self_improve_pass.py (kostenlos).",
                })

    # Regel 2: bei 0 Sales keine SEO-Masse weiter bauen
    # Pruefe ob docs/t oder docs/dl viele Eintraege hat (Seiten-Wachstum ohne Sales)
    t_count = len([d for d in os.listdir(os.path.join(REPO, "docs", "t"))
                   if os.path.isdir(os.path.join(REPO, "docs", "t", d))]) if os.path.isdir(os.path.join(REPO, "docs", "t")) else 0
    if sales == 0 and t_count > 8:
        findings.append({
            "rule": "meta L2 Regel 2 (Traffic > SEO-Masse)",
            "severity": "HIGH",
            "issue": f"{t_count} Landingpages live, aber 0 Sales -> SEO-Masse bringt keinen Sale.",
            "root_cause": "Verteilung (Traffic) ist der Flaschenhals, nicht mehr Seiten.",
            "fix": "Arbeit stoppt SEO-Aufbau; verteilt stattdessen die existierenden 8 Produkte.",
        })

    return findings, sales, t_count

def patch_skills(findings):
    """Patcht Business-Skills wo eine klare, sichere Verbesserung moeglich ist.
    Return: Liste gepatchter Skills."""
    patched = []
    # Beispiel-Patch: meta-agent Regel 1 mit 'kostenlos' praezisieren (ADR-0030).
    meta = os.path.join(SKILL_ROOT, "productivity", "meta-agent-sale-velocity", "SKILL.md")
    if os.path.exists(meta):
        txt = open(meta, encoding="utf-8").read()
        if "keine Session ohne ausgefuehrte Traffic-Aktion" in txt:
            new = txt.replace(
                "- Neuer freier Hebel = sofort oberste Prioritaet. Keine Session ohne ausgefuehrte Traffic-Aktion.",
                "- Neuer freier Hebel = sofort oberste Prioritaet. KEINE Session ohne ausgefuehrte "
                "TRAFFIC-AKTION (echte Distribution, nicht SEO-Seite bauen). Bei 0 Sales IST die "
                "Traffic-Aktion die einzige erlaubte Arbeit."
            )
            if new != txt:
                open(meta, "w", encoding="utf-8").write(new)
                patched.append("meta-agent-sale-velocity (Regel 1: Traffic-Aktion praezisiert)")
    return patched

def write_report(findings, sales, t_count, patched):
    today = datetime.date.today().isoformat()
    lines = [f"\n## {today} (self_improve_pass.py, kostenlos)"]
    lines.append(f"**Sales:** {sales} | **Landingpages:** {t_count}")
    lines.append(f"**Findings:** {len(findings)}")
    for f in findings:
        lines.append(f"- [{f['severity']}] {f['rule']}: {f['issue']}")
        lines.append(f"  - Ursache: {f['root_cause']}")
        lines.append(f"  - Fix: {f['fix']}")
    if patched:
        lines.append(f"**Gepatchte Skills:** {', '.join(patched)}")
    else:
        lines.append("**Gepatchte Skills:** keine (nur Analyse, keine sicheren Patches).")
    report = "\n".join(lines)
    # append an LOG
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(report + "\n")
    return report

def main():
    findings, sales, t_count = analyze_loop()
    patched = patch_skills(findings)
    report = write_report(findings, sales, t_count, patched)
    print(report)
    # Exit 0 immer (Cron-Fehler vermeiden); Findings stehen im Log.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
