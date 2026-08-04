# Ticket 6 — Rechtsseiten auf dem Kaufpfad produktionsreif machen

Typ: `wayfinder:task` (AFK bis auf EINEN Datenpunkt)
Status: **CLOSED 2026-08-04** — aufgelöst, siehe Auflösung am Ende
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
   muss (§ 356 Abs. 6 BGB — Zitat korrigiert 2026-08-04, Abs. 5 gilt nur fuer
   Dienstleistungen). Im Stripe-Payment-Link ist das nicht konfiguriert.
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

---

## Auflösung (2026-08-04, Commit `4b6f598`)

**Antwort: Ja, der Kaufpfad ist jetzt zumutbar — mit genau einem offenen
USER-Datenpunkt (Postanschrift), der nur noch an einer Stelle steht.**

### Gebaut

1. **`datenschutz.html` neu** (6257 B live). Art.-13-Pflichtangaben: Verantwortlicher
   per Verweis aufs Impressum (Anschrift existiert damit genau **einmal** im Repo),
   Verarbeiter Stripe (IE/US) und GitHub Pages (US), Rechtsgrundlagen
   Art. 6 Abs. 1 lit. b/c/f, Drittlandtransfer (SCC/DPF), Speicherdauer
   (§ 147 AO, § 257 HGB), Betroffenenrechte, Beschwerderecht.
   Tatsachenbasis frisch gemessen, nicht aus dem Befund übernommen:
   `curl -I` zeigt **kein** `Set-Cookie`, Grep über die Live-Seiten zeigt
   **keine** Third-Party-Ressourcen auf `rtd.html`/`thanks.html`.
2. **`agb.html` ent-templatisiert.** `[DEIN VOLLER NAME]` → Philipp Behnisch,
   `[EMAIL]` → philippbehnisch@gmail.com, `[DATUM]` → 4. August 2026,
   USt-Alternative → Kleinunternehmer § 19 UStG. `noindex` entfernt
   (live geprüft: `<meta name="robots" content="index,follow">`).
3. **Warnkasten ersetzt statt entfernt.** Er behauptet nicht mehr, das ganze
   Dokument sei ein Template, sondern benennt exakt das, was fehlt: die Anschrift.
   Das war die Vorgabe des Tickets — der Kasten verschwindet erst mit der Adresse.
4. **§ 3 Lieferfrist:** 24 Stunden Regelfall, 5 Werktage Maximum, Rücktrittsrecht
   bei Überschreitung. *Das ist eine DECISION, keine Messung* — gestützt darauf,
   dass der Fulfillment-Cron alle 2 h läuft; `gig.html` sagte bereits „binnen 24 h“,
   die Seiten widersprechen sich jetzt nicht mehr.
5. **§ 5 ehrlich gefasst.** Die alte Fassung behauptete faktisch das Erlöschen des
   Widerrufsrechts, obwohl die Zustimmung nie eingeholt wird. Jetzt steht dort,
   dass die Zustimmung **nicht** eingeholt wird und das 14-tägige Widerrufsrecht
   daher bestehen bleibt. Kosten: bis zu 14,99 € Rückerstattungsrisiko pro Sale.
   Technische Einholung → **Ticket 7**.

### Zwei Befunde, die im Ticket nicht standen

- **Der Adress-Platzhalter stand in 6 Seiten, nicht in 2.** Neben `impressum.html`
  und `agb.html` auch in `rtd.html`, `gig.html`, `lead_magnet.html` und
  `ki-text-service/index.html`. Alle vier zeigen jetzt auf das Impressum.
- **`scripts/request_delivery/index.html` war live erreichbar** (HTTP 200) — eine
  Altkopie der Verkaufsseite mit `[DEIN NAME]`, `[STRASSE]`, `[EMAIL]`,
  schlechter als die echte Seite und Duplicate Content. Kein Generator las sie
  (nur `MANUELLE_SCHRITTE.md` erwähnt sie). Jetzt `noindex`-Redirect auf `rtd.html`.

### MEASURED (live gegen translucentv1.github.io)

| Prüfung | Vorher | Nachher |
|---|---|---|
| `datenschutz.html` | HTTP 404 | **HTTP 200**, 6257 B |
| `agb.html` robots | `noindex` | `index,follow` |
| Platzhalter auf Live-Seiten | 6 Seiten | **nur `impressum.html`** |
| „TEMPLATE — NICHT VERÖFFENTLICHUNGSREIF“ live | sichtbar | weg (0 Treffer) |
| Datenschutz-Link auf rtd/thanks/index/agb/impressum | 0 | 1 je Seite |
| Sitemap-URLs | 1207 | 1210 (XML wohlgeformt) |
| Altkopie `scripts/request_delivery/index.html` | Platzhalter, HTTP 200 | Redirect, `noindex,follow` |
| `verify_rtd_chain.py` | KETTE_OK | **KETTE_OK** (3 LIVE-Links unverändert) |
| IndexNow | — | 1210 URLs → HTTP 200 *(angenommen, ≠ indexiert)* |

### Bleibt offen (USER-Blocker, nicht erfunden)

**Ladungsfähige Postanschrift** (Straße, PLZ, Ort) in `impressum.html`
Zeilen 20–21. Das ist jetzt die **einzige** Stelle im ganzen Repo.
Ohne sie ist § 5 DDG nicht erfüllt — das ließ sich nicht autonom lösen und
wurde deshalb nicht kaschiert.
