"""Check Reddit login status via CDP. BringToFront + read body text."""
import asyncio, json, urllib.request
import websockets  # available in hermes venv

CDP_BASE = "http://127.0.0.1:9223"

def get_json(path):
    with urllib.request.urlopen(f"{CDP_BASE}{path}", timeout=5) as r:
        return json.load(r)

async def cdp_eval(ws_url, expr, to=15):
    async with websockets.connect(ws_url, max_size=None, ping_interval=None,
                                  close_timeout=4, open_timeout=8) as ws:
        async def send(obj, t=15):
            return await asyncio.wait_for(_roundtrip(ws, obj, t), timeout=t)
        await send({"method":"Page.bringToFront","params":{}}, t=8)
        r = await send({"method":"Runtime.evaluate","params":{
            "expression": expr, "returnByValue": True, "awaitPromise": True}}, t=to)
        try:
            return r["result"]["result"]["value"]
        except Exception:
            return r

async def _roundtrip(ws, obj, t):
    import random
    oid = random.randint(1, 10**6)
    payload = dict(obj, id=oid)
    while True:
        await ws.send(json.dumps(payload))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=t))
        if msg.get("id") == oid:
            return msg

async def main():
    tabs = get_json("/json")
    reddits = [t for t in tabs if t.get("type")=="page" and "reddit.com/r/Finanzen" in (t.get("url") or "")]
    if not reddits:
        print("No r/Finanzen tab found")
        return
    tab = reddits[0]
    print(f"Tab URL: {tab['url']}")
    text = await cdp_eval(tab["webSocketDebuggerUrl"], "document.body.innerText.slice(0, 3000)")
    print("=== PAGE TEXT (first 1500) ===")
    print(str(text)[:1500])
    logged_out_markers = ["Log In", "Anmelden", "Sign Up", "Registrieren"]
    is_out = any(m in str(text) for m in logged_out_markers)
    is_in = "Log Out" in str(text) or "About" in str(text) or "Create Post" in str(text)
    print(f"=== logged_out_marker={is_out} logged_in_marker={is_in} ===")

asyncio.run(main())
