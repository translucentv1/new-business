#!/usr/bin/env python3
"""Selftest der Qualitaetsschranke in scripts/enrich_blog.py.

Zweck: beweisen, dass der Pruefer BEIDE Richtungen kann — gutes JSON durchlaesst
UND jede einzelne Verbotsregel rot wird. Ein Pruefer, der nie rot wird, ist kein
Pruefer. Laeuft ohne Ollama, rein lokal.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import enrich_blog as E  # noqa: E402


def good():
    return {
        "intro": ("Diese Seite richtet sich an alle, die eine Mahnung "
                  "formulieren muessen und dafuer eine saubere Vorlage suchen. "
                  "Du lieferst die Eckdaten deiner offenen Rechnung, du bekommst "
                  "den fertigen Text zurueck, den du nur noch absenden musst. "
                  "Der Ton laesst sich von freundlicher Erinnerung bis zu einer "
                  "deutlich bestimmteren Formulierung waehlen."),
        "lieferung": ["Fertiger Mahntext als Word-Datei und als reiner Text",
                      "Zweite Fassung in bestimmterem Ton zum Nachfassen",
                      "Betreffzeile und Anrede passend zum Empfaenger",
                      "Hinweis auf Zahlungsziel und Rechnungsnummer eingearbeitet"],
        "brauchen": ["Rechnungsnummer, Rechnungsdatum und offener Betrag",
                     "Name und Anschrift des Empfaengers",
                     "Gewuenschter Ton und bisheriger Schriftwechsel",
                     "Das Zahlungsziel, das du setzen moechtest"],
        "faq": [
            {"f": "Wie lange dauert es?",
             "a": "Die Lieferung erfolgt innerhalb von 24 Stunden nach Zahlungseingang, "
                  "meist deutlich frueher am selben Werktag."},
            {"f": "Ist das eine Rechtsberatung?",
             "a": "Nein, der Text ersetzt keine Rechtsberatung durch einen Anwalt "
                  "und trifft keine Aussage zur Rechtslage in deinem Fall."},
            {"f": "Kann ich Aenderungen bekommen?",
             "a": "Ab der Stufe 7,99 EUR ist eine Korrekturschleife enthalten, "
                  "in der du Formulierungen anpassen lassen kannst."},
        ],
        "abgrenzung": ("Nicht enthalten sind das Versenden der Mahnung und "
                       "jede Form der Vertretung gegenueber dem Schuldner. "
                       "Ebenfalls nicht enthalten ist die Pruefung, ob deine "
                       "Forderung inhaltlich berechtigt ist."),
    }


CASES = []


def case(name, mutate, expect_ok, reason=""):
    """reason = Teilstring, der in der Begruendung stehen MUSS (nur bei rot).

    Ohne diese Pflicht kann ein Fall aus dem falschen Grund rot werden und die
    eigentlich gemeinte Regel bleibt ungeprueft (genau das ist im ersten Lauf
    passiert: die FAQ-Frage 'Ist das eine Rechtsberatung?' hat 4 Faelle maskiert).
    """
    CASES.append((name, mutate, expect_ok, reason))


case("Positivfall unveraendert", lambda d: d, True)
case("Disclaimer 'keine Rechtsberatung' erlaubt",
     lambda d: d | {"abgrenzung": "Dies ersetzt keine Rechtsberatung."}, True)
case("Disclaimer 'ohne Garantie' erlaubt",
     lambda d: d | {"abgrenzung": "Der Entwurf wird ohne Garantie auf Erfolg geliefert."}, True)
case("FAQ-Frage nach Rechtsberatung ist kein Claim",
     lambda d: d, True)
case("bietet Rechtsberatung an -> rot",
     lambda d: d | {"intro": "Wir bieten dir eine solide Rechtsberatung zu deinem Fall."},
     False, "rechtsberatung")
case("Erfolgsgarantie -> rot",
     lambda d: d | {"intro": "Mit Erfolgsgarantie fuer deine Bewerbung."},
     False, "erfolgsgarantie")
case("'kostenlos' -> rot",
     lambda d: d | {"intro": "Die erste Fassung ist kostenlos und unverbindlich."},
     False, "kostenlos")
case("garantiert ohne Verneinung -> rot",
     lambda d: d | {"intro": "Der Text wirkt garantiert bei jedem Empfaenger."},
     False, "garantie")
case("fremder Preis 49 EUR -> rot",
     lambda d: d | {"intro": "Der Auftrag kostet pauschal 49 EUR fuer den gesamten Umfang."},
     False, "fremder Preis")
case("erlaubter Preis 7,99 EUR -> gruen",
     lambda d: d | {"intro": "Die mittlere Stufe kostet 7,99 EUR und enthaelt eine Korrekturschleife dazu."}, True)
case("HTML im Text -> rot",
     lambda d: d | {"intro": "Hier <script>alert(1)</script> steht boeser Code."},
     False, "HTML")
case("Markdown-Zaun -> rot",
     lambda d: d | {"intro": "```json hier faengt der Zaun an und laeuft weiter```"},
     False, "HTML/Markdown")
case("zu kurz -> rot",
     lambda d: {"intro": "Kurz.", "lieferung": ["a b c", "d e f"],
                "brauchen": ["g h i", "j k l"],
                "faq": [{"f": "x y z", "a": "a b c"}, {"f": "q r s", "a": "t u v"}],
                "abgrenzung": "Nichts weiter."}, False, "Laenge")
case("Schluessel fehlt -> rot",
     lambda d: {k: v for k, v in d.items() if k != "faq"}, False, "Schluessel fehlt")
case("faq zu klein -> rot", lambda d: d | {"faq": d["faq"][:1]}, False, "faq")
case("lieferung leer -> rot", lambda d: d | {"lieferung": []}, False, "lieferung")
case("kein dict -> rot", lambda d: ["a", "b"], False, "kein JSON-Objekt")
# Widerspruchsregel — der reale 3b-Fehlgriff vom 2026-08-10 als Testfall
case("'kann nicht angepasst werden' -> rot",
     lambda d: d | {"faq": d["faq"][:2] + [{
         "f": "Kann ich den Text noch aendern?",
         "a": "Die Mahnung wird exakt wie in der Vorlage erstellt und kann nicht "
              "angepasst werden, das ist Teil des Verfahrens."}]},
     False, "Widerspruch")
case("'keine Korrekturschleife' -> rot",
     lambda d: d | {"abgrenzung": "Es sind keine Korrekturschleifen enthalten, "
                                  "die Lieferung erfolgt einmalig und endgueltig."},
     False, "Widerspruch")
case("Korrekturschleife positiv erwaehnt -> gruen",
     lambda d: d | {"abgrenzung": "Nicht enthalten ist der Versand. Eine "
                                  "Korrekturschleife ist ab 7,99 EUR dabei."}, True)
# Anrede — der reale 7b-Fehlgriff vom 2026-08-10 als Testfall
case("durchgehendes Siezen -> rot",
     lambda d: d | {"intro": "Diese Seite ist fuer Sie, wenn Sie eine Mahnung "
                             "senden moechten. Wir bieten Ihnen ein Konzept, "
                             "um Ihre Forderung klar zu formulieren."},
     False, "Anrede-Bruch")
case("Du-Form bleibt gruen",
     lambda d: d | {"intro": "Diese Seite ist fuer dich, wenn du eine Mahnung "
                             "senden moechtest. Du bekommst einen Text, mit dem "
                             "du deine Forderung klar formulierst und nachfasst."}, True)
# Leistungskette — der reale 7b-Fehlgriff vom 2026-08-13
# (blog/ghostwriter-buch-kosten.html) als Testfall. Beide Saetze kamen
# WOERTLICH aus dem Modell und haben jede damalige Schranke passiert.
case("'einen Ghostwriter fuer dich finden' -> rot",
     lambda d: d | {"intro": "Diese Seite ist fuer dich, wenn du ein Buch planst. "
                             "Wir loesen das, indem wir einen Ghostwriter fuer "
                             "dich finden, der dein Buch schreibt."},
     False, "falsche Leistungskette")
case("'unsere Ghostwriter' -> rot",
     lambda d: d | {"faq": d["faq"][:2] + [{
         "f": "Welche Themen sind moeglich?",
         "a": "Unsere Ghostwriter schreiben ueber ein breites Spektrum an "
              "Themen, solange es zum Publikum passt."}]},
     False, "falsche Leistungskette")
case("'bereit zum Veroeffentlichen' -> rot",
     lambda d: d | {"lieferung": ["Ein gepruefter Endtext, bereit zum "
                                  "Veroeffentlichen", "Eine Gliederung",
                                  "Ein Probekapitel"]},
     False, "falsche Leistungskette")
case("'druckreif' -> rot",
     lambda d: d | {"lieferung": ["Ein druckreifes Manuskript",
                                  "Eine Gliederung", "Ein Probekapitel"]},
     False, "falsche Leistungskette")
case("ehrliche Buch-Abgrenzung bleibt gruen",
     lambda d: d | {"abgrenzung": "Nicht enthalten ist ein komplettes Buch: du "
                                  "bekommst Expose, Gliederung und einen "
                                  "Probekapitel-Entwurf zum Weiterschreiben."}, True)
case("Wort 'Ghostwriter' allein bleibt gruen",
     lambda d: d | {"intro": "Du vergleichst gerade, was ein Ghostwriter fuer "
                             "ein Buch kostet. Hier siehst du, welchen kleinen "
                             "Einstieg du stattdessen bekommst."}, True)


def main():
    ok = fail = 0
    for name, mut, expect, reason in CASES:
        got, why = E.validate(mut(good()))
        right = (got == expect)
        # rot ist nur dann ein bestandener Fall, wenn es AUS DEM GEMEINTEN GRUND rot ist
        if right and not expect and reason and reason.lower() not in why.lower():
            right, why = False, f"rot aus falschem Grund: {why}"
        ok += right
        fail += not right
        print(f"[{'ok  ' if right else 'FAIL'}] {name}  -> {got} ({why})")
    print(f"\nSelftest: {ok} ok, {fail} fail von {len(CASES)}")
    # Mutationsprobe: ohne Regeln muss der Selftest zerbrechen
    real = E.FORBIDDEN, E.NEEDS_NEGATION, E.CONTRADICTIONS
    E.FORBIDDEN, E.NEEDS_NEGATION, E.CONTRADICTIONS = [], [], []
    broke = sum(1 for n, m, ex, r in CASES if (E.validate(m(good()))[0] == ex) is False)
    E.FORBIDDEN, E.NEEDS_NEGATION, E.CONTRADICTIONS = real
    print(f"MUTATIONSPROBE (Regeln entfernt): {broke} Faelle kippen "
          f"-> {'OK' if broke >= 3 else 'ZU SCHWACH'}")
    return 0 if fail == 0 and broke >= 3 else 1


if __name__ == "__main__":
    sys.exit(main())
