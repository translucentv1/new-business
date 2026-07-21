"""Minimal CDP probe: open a page, send Page.bringToFront, read location.href."""
import asyncio
import json
import urllib.request
import random
import websockets

CDP_BASE = "http://127.0.0.1:9223"

def get_json(path):
    with urllib.request.urlopen(f"{CDP_BASE}{path}", timeout=5) as r:
        return json.load(r)

async def cdp(ws_url):
    return await websockets.connect(
        ws_url, max_size=None, ping_interval=None,
        close_timeout=4, open_timeout=8,
    )

async def send(ws, obj, t=20):
    oid = random.randint(1, 10**6)
    await ws.send(json.dumps(dict(obj, id=oid)))
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=t))
        if msg.get("id") == oid:
            return msg

async def test_tab(ws_url, label):
    print(f"--- test_tab {label} ---")
    print(f"ws_url: {ws_url}")
    async with await cdp(ws_url) as ws:
        r = await send(ws, {"method":"Page.bringToFront","params":{}}, t=8)
        print("bringToFront:", r.get("result"), "err:", r.get("error"))
        await asyncio.sleep(4)
        # Simple string returns
        for expr in ['"hello_str"', 'location.href', 'document.title',
                     'document.body ? String(document.body.innerText.length) : "noBody"',
                     'JSON.stringify({a:1,b:2})',
                     'typeof document.body',
                     '[1,2,3].join(",")',
                     'String(Math.random())']:
            r = await send(ws, {"method":"Runtime.evaluate",
                                "params":{"expression": expr, "returnByValue": True}},
                           t=10)
            v = r.get("result", {})
            print(f"  expr[{expr[:50]}] -> type={v.get('type')} val={str(v.get('value',''))[:200]}")
            print(f"     RAW: {json.dumps(r, default=str)[:400]}")

async def main():
    tabs = get_json("/json")
    # find first reddit tab
    rt = [t for t in tabs if t.get("type")=="page" and "reddit.com" in (t.get("url") or "")]
    for i, t in enumerate(rt[:3]):
        await test_tab(t["webSocketDebuggerUrl"], f"reddit-tab-{i} url={t['url'][:80]}")
        print()

asyncio.run(main())
