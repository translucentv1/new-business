#!/usr/bin/env python3
"""Setzt den Anreicherungsblock fuer blog/ghostwriter-buch-kosten.html HAND-
GESCHRIEBEN ein — durch dieselben Schranken wie die Ollama-Ausgabe.

WARUM (MEASURED 2026-08-13):
  qwen2.5:7b hat fuer diese Seite zweimal unbrauchbaren Text geliefert:
  Lauf 1 behauptete "wir finden einen Ghostwriter fuer dich, der dein Buch
  schreibt" + "gepruefter Endtext, bereit zum Veroeffentlichen" (beides sachlich
  falsch, passierte damals alle Schranken -> daraufhin FALSE_SERVICE in
  enrich_blog.py + 6 neue Selftest-Faelle).
  Lauf 2 (mit neuer Schranke, --force) wurde korrekt ABGELEHNT:
  "Widerspruch zum Angebot: 'keine aenderungen'".
  Ein Modell, das zweimal falsch liefert, bekommt keinen dritten Versuch auf
  einer Geldseite. Der Text hier ist von Hand geschrieben, laeuft aber durch
  enrich_blog.validate() + render(), damit KEINE Schranke umgangen wird.

Nutzung:  python evidence/_t_ghostwriter_block.py [--dry]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import enrich_blog as E  # noqa: E402

PAGE = ROOT / "blog" / "ghostwriter-buch-kosten.html"

BLOCK = {
    "intro": (
        "Du vergleichst gerade, was ein Ghostwriter fuer ein Buch verlangt. "
        "Belastbare Zahlen nennt dir nur ein konkretes Angebot, weil Umfang, "
        "Recherche und Honorarmodell den Preis bestimmen. Hier bekommst du "
        "stattdessen die Vorarbeit zum Festpreis: die Struktur deines Buches, "
        "mit der du selbst weiterschreiben oder ein Angebot ueberhaupt erst "
        "sinnvoll einholen kannst."
    ),
    "lieferung": [
        "Ein Expose auf 1 bis 2 Seiten: Thema, Zielgruppe, Nutzenversprechen, "
        "Vergleichstitel",
        "Eine Kapitel-Gliederung mit Arbeitstiteln und je 2 bis 3 Stichpunkten "
        "pro Kapitel",
        "Einen Probekapitel-Entwurf, an dem du Ton, Perspektive und Tempo "
        "pruefen kannst",
        "Alles als Text zum Weiterschreiben, nicht als abgeschlossenes "
        "Manuskript",
    ],
    "brauchen": [
        "Dein Thema und in zwei Saetzen, worum es im Buch gehen soll",
        "Fuer wen du schreibst: Zielgruppe und deren Vorwissen",
        "Sachbuch oder Roman, gewuenschter Umfang, gewuenschte Erzaehlperspektive",
        "Vorhandene Notizen oder Kapitel, falls es schon welche gibt",
    ],
    "faq": [
        {
            "f": "Schreibt ihr mein ganzes Buch?",
            "a": "Nein. Fuer 3,99 bis 14,99 EUR bekommst du Expose, Gliederung "
                 "und einen Probekapitel-Entwurf. Ein vollstaendiges Manuskript "
                 "ist in dieser Preisstufe nicht moeglich, und alles andere "
                 "waere ein leeres Versprechen.",
        },
        {
            "f": "Warum steht hier kein Preis fuer ein komplettes Buch?",
            "a": "Weil wir keinen kennen, den wir belegen koennen. Der Preis "
                 "haengt an Seitenzahl, Recherchetiefe und Absprachen; eine "
                 "Zahl ohne Angebot waere geraten.",
        },
        {
            "f": "Was mache ich mit dem Entwurf weiter?",
            "a": "Du schreibst ihn selbst aus, nutzt ihn als Briefing fuer "
                 "einen Dienstleister oder pruefst damit erst einmal, ob die "
                 "Buchidee traegt. Der Text gehoert dir.",
        },
        {
            "f": "Wie lange dauert es?",
            "a": "Die Lieferung erfolgt innerhalb von 24 Stunden nach "
                 "Auftragseingang. Ab 7,99 EUR ist eine Korrekturschleife "
                 "enthalten, wenn Richtung oder Ton noch nicht passen.",
        },
    ],
    "abgrenzung": (
        "Nicht enthalten sind ein vollstaendiges Manuskript, Lektorat des "
        "ganzen Buches, Buchsatz, Cover, ISBN oder die Vermittlung eines "
        "menschlichen Autors. Du bekommst einen Entwurf als Startpunkt, kein "
        "publikationsfertiges Buch."
    ),
}


def main() -> int:
    ok, why = E.validate(BLOCK)
    print(f"validate: {ok} — {why}")
    if not ok:
        return 1
    block = E.render(BLOCK)
    html = PAGE.read_text(encoding="utf-8")
    if E.START in html:
        new = re.sub(re.escape(E.START) + r".*?" + re.escape(E.END), lambda _: block,
                     html, flags=re.S)
    else:
        anchor = E.anchor_of(html)
        if anchor is None:
            print("FAIL: Ankerpunkt fehlt")
            return 1
        new = html.replace(anchor, block + "\n" + anchor, 1)
    if new == html:
        # Idempotenz: derselbe Block steht schon drin -> kein Defekt.
        print("UNVERAENDERT: Block ist bereits identisch eingesetzt")
        return 0
    if "--dry" in sys.argv:
        print("DRY — nichts geschrieben")
        return 0
    PAGE.write_text(new, encoding="utf-8")
    print(f"GESCHRIEBEN: {PAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
