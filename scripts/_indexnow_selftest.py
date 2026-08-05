#!/usr/bin/env python3
"""Fault-Injection-Harness fuer indexnow_submit.py (Ticket 19).

Konvention aus Ticket 14-18: es wird KEIN Verhalten nachgebaut. Geladen wird die
ECHTE main() des Moduls; injiziert werden nur
  - die HTTP-Antworten (Modul-Attribut `http` wird ersetzt) und
  - die lokale sitemap.xml (Modul-Attribut `SITEMAP` zeigt auf eine Temp-Datei).

Dadurch laeuft derselbe Harness auch gegen einen ALT-STAND, der per `git show`
in eine Sandbox gelegt wurde -> Blindheit wird AUSGEFUEHRT, nicht argumentiert.

WICHTIG: es wird nie eine echte Einreichung ausgeloest. Sobald `http` ersetzt
ist, geht kein Byte ins Netz; jeder Aufruf wird protokolliert.
"""
from __future__ import annotations

import importlib.util
import io
import os
import sys
import tempfile
import uuid
from contextlib import redirect_stderr, redirect_stdout

NET_ERROR = 0  # so meldet http() Netz-/DNS-Fehler


def load_module(path: str, name: str | None = None):
    """Laedt eine Python-Datei als frisches Modul (Alt-Stand oder Produktivcode)."""
    name = name or ("indexnow_mod_" + uuid.uuid4().hex[:8])
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("kann Modul nicht laden: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sitemap_xml(urls) -> str:
    body = "".join("<url><loc>%s</loc></url>" % u for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + body + "</urlset>")


class FakeNet:
    """Ersetzt indexnow_submit.http(). Kennt drei Ziele: Key, Live-Sitemap, Endpoint."""

    def __init__(self, mod, *, key=None, live_sitemap=None, submit_codes=None):
        self.mod = mod
        # key: (status, body) — default: gesunde Key-Datei
        self.key = key if key is not None else (200, mod.KEY)
        # live_sitemap: (status, body) oder None = "wird nicht gebraucht"
        self.live_sitemap = live_sitemap
        # submit_codes: Liste von Statuscodes, einer pro Batch
        self.submit_codes = list(submit_codes or [200])
        self.submits = []      # protokollierte urlList je Batch
        self.calls = []        # alle angefragten URLs

    def __call__(self, url, data=None, headers=None, timeout=60, maxlen=400):
        """Bildet den Vertrag des echten http() nach — INKLUSIVE Kuerzung.

        Am 2026-08-05 hat eine Attrappe ohne Kuerzung einen echten Defekt
        verdeckt: das Produktiv-http() schnitt jeden Body auf 400 Zeichen ab,
        wodurch die Live-Sitemap wie 3 statt 1220 URLs aussah. Eine Attrappe,
        die groesszuegiger ist als die Realitaet, macht den Selftest blind.
        """
        self.calls.append(url)

        def cut(body):
            return body if maxlen is None else body[:maxlen]

        if data is not None:
            import json
            payload = json.loads(data.decode("utf-8"))
            self.submits.append(payload.get("urlList", []))
            code = self.submit_codes[min(len(self.submits) - 1,
                                         len(self.submit_codes) - 1)]
            return code, cut("" if code in (200, 202)
                             else "injizierter Fehler %s" % code)
        if url == self.mod.KEY_URL:
            return self.key[0], cut(self.key[1])
        if self.live_sitemap is not None:
            return self.live_sitemap[0], cut(self.live_sitemap[1])
        return (404, cut("unerwartete URL im Selftest: %s" % url))

    @property
    def submitted_urls(self):
        out = []
        for batch in self.submits:
            out.extend(batch)
        return out


def run_case(mod, *, local_urls=None, local_sitemap_missing=False,
             key=None, live_sitemap=None, submit_codes=None,
             argv=None, batch=None):
    """Fuehrt die ECHTE main() des Moduls gegen injizierte Antworten aus.

    Rueckgabe: (rc, stdout+stderr, FakeNet)
    """
    tmp = None
    old_sitemap, old_batch, old_http, old_argv = (
        mod.SITEMAP, getattr(mod, "BATCH", None), mod.http, sys.argv)
    try:
        if local_sitemap_missing:
            mod.SITEMAP = os.path.join(tempfile.gettempdir(),
                                       "nicht_vorhanden_%s.xml" % uuid.uuid4().hex[:8])
        else:
            fd, tmp = tempfile.mkstemp(suffix=".xml", prefix="t19_sitemap_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(sitemap_xml(local_urls or []))
            mod.SITEMAP = tmp
        fake = FakeNet(mod, key=key, live_sitemap=live_sitemap,
                       submit_codes=submit_codes)
        mod.http = fake
        if batch is not None:
            mod.BATCH = batch
        sys.argv = ["indexnow_submit.py"] + list(argv or [])
        buf = io.StringIO()
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = mod.main()
        except SystemExit as e:          # argparse
            rc = e.code if isinstance(e.code, int) else 1
        except Exception as e:           # Traceback-Faelle sichtbar machen
            import traceback
            buf.write("\nTraceback (selftest-gefangen): %r\n%s"
                      % (e, traceback.format_exc()))
            rc = 99
        return rc, buf.getvalue(), fake
    finally:
        mod.SITEMAP, mod.http, sys.argv = old_sitemap, old_http, old_argv
        if old_batch is not None:
            mod.BATCH = old_batch
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
