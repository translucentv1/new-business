"""END FINAL v8: kompletter Agent-Skill-Step-1-Flow.
s0='skill', s1='chatgpt-skill', s2='0: 2.99', name+desc -> Klick 'Next: Skill File' -> Step 2.
Getestet."""
import sys, os, time, json, urllib.request

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import cdp_helper as c
import websockets, asyncio


def get_box(tab_ws, text_fragment):
    async def send():
        async with websockets.connect(tab_ws, max_size=None, ping_interval=None, close_timeout=4, open_timeout=8) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
                "expression": """
(function(){
  var btns=[...document.querySelectorAll('div.action-button, button, a')];
  var target=null;
  for(var e of btns){ if((e.innerText||'').indexOf(%r)>=0){ target=e; break; } }
  if(!target) return JSON.stringify({err:'NO_BTN'});
  var r=target.getBoundingClientRect();
  return JSON.stringify({cx:r.x+r.width/2, cy:r.y+r.height/2, txt:target.innerText.trim()});
})()
""" % text_fragment, "returnByValue": True}}))
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
            return m.get("result", {}).get("result", {}).get("value")
    return asyncio.run(send())


def mouse_click(tab_ws, cx, cy):
    async def send():
        async with websockets.connect(tab_ws, max_size=None, ping_interval=None, close_timeout=4, open_timeout=8) as ws:
            for ev in ["mousePressed", "mouseReleased"]:
                await ws.send(json.dumps({"id": 1, "method": "Input.dispatchMouseEvent", "params": {
                    "type": ev, "x": cx, "y": cy, "button": "left",
                    "clickCount": 1 if ev == "mousePressed" else 0}}))
                await asyncio.wait_for(ws.recv(), timeout=8)
    return asyncio.run(send())


def set_select(index, value):
    return c.eval_tab("sell", r"""
(function(i, v){
  var s=document.querySelectorAll('select')[i];
  if(!s) return 'NOSEL'+i;
  v=(v||'').toLowerCase();
  for(var j=0;j<s.options.length;j++){
    if(s.options[j].text.toLowerCase().indexOf(v)>=0 || s.options[j].value.toLowerCase().indexOf(v)>=0){
      var n=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;
      n.call(s, s.options[j].value);
      s.dispatchEvent(new Event('input',{bubbles:true}));
      s.dispatchEvent(new Event('change',{bubbles:true}));
      if(s._valueTracker) s._valueTracker.setValue('');
      return 's'+i+'='+s.value;
    }
  }
  return 'OPTNF'+i+'('+v+')';
})(%d,%r)
""" % (index, value))


def main():
    t = c.find_pb_sell_tab()
    if not t or "sell" not in (t.get("url") or ""):
        c.navigate_tab("sell", "https://promptbase.com/sell")
        time.sleep(4)
        t = c.find_pb_sell_tab()
    print("SELL TAB:", t.get("url"))
    ws = t["webSocketDebuggerUrl"]

    print("s0:", set_select(0, "skill"))
    print("s1:", set_select(1, "chatgpt skill"))
    print("s2:", set_select(2, "2.99"))
    c.eval_tab("sell", r"""
(function(){
  function reactSet(el,v){var d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value');var n=d?d.set:Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype,'value').set;n.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));if(el._valueTracker)el._valueTracker.setValue('');}
  var ins=[...document.querySelectorAll('input[type=text],textarea')].filter(e=>e.placeholder||e.tagName==='TEXTAREA');
  if(ins[0])reactSet(ins[0],'Clean Code Reviewer');
  if(ins[1])reactSet(ins[1],'Reviews code like a strict senior engineer.');
})""")

    time.sleep(3)
    box = get_box(ws, "Next: Skill File")  # KORREKT: 'Skill File' nicht 'Prompt File'
    print("BOX:", box)
    if box and "cx" in box:
        b = json.loads(box)
        mouse_click(ws, b["cx"], b["cy"])
        print("CLICKED at", b["cx"], b["cy"])
    else:
        print("KEIN BUTTON")

    time.sleep(5)
    check = c.eval_tab("sell", r"""
(function(){
  var step=(document.body.innerText||'').match(/\d\/4/);
  var errs=[...document.querySelectorAll('*')].map(e=>(e.innerText||'').trim()).filter(t=>/^(please|select a|error|required|must|enter|fill|provide|choose)/i.test(t));
  var ins=[...document.querySelectorAll('input[type=text],textarea')].filter(e=>e.placeholder||e.tagName==='TEXTAREA');
  return JSON.stringify({step:step?step[0]:null, errs:errs.slice(0,5), ins:ins.length, url:location.href});
})()""")
    print("CHECK:", check)


if __name__ == "__main__":
    main()
