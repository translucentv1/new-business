# Spec: Download-Gate & Preview-Fulfillment (Conversion-Hebel)

**Erstellt:** 2026-07-18 · **Von:** Claude Code (leitender Kopf) · **Ausfuehrung:**
Hermes (autonom, ueber Nacht) · **Grundlage:** ADR-0013, `grill-with-docs`-Session.
**Tracker-Tickets:** TB-8, TB-9, TB-10 (in `kanban.db`).

## Problem Statement
Aus Kaeufer-Sicht: Auf der Produktseite steht bereits der **komplette, kostenlose
Buchtext**. Es gibt keinen Grund, 3,99 EUR zu zahlen — der Wert ist schon gratis
und vollstaendig da. Der bezahlte Kauf fuehlt sich wie eine Spende an, nicht wie
ein Erwerb. Das ist die wahrscheinlichste Ursache fuer "0 Sales trotz Live-Kasse".

## Solution
Aus Kaeufer-Sicht: Die oeffentliche Seite zeigt nur noch eine **Leseprobe**
(Titel, Autor, Inhaltsverzeichnis, erstes Kapitel) und einen Kaufbutton. Das
**vollstaendige, offline lesbare eBook** (eine gestylte, self-contained Datei)
gibt es erst **nach der Zahlung** — Stripe leitet direkt zur Download-Datei
weiter. Der Wert liegt damit hinter der Kasse, nicht davor.

## User Stories
1. Als Interessent will ich auf der Produktseite eine aussagekraeftige Leseprobe
   (Klappentext, Inhaltsverzeichnis, erstes Kapitel) sehen, damit ich die
   Qualitaet der Aufbereitung einschaetzen kann, bevor ich kaufe.
2. Als Interessent will ich NICHT den ganzen Text gratis auf der Seite sehen,
   damit der Kauf einen erkennbaren Mehrwert hat.
3. Als Kaeufer will ich nach der Zahlung sofort und ohne Umweg zur vollstaendigen
   eBook-Datei gelangen, damit ich bekomme, wofuer ich bezahlt habe.
4. Als Kaeufer will ich das eBook als **eine** ordentliche, offline lesbare
   Datei erhalten (nicht als Roh-Textdump), damit es sich wie ein Produkt anfuehlt.
5. Als Kaeufer will ich, dass der Download nach Zahlung tatsaechlich existiert und
   200 liefert (kein 404), damit kein Refund/Chargeback-Grund entsteht.
6. Als Betreiber will ich, dass die Download-Datei NICHT ueber Suche/Sitemap/
   interne Links auffindbar ist, damit sie nicht das Preview-Gate aushebelt.
7. Als Betreiber will ich, dass die Umstellung des Stripe-Redirects erst passiert,
   nachdem Preview + Download-Datei fuer ALLE 8 Produkte MEASURED-gruen sind,
   damit kein Live-Kauflink ins Leere zeigt.
8. Als Betreiber will ich die bekannte Schwaeche (geteilte URL umgeht das Gate)
   dokumentiert und ehrlich benannt haben, damit niemand falsche Sicherheit annimmt.
9. Als Betreiber will ich, dass ueber Nacht NICHTS oeffentlich gepusht wird —
   nur lokale Commits — damit ich morgens alles pruefen und selbst freigeben kann.
10. Als Betreiber will ich pro Loop-Tick nur EINEN Teilschritt, jeweils mit
    frischem Beleg (MEASURED), damit ein schwaches Modell keinen Flurschaden anrichtet.
11. Als Kaeufer eines beliebigen der 8 Buecher will ich dasselbe Verhalten, damit
    das Gate nicht nur fuer ein Vorzeige-Produkt funktioniert.

## Implementation Decisions
- **Betroffene Module:** `scripts/landingpage_gen.py` (Preview statt Volltext +
  Download-Datei-Generierung), `scripts/stripe_uploader.py` (Redirect-Ziel),
  ggf. neues kleines Modul `scripts/deliverable_gen.py` fuer die eBook-Datei.
- **Preview-Umfang:** Titel, Autor, Klappentext (`description.md` erste Zeilen),
  vollstaendiges Inhaltsverzeichnis (aus `meta.json` chapters/TOC), **erstes
  Kapitel** im Volltext. Danach ein "Weiterlesen im gekauften eBook"-Hinweis.
- **Download-Pfad (Gate):** `docs/dl/<hash>/<slug>.html`, mit
  `hash = sha256(f"{book_id}:{SALT}")[:16]`. `SALT` aus Datei `.dl_salt`
  (gitignored, lokal erzeugt falls fehlt). Der Pfad wird NICHT in `sitemap.xml`
  gelistet und via `robots.txt` `Disallow: /dl/` von Crawlern ausgeschlossen.
- **Deliverable-Format:** Tier-1 self-contained HTML (Georgia-Reader-Style,
  voller Text inline, keine externen Assets). Tier-2 EPUB via stdlib `zipfile`
  ist ein SEPARATES spaeteres Ticket, nicht Teil dieser Nacht.
- **Stripe-Redirect:** `after_completion[redirect][url]` je Link auf die absolute
  Download-URL (`https://translucentv1.github.io/new-business/dl/<hash>/<slug>.html`).
  Umstellung ist der LETZTE Schritt (TB-10), blockiert durch TB-8 + TB-9.
- **Kein PDF, keine neue pip-Abhaengigkeit, kein Serverless-Deploy.** Alles
  stdlib, alles auf bestehender GitHub-Pages-Infra.
- **Publish:** Ueber Nacht NUR lokale Commits (`git commit`), KEIN `git push`,
  KEIN `publish_site.py`-Push. Der Push auf gh-pages ist ein bewusster
  Morgen-Schritt des Nutzers nach Review.

## Testing Decisions
- Guter Test = prueft **beobachtbares Verhalten**, nicht Implementierung, und
  gegen realistische Eingaben (echte `content.md` der 8 Produkte, nicht Spielzeug).
- `scripts/test_pd_processor.py` bleibt gruen (Produkt-QA-Gate, 4/4).
- Neuer Test `scripts/test_download_gate.py`:
  - Preview-HTML enthaelt Inhaltsverzeichnis + 1. Kapitel, aber **NICHT** den
    Volltext des letzten Kapitels (Assertion gegen einen Marker-String aus dem
    letzten Kapitel jedes Produkts).
  - Download-Datei existiert je Produkt, ist self-contained (kein `http://`/
    `https://`-Asset-Link, kein `<script src`), enthaelt den Volltext.
  - Der Hash-Pfad ist deterministisch reproduzierbar aus id+salt.
  - `robots.txt` enthaelt `Disallow: /dl/`; `sitemap.xml` enthaelt KEINEN
    `/dl/`-Eintrag.
- Prior Art: `scripts/test_pd_processor.py` (Regressionstests gegen echte
  Produkt-Eingaben) ist die Vorlage fuer Stil und Strenge.
- **MEASURED-Gate vor Redirect-Umstellung:** alle obigen Tests gruen + je
  Produkt `curl`-loses Datei-Existenz-Check (Datei liegt unter erwartetem Pfad).

## Out of Scope (heute Nacht ausdruecklich NICHT)
- Serverseitig verifiziertes Gate (signierte URL / Serverless + Stripe-Session).
- EPUB/PDF-Erzeugung (EPUB = spaeteres eigenes Ticket, PDF gar nicht).
- Oeffentlicher Push auf gh-pages (macht der Nutzer morgens).
- SEO-Flaechen-Ausbau (separates Mandat, hier bewusst zurueckgestellt).
- Aenderungen am Produktinhalt/Korpus, an Preisen, an der Zahlungs-Rail.
- Alles unter Hard Stops (Accounts, Keys, Geldbewegung, OAuth, Social-Posting).

## Further Notes
- Ausfuehrendes Modell ist schwach (`tencent/hy3:free`) und laeuft unbeaufsichtigt.
  Deshalb: kleine Schritte, ein Ticket pro Tick, jeder Schritt MEASURED belegt,
  bei Unsicherheit Stopp + ehrlicher Statusping statt Raten.
- Reihenfolge/Blocker: TB-8 (Preview + Deliverable-Gen) -> TB-9 (Tests + QA gruen)
  -> TB-10 (Stripe-Redirect umstellen, lokal committen). TB-10 blockiert durch TB-9.
- Bekanntes Loch (ADR-0013) ist akzeptiert und dokumentiert, kein Blocker.
