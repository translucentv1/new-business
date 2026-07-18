# Glossar — Neues Business (Self-Loop Entwurf)

- **free-to-build**: Kein Startbudget. Keine Bezahldienste vor belegtem Gewinn. Gewinn -> Reinvestition.
- **legal-only**: Keine Fake-Accounts, keine ToS-Umgehung, kein KYC/VPN/ID-Bypass.
- **harte Stopps**: Agent führt keine echten Schritte aus (Geld, Account, Upload, OAuth). Nutzer gibt frei.
- **PLR** (Private Label Rights): Lizenz, vorab erstellte Inhalte unter eigener Marke weiterzuverkaufen.
- **Public Domain**: Werk ohne Urheberrechtsschutz (EU: Leben+70 Jahre). Frei nutzbar.
- **Gumroad Discover**: Interne Marketplace-Suche auf Gumroad, bringt Traffic ohne eigene Werbung.
- **Tracer-Bullet-Ticket**: Schritt-3 Ticket, das einen schmalen, aber vollständigen Pfad durch alle Schichten schneidet.
- **Liquiditäts-Lücke**: Bei physischer Arbitrage: Payment-Holds + Verkaufslimits blockieren Reinvestition (Erfahrung arbitrage_bot).
- **DSGVO / Impressumspflicht**: Bei gewerblichem Online-Verkauf in DE gesetzlich nötig (MEASURED eRecht24).
- **Gewerbeanmeldung**: In DE Pflicht bei nachhaltiger Gewinnerzielungsabsicht (MEASURED Gewerberecht).
- **Self-Loop**: Agent entwirft im Kreislauf (grill -> spec -> tickets -> implement), Nutzer schaltet Real-Schritte frei.
- **Preview-Fulfillment**: Oeffentliche Produktseite zeigt nur Leseprobe (Titel, Inhaltsverzeichnis, 1. Kapitel) + Kaufbutton; der volle Text steckt hinter der Kasse (ADR-0013).
- **Download-Gate**: Das vollstaendige eBook liegt hinter dem Kauf, nicht davor. Auslieferung nach Zahlung via Stripe-`after_completion`-Redirect (ADR-0013).
- **Obscure-URL-Gate**: Download unter nicht erratbarem, gehashtem Pfad (`/dl/<sha>/...`), nur ueber den Stripe-Redirect erreichbar, nie oeffentlich verlinkt. Obscurity, KEINE Kryptographie — geteilte URL umgeht das Gate (bekanntes Loch, ADR-0013). Echtes serverseitig verifiziertes Gate = spaeteres TB.
- **Deliverable**: Die verkaufte Datei selbst. Tier-1 = self-contained HTML (zero-dep), Tier-2 = EPUB (stdlib zipfile). Kein PDF (keine Lib installiert, wuerde Infra mehren).
