# Ticket 31 — Der Alarmweg ist nur resolverseitig belegt, nicht end-to-end

Typ: `wayfinder:task` (AFK) · Status: **OFFEN** · unblockiert · Priorität: hoch
Hervorgegangen aus: [Ticket 30](30-zustellbarkeit-ungewacht.md) (GESCHLOSSEN)
Eltern: [wayfinder:map — Ersten realen Sale erzielen](../wayfinder_map.md)

## Question

`cron_delivery_audit.py` fragt den **produktiven Resolver**, ob ein Zustellziel
auflösbar ist. Das ist echt gemessen — aber es ist die Etappe **vor** dem Senden.
Belegt ist: „der Scheduler würde eine Adresse finden". **Nicht** belegt: „eine
Nachricht dieses Jobs kommt an."

Genau diese Lücke hat schon einmal 11 Tage gekostet (IndexNow-Branch-Falle) und
einmal den Kundenpfad betroffen (Publish-Etappe, Ticket 11). Die Antwort dort
war jeweils ein **Canary durch die echten Produktivfunktionen** —
`verify_publish_leg.py` ist die Bauform, die hier fehlt.

## Faktenlage (MEASURED, Ticket 30)

- 7 aktive Jobs → alle mit auflösbarem Ziel, `DELIVERY_OK`.
- End-to-End belegt ist **eine** Zustellung, und zwar die von Ticket 23
  (`bfb63346d942`, 23:58:50 `delivered to whatsapp:…@lid`).
- Für die in Ticket 30 reparierten Jobs `5e99ad47470f` (2. Ring) und
  `bae39ea51a60` (AI-CEO, trägt `ERSTER SALE`) ist **keine** eigene Zustellung
  gemessen. Sie zeigen resolverseitig auf dieselbe Adresse wie ein
  nachweislich zustellender Job — das ist ein starkes Indiz, kein Beleg.
- Verschärfend: der 2. Ring meldet auf dem OK-Pfad jetzt bewusst `[SILENT]`.
  Sein Zustellweg wird im Normalbetrieb also **nie** benutzt und kann still
  verrotten, ohne dass es jemandem auffällt — bis zum Alarm.

## Vorgehen

1. Canary in der Bauform von `verify_publish_leg.py`: **einmalig** eine echte
   Nachricht über den produktiven Zustellweg schicken (nicht nachgebaut —
   `_deliver_result` bzw. der reguläre Job-Pfad), Erfolg am **positiven**
   Logeintrag `delivered to …` festmachen, nicht an `last_delivery_error=None`
   (Merkregel Ticket 23: ein selbst genulltes Feld ist kein Messwert).
2. Der Canary muss sich selbst aufräumen und darf **keine** Produktionsjobs
   mutieren (Merkregel Ticket 28: Kopie statt Produktion).
3. Ergebnisworte + `--selftest` + Mutationsprobe wie bei jedem stehenden Tor.
4. Prüfen, ob der Canary regelmäßig laufen soll oder ein einmaliger Beleg
   genügt — ein Zustellweg, der nur im Alarmfall benutzt wird, ist genau der
   Fall, für den „einmal bewiesen" zu wenig sein könnte.

## Nicht vergessen (ASSUMED, vor dem Beantworten nachmessen)

- Ob `[SILENT]` wirklich nur den **Erfolgs**pfad unterdrückt, ist an
  `cron/scheduler.py` Z. 3833 gelesen (`if should_deliver and success and …`)
  und damit MEASURED **an der Quelle** — aber noch nie an einem echten
  Alarmlauf beobachtet. Das ist der Kern dieses Tickets.
- Die WhatsApp-Adresse darf in keinem Log/Commit im Klartext landen
  (`redact()`-Konvention aus `cron_delivery_audit.py` übernehmen).
