"""Post on r/Finanzen via CDP. Wert zuerst, Link in Top-Kommentar.

Phase 1 (dieses Skript): Navigate to submit, screenshot state, DUMP form.
Wir klicken NICHT automatisch auf Post. Der User validiert visuell.

Ausdafur: cdp_post_reddit_finanzen.py  (neu geschrieben, em-dash-free)
"""
import asyncio
import json
import urllib.request
import random
import websockets

CDP_BASE = "http://127.0.0.1:9223"

POST_TITLE = (
    "Kleines 3-Topf-System, mit dem ich seit einem halben Jahr zum ersten Mal "
    "weiss, wohin mein Geld geht (kostenlos nachbaubar)"
)
POST_BODY = (
    "Ich habe Jahre lang versucht, ein perfektes Budgeting-Setup hinzubekommen "
    "und immer wieder aufgegeben, weil es zu kompliziert wurde. Was haengen "
    "geblieben ist, ist dumm einfach:\n\n"
    "1. **Drei Toepfe:** Fixkosten / Flex (Lebensmittel, Freizeit) / Sparen. "
    "Alles ausser Fix landet erst mal im Flex-Topf.\n"
    "2. **Woechentlicher 10-Min-Check** statt monatlich. Sonntagabend: "
    "Flex-Topf sichten, uebriggebliebenes zur Haelfte in Sparen. Mehr braucht "
    "es bei mir nicht.\n"
    "3. **Ein einziges Sheet/Notion** als \"externes Gehirn\" - nicht fuer "
    "Motivation, sondern damit ich nicht im Kopf rechnen muss.\n\n"
    "Das Prinzip oben reicht voellig, kein Tool noetig. Falls jemand das fertig "
    "strukturierte Template (Notion + Google-Sheets, mit deutscher Kategorien-"
    "Logik und Monats-/Jahres-Auswertung) statt selbstbauen will: Ich habe "
    "eins aufbereitet - Link in den Kommentaren. Ist kein Muss."
)
COMMENT_BODY = (
    "Falls es jemand fertig will statt selbst zu bauen: Ich habe ein "
    "\"Finanz-Tracker DACH\"-Template (Notion + Sheets) gemacht, 4,99 EUR, "
    "weil ich selbst danach gesucht hatte und nur Engel-Preis-Murks fand. "
    "Eigene Empfehlung, daher hier als Kommentar:\n\n"
    "https://translucentv1.github.io/new-business/t/finanz-tracker-dach"
)


def get_json(path):
    with urllib.request.urlopen(f"{CDP_BASE}{path}", timeout=5) as r:
        return json.load(r)


def cdp_get_result(r):
    """Walk CDP wrapper dict: r -> result -> result -> value (handle nested)."""
    outer = r.get("result", {})
    if isinstance(outer, dict) and "result" in outer:
        inner = outer["result"]
        if isinstance(inner, dict):
            return inner.get("value", inner)
    # Fallback for top-level result already being a primitive
    return outer


async def cdp(ws_url):
    return await websockets.connect(
        ws_url, max_size=None, ping_interval=None,
        close_timeout=4, open_timeout=8,
    )


async def send(ws, obj, t=20):
    oid = random.randint(1, 10**6)
    payload = dict(obj, id=oid)
    await ws.send(json.dumps(payload))
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=t))
        if msg.get("id") == oid:
            return msg


async def bring_front_and_eval(ws, expr, t=20):
    await send(ws, {"method": "Page.bringToFront", "params": {}}, t=8)
    r = await send(
        ws,
        {"method": "Runtime.evaluate",
         "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}},
        t=t,
    )
    return cdp_get_result(r)


async def dump_state(ws, label):
    expr = r"""
    (function(){
      function vis(e){return e && e.offsetParent!==null;}
      const inputs=[...document.querySelectorAll('input')].filter(vis);
      const tas=[...document.querySelectorAll('textarea, [contenteditable=true], [role=textbox]')].filter(vis);
      const btns=[...document.querySelectorAll('button, [role=button]')].filter(vis)
        .filter(e=>/post|publish|veröffentl|senden|submit|absenden|text|link|poll/i.test(e.innerText||''))
        .filter(e=>(e.innerText||'').length<80);
      return JSON.stringify({
        url: location.href,
        inputs: inputs.map(e=>({ph:e.placeholder||'', val:(e.value||'').slice(0,80)})),
        textareas: tas.map(e=>({tag:e.tagName, val:(e.value||e.innerText||'').slice(0,200)})),
        btns: btns.map(e=>({t:(e.innerText||'').slice(0,40)})).slice(0,12)
      });
    })()
    """
    r = await bring_front_and_eval(ws, expr, t=10)
    val = r if isinstance(r, str) else str(r)
    print(f"=== {label} ===")
    try:
        parsed = json.loads(val)
        print("URL:", parsed.get("url"))
        print("inputs:", parsed.get("inputs"))
        print("textareas:", parsed.get("textareas"))
        print("buttons:", parsed.get("btns"))
    except Exception:
        print("raw:", val[:1000])
    print("=" * 50)


async def main():
    tabs = get_json("/json")
    reddits = [t for t in tabs if t.get("type") == "page"
               and "reddit.com/r/Finanzen" in (t.get("url") or "")]
    if not reddits:
        print("No r/Finanzen tab. Aborting.")
        return
    tab = reddits[0]
    print(f"Using tab: {tab['url']}")
    async with await cdp(tab["webSocketDebuggerUrl"]) as ws:
        await send(ws, {"method": "Page.bringToFront", "params": {}}, t=5)
        await asyncio.sleep(1)
        await send(ws, {"method": "Page.navigate",
                        "params": {"url": "https://www.reddit.com/r/Finanzen/submit"}},
                   t=20)
        # wait for navigate to settle - poll location.href stability
        for i in range(15):
            await asyncio.sleep(2)
            r = await bring_front_and_eval(ws, "location.href", t=8)
            v = r if isinstance(r, str) else str(r)
            if "/submit" in str(v):
                print(f"stab_href={v}")
                break
        await asyncio.sleep(3)  # extra settle for JS render
        await dump_state(ws, "After navigate to /submit")

        # Find and click any "Text" option if multiple types offered
        click_text = r"""
        (function(){
          const btns=[...document.querySelectorAll('button, [role=tab], [role=button]')];
          const t = btns.find(b => /^\s*Text\s*$/i.test(b.innerText||'') && b.offsetParent!==null);
          if (t){t.click(); return 'CLICKED_TEXT';}
          return 'NO_TEXT_BTN';
        })()
        """
        r = await bring_front_and_eval(ws, click_text, t=8)
        print("Click text result:", r if isinstance(r, str) else str(r)[:200])
        await asyncio.sleep(2)
        await dump_state(ws, "After click Text")

        # Fill title - first visible input
        set_title = (
            "(function(){\n"
            "  const inp=[...document.querySelectorAll('input')].filter(e=>e.offsetParent!==null)[0];\n"
            "  if(!inp) return 'NO_INPUT';\n"
            "  const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;\n"
            "  s.call(inp, " + json.dumps(POST_TITLE) + ");\n"
            "  inp.dispatchEvent(new Event('input',{bubbles:true}));\n"
            "  inp.dispatchEvent(new Event('change',{bubbles:true}));\n"
            "  return 'TITLE_SET:'+inp.value.length;\n"
            "})()"
        )
        r = await bring_front_and_eval(ws, set_title, t=8)
        print("Title:", r if isinstance(r, str) else str(r)[:200])

        # Fill body - first textarea, contenteditable div, or [role=textbox]
        set_body = (
            "(function(){\n"
            "  const qs=[...document.querySelectorAll('textarea, [contenteditable=true], [role=textbox]')];\n"
            "  const v=qs.filter(e=>e.offsetParent!==null);\n"
            "  const body=v.find(e=>(e.innerText||e.value||'').length<50) || v[0];\n"
            "  if(!body) return 'NO_BODY';\n"
            "  body.focus();\n"
            "  if(body.tagName==='TEXTAREA'){\n"
            "    const s=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;\n"
            "    s.call(body, " + json.dumps(POST_BODY) + ");\n"
            "    body.dispatchEvent(new Event('input',{bubbles:true}));\n"
            "    body.dispatchEvent(new Event('change',{bubbles:true}));\n"
            "  } else {\n"
            "    body.innerText=" + json.dumps(POST_BODY) + ";\n"
            "    body.dispatchEvent(new InputEvent('input',{bubbles:true,data:body.innerText}));\n"
            "  }\n"
            "  return 'BODY_SET:'+(body.innerText||body.value||'').length;\n"
            "})()"
        )
        r = await bring_front_and_eval(ws, set_body, t=8)
        print("Body:", r if isinstance(r, str) else str(r)[:200])
        await asyncio.sleep(2)
        await dump_state(ws, "After fill title+body")
        print("STOP - Form filled. Not auto-posting.")
        print("Re-run cdp_post_reddit_finanzen_submit.py to click Post after user review.")


asyncio.run(main())
