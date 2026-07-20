"""CDP helper over websockets (Vivaldi-compatible, Windows-safe).

Critical: websockets.connect() needs open_timeout on Windows or the
handshake hangs. Use ping_interval=None + open_timeout=8 + close_timeout=4.

Reads page DOM + fills forms on an already-authenticated browser that the
user launched with --remote-debugging-port=9223 against their profile.
"""
import json, asyncio, websockets, urllib.request

CDP = "http://127.0.0.1:9223"


def _tabs():
    return json.loads(urllib.request.urlopen(f"{CDP}/json", timeout=10).read())


def find_tab(keyword: str):
    for t in _tabs():
        if t.get("type") == "page" and keyword in (t.get("url") or "").lower():
            return t
    return None


async def _roundtrip(ws_url, payload, timeout=12, bring_to_front=True):
    async with websockets.connect(ws_url, max_size=None, ping_interval=None,
                                  close_timeout=4, open_timeout=8) as ws:
        if bring_to_front:
            await asyncio.wait_for(ws.send(json.dumps(
                {"id": 0, "method": "Page.bringToFront", "params": {}})), timeout=8)
        await asyncio.wait_for(ws.send(json.dumps(payload)), timeout=8)
        while True:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if m.get("id") == payload["id"]:
                return m


def eval_tab(keyword: str, expression: str, timeout: int = 40):
    t = find_tab(keyword)
    if not t:
        return "NO_TAB:" + keyword
    m = asyncio.run(asyncio.wait_for(
        _roundtrip(t["webSocketDebuggerUrl"],
                   {"id": 1, "method": "Runtime.evaluate",
                    "params": {"expression": expression, "returnByValue": True,
                               "awaitPromise": True}}),
        timeout=timeout))
    if "error" in m:
        return "CDP_ERR:" + str(m["error"])[:200]
    return m.get("result", {}).get("result", {}).get("value")


async def _cmd(ws_url, method, params, timeout=12):
    async with websockets.connect(ws_url, max_size=None, ping_interval=None,
                                  close_timeout=4, open_timeout=8) as ws:
        await asyncio.wait_for(ws.send(json.dumps(
            {"id": 1, "method": method, "params": params})), timeout=8)
        while True:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if m.get("id") == 1:
                return m


def navigate_tab(keyword: str, url: str, timeout: int = 40):
    t = find_tab(keyword)
    if not t:
        return "NO_TAB:" + keyword
    return asyncio.run(asyncio.wait_for(
        _roundtrip(t["webSocketDebuggerUrl"],
                   {"id": 1, "method": "Page.navigate", "params": {"url": url}}),
        timeout=timeout))


def cdp_cmd(keyword, method, params, timeout=30):
    t = find_tab(keyword)
    if not t:
        return "NO_TAB:" + keyword
    return asyncio.run(asyncio.wait_for(
        _cmd(t["webSocketDebuggerUrl"], method, params), timeout=timeout))


def set_file_input(keyword, selector, filepath, timeout=30):
    """Mount a file onto a <input type=file> via DOM.setFileInputFiles (no OS dialog)."""
    # first resolve nodeId of the input
    node = cdp_cmd(keyword, "DOM.getDocument", {})
    # find the file input node by querySelector via Runtime
    node_id = cdp_cmd(keyword, "DOM.querySelector",
                      {"nodeId": node.get("result", {}).get("root", {}).get("nodeId"),
                       "selector": selector})
    nid = node_id.get("result", {}).get("nodeId")
    if not nid:
        return "NO_NODE:" + selector
    return cdp_cmd(keyword, "DOM.setFileInputFiles",
                   {"nodeId": nid, "files": [filepath]})



if __name__ == "__main__":
    txt = eval_tab("payouts", "document.body.innerText")
    print((txt or "")[:800])
