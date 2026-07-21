"""Dump full form structure on r/Finanzen/submit to find Title field."""
import asyncio
import json
import urllib.request
import random
import websockets

CDP_BASE = "http://127.0.0.1:9223"

def get_json(path):
    with urllib.request.urlopen(f"{CDP_BASE}{path}", timeout=5) as r:
        return json.load(r)

def cdp_get_result(r):
    outer = r.get("result", {})
    if isinstance(outer, dict) and "result" in outer:
        inner = outer["result"]
        if isinstance(inner, dict):
            return inner.get("value", inner)
    return outer

async def cdp(ws_url):
    return await websockets.connect(ws_url, max_size=None, ping_interval=None,
                                    close_timeout=4, open_timeout=8)

async def send(ws, obj, t=20):
    oid = random.randint(1, 10**6)
    await ws.send(json.dumps(dict(obj, id=oid)))
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=t))
        if msg.get("id") == oid:
            return msg

async def main():
    tabs = get_json("/json")
    rt = [t for t in tabs if t.get("type")=="page" and "reddit.com/r/Finanzen/submit" in (t.get("url") or "")]
    if not rt:
        print("No submit tab")
        return
    tab = rt[0]
    print(f"Tab: {tab['url']}")
    async with await cdp(tab["webSocketDebuggerUrl"]) as ws:
        await send(ws, {"method":"Page.bringToFront","params":{}}, t=8)
        await asyncio.sleep(3)
        # Full dump: describe every element with role, contentEditable, placeholder, aria-label
        expr = r"""
        (function(){
          function vis(e){return e && e.offsetParent!==null;}
          function desc(el){
            return {
              tag: el.tagName,
              role: el.getAttribute('role'),
              ce: el.getAttribute('contenteditable'),
              ph: el.placeholder || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '',
              label: el.getAttribute('label') || '',
              name: el.name || '',
              type: el.type || '',
              text: (el.innerText || el.value || '').slice(0, 80),
              cls: (el.className || '').toString().slice(0, 120)
            };
          }
          const inputs = [...document.querySelectorAll('input')].filter(vis);
          const tas = [...document.querySelectorAll('textarea')].filter(vis);
          const ces = [...document.querySelectorAll('[contenteditable=true]')].filter(vis);
          const rts = [...document.querySelectorAll('[role=textbox]')].filter(vis);
          const all = [...new Set([...inputs, ...tas, ...ces, ...rts])];
          return JSON.stringify({
            inputs: inputs.map(desc),
            tas: tas.map(desc),
            ces: ces.map(desc),
            rts: rts.map(desc),
            all: all.map(desc)
          }, null, 2);
        })()
        """
        r = await send(ws, {"method":"Runtime.evaluate","params":{"expression":expr,"returnByValue":True}}, t=10)
        v = cdp_get_result(r)
        print(str(v)[:6000])

asyncio.run(main())
