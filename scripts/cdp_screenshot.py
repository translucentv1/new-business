"""Capture screenshot of the reddit submit tab via CDP and save as PNG."""
import asyncio
import json
import urllib.request
import random
import base64
import websockets

CDP_BASE = "http://127.0.0.1:9223"

def get_json(path):
    with urllib.request.urlopen(f"{CDP_BASE}{path}", timeout=5) as r:
        return json.load(r)

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
    async with await cdp(tab["webSocketDebuggerUrl"]) as ws:
        await send(ws, {"method":"Page.bringToFront","params":{}}, t=8)
        await asyncio.sleep(3)
        # Capture full page screenshot
        r = await send(ws, {"method":"Page.captureScreenshot","params":{"format":"png","captureBeyondViewport":False}}, t=15)
        data = r.get("result",{}).get("data","")
        if not data:
            print("no data", r)
            return
        out = "C:/Users/phili/new-business/scripts/reddit_submit_screenshot.png"
        with open(out, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"saved: {out}")

asyncio.run(main())
