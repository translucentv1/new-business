# Ticket 6 — Rechtsseiten auf dem Kaufpfad produktionsreif machen

Typ: `wayfinder:task` (AFK bis auf EINEN Datenpunkt)
Status: **OPEN** — auf der Frontier, sofort bearbeitbar
Blockiert durch: nichts
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

Der Kaufpfad (`rtd.html` → Stripe → `thanks.html`) ist technisch bewiesen
(KETTE_OK), aber die Rechtsseiten daneben sind es nicht. Was muss passieren,
damit ein echter Besucher nicht beim ersten Klick auf „AGB“ abspringt — und
damit die Seite DSGVO-seitig nicht offen liegt?

## Befund (MEASURED 2026-08-04)

| Prüfung | Ergebnis |
|---|---|
| `curl .../datenschutz.html` | **HTTP 404** |
| `ls datenschutz.html` | existiert lokal nicht |
| `git ls-tree -r HEAD \| grep datenschutz` | nicht in git |
| `curl .../agb.html` | HTTP 200, 4288 B |
| `curl .../impressum.html` | HTTP 200, 1592 B |
| Third-Party-Scripts in rtd/thanks | **keine** |
| `Set-Cookie` von GitHub Pages | **keiner** |

1. **`datenschutz.html` fehlt vollständig.** Nicht live, nicht lokal, nicht in
   git — sie wurde nie gebaut. Kein toter Link (nichts verlinkt sie), aber eine
   fehlende Pflichtseite: über Stripe-Checkout werden Name, E-Mail, Zahlungs-
   und Adressdaten erhoben, Hosting läuft über GitHub Pages (US-Drittland).
   DSGVO Art. 13 verlangt die Information am Erhebungspunkt.
2. **`agb.html` ist live, von `rtd.html` verlinkt — und sichtbar unfertig.**
   Sie zeigt einen orangefarbenen Kasten
   `[TEMPLATE — NICHT VERÖFFENTLICHUNGSREIF]` sowie die Platzhalter
   `[DEIN VOLLER NAME]`, `[EMAIL]`, `[STRASSE HAUSNUMMER]`, `[PLZ ORT]`,
   `[DATUM]`, `[LIEFERFRIST]`. Zusätzlich trägt sie
   `<meta name="robots" content="noindex">`.
   Für einen zahlenden Besucher ist das ein sofortiger Vertrauensabbruch.
3. **`impressum.html` ist fast fertig.** Echte Daten sind vorhanden
   (Philipp Behnisch, philippbehnisch@gmail.com, +49 1523 7977826,
   Kleinunternehmer § 19 UStG). Offen sind nur `[Straße Hausnummer]` und
   `[PLZ Ort]`.
4. **Widerrufs-Zustimmung fehlt technisch.** `agb.html` § 5 sagt selbst, dass
   die Zustimmung zum vorzeitigen Leistungsbeginn per Checkbox eingeholt werden
   muss (§ 356 Abs. 5 BGB). Im Stripe-Payment-Link ist das nicht konfiguriert.
   Folge: Das Widerrufsrecht erlischt **nicht** — ein Kunde kann nach Lieferung
   14 Tage lang widerrufen.

## Was autonom erledigt werden kann

- `datenschutz.html` vollständig bauen. Alle nötigen Fakten sind MEASURED:
  kein Tracking, keine eigenen Cookies, Verarbeiter = Stripe + GitHub Pages,
  Zweck = Vertragserfüllung (Art. 6 Abs. 1 lit. b).
  Verantwortlichen per Verweis auf das Impressum benennen — dann existiert die
  Anschrift genau **einmal** im Repo statt dreimal.
- `agb.html` ent-templatisieren: `[DEIN VOLLER NAME]` → Philipp Behnisch,
  `[EMAIL]` → philippbehnisch@gmail.com, `[DATUM]` → echtes Datum,
  `[LIEFERFRIST]` → an das anpassen, was `rtd.html` tatsächlich zusagt,
  Umsatzsteuer-Alternative → Kleinunternehmer (wie im Impressum belegt).
- Verlinkung: `datenschutz.html` von `rtd.html`, `thanks.html`, `index.html`,
  `impressum.html`, `agb.html` aus erreichbar machen, in `sitemap.xml`
  aufnehmen, per IndexNow einreichen.

## Was USER-Blocker bleibt (NICHT erfinden)

- **Postanschrift (Straße, PLZ, Ort).** § 5 DDG verlangt sie im Impressum.
  Ohne sie bleibt die Seite unvollständig — egal was sonst gebaut wird.
  Ziel dieses Tickets: den Blocker auf **eine einzige Stelle** reduzieren.
- Der Hinweis „kein Ersatz für Rechtsberatung“ bleibt stehen. Der
  `[TEMPLATE — NICHT VERÖFFENTLICHUNGSREIF]`-Kasten darf erst verschwinden,
  wenn die Anschrift drin ist — ihn vorher zu entfernen wäre kosmetischer
  Selbstbetrug, kein Fortschritt.

## Entscheidung, die daran hängt

Ob der Kaufpfad einem echten Besucher überhaupt zumutbar ist. Solange die AGB
sich selbst als unfertig bezeichnet, ist jede Traffic-Arbeit (Ticket 3, Ticket 5)
verschwendet — der Besucher käme an, sähe den Warnkasten und ginge.
