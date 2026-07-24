"""END FINAL v9: robuster kompletter Flow fuer 2 Skills (Max-2-Regel).

Nutzt die bewaehrten Bausteine aus pb_final8 (der funktioniert hat):
 - find_pb_sell_tab (repariert)
 - set_select mit value-match
 - echter Mausklick via CDP
 - Step1: s0='skill', s1='chatgpt-skill', s2='0: 2.99', name+desc
 - Next: 'Next: Skill File'
 - Step2: 9 Felder + gpt-5.5

Stoppt vor finalem Publish (Payout/Step3 = manuell).
"""
import sys, os, time, json, urllib.request

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import cdp_helper as c
import websockets, asyncio
import promptbase_lister as P


PUBLISH_IDX = [6, 2]  # clean-code-reviewer, root-cause-debugger


def ws_of():
    t = c.find_pb_sell_tab()
    return t["webSocketDebuggerUrl"] if t else None


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
  return JSON.stringify({cx:r.x+r.width/2, cy:r.y+r.height/2});
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
                    "type": ev, "x": cx, "y": cy, "button": "left", "clickCount": 1 if ev == "mousePressed" else 0}}))
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


def wait_step(target_step, timeout=20):
    """Wartet bis der Wizard bei target_step (z.B. '1/4' oder '2/4') ist."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            s = c.eval_tab("sell", r"""
(function(){
  var st=(document.body.innerText||'').match(/\\d\\/4/);
  return st?st[0]:'';
})()""", timeout=8)
            if s == target_step:
                return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def fill_step1(name, desc):
    set_select(0, "skill")
    set_select(1, "chatgpt skill")
    set_select(2, "2.99")
    c.eval_tab("sell", r"""
(function(){
  function reactSet(el,v){var d=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value');var n=d?d.set:Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype,'value').set;n.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));if(el._valueTracker)el._valueTracker.setValue('');}
  var ins=[...document.querySelectorAll('input[type=text],textarea')].filter(e=>e.placeholder||e.tagName==='TEXTAREA');
  if(ins[0])reactSet(ins[0],%r);
  if(ins[1])reactSet(ins[1],%r);
})""" % (name, desc))
    time.sleep(3)
    ws = ws_of()
    if not ws:
        return "NO_WS"
    box = get_box(ws, "Next: Skill File")
    if box and "cx" in box:
        b = json.loads(box)
        mouse_click(ws, b["cx"], b["cy"])
        return "CLICKED Next: Skill File"
    return "NO_BTN:Next: Skill File"


def fill_step2(skill):
    sk_json = json.dumps({
        "name": skill["name"], "when": skill["when"], "overview": skill["overview"],
        "tools": skill["tools"],
        "example1_prompt": skill["example1_prompt"], "example1_response": skill["example1_response"],
        "example2_prompt": skill["example2_prompt"], "example2_response": skill["example2_response"],
        "setup": skill["setup"], "model": skill["model"],
    })
    res = c.eval_tab("sell", """
(function(sk){
  function setEl(el,val){
    var proto=Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype,'value').set;
    proto.call(el,val);
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  }
  function setSel(selIdx,txt){
    var s=document.querySelectorAll('select')[selIdx];
    if(!s) return 'NO_SELECT:'+selIdx;
    txt=(txt||'').toLowerCase().trim();
    for(var j=0;j<s.options.length;j++){
      var ot=(s.options[j].text||'').toLowerCase().trim();
      var ov=(s.options[j].value||'').toLowerCase().trim();
      if(ot===txt||ov===txt||ot.indexOf(txt)>=0||ov.indexOf(txt)>=0){
        var p=Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype,'value').set;
        p.call(s,s.options[j].value);
        s.dispatchEvent(new Event('change',{bubbles:true}));
        return 'SEL='+s.value;
      }
    }
    return 'OPT_NOT_FOUND:'+selIdx;
  }
  var els=[...document.querySelectorAll('input[type=text],textarea')].filter(e=>e.placeholder||e.tagName==='TEXTAREA');
  if(els.length<9) return 'TOO_FEW_INPUTS:'+els.length;
  setEl(els[0], sk.name);
  setEl(els[1], sk.when);
  setEl(els[2], sk.overview);
  setEl(els[3], sk.tools);
  setEl(els[4], sk.example1_prompt);
  setEl(els[5], sk.example1_response);
  setEl(els[6], sk.example2_prompt);
  setEl(els[7], sk.example2_response);
  setEl(els[8], sk.setup);
  var selRes = setSel(0, sk.model);
  return 'OK fields='+els.length+' name='+els[0].value.slice(0,20)+' | '+selRes;
})(%s)
""" % sk_json)
    return res


def main():
    for idx in PUBLISH_IDX:
        sk = P.SKILLS[idx]
        # frischer sell-tab
        c.navigate_tab("sell", "https://promptbase.com/sell")
        time.sleep(4)
        if not wait_step("1/4", timeout=10):
            print(f"Skill {idx}: nicht bei Step 1 - uebersprungen")
            continue
        print(f"\n=== Skill {idx}: {sk['name']} ===")
        r1 = fill_step1(sk["title"][:40], sk["overview"][:120])
        print("  Step1:", r1)
        if not wait_step("2/4", timeout=15):
            print("  Step2 nicht erreicht - Validierung?")
            continue
        r2 = fill_step2(sk)
        print("  Step2:", r2)
        errs = P.validate_form()
        bad = [e for e in errs if any(k in e.lower() for k in ("example","buyer","please","provide"))]
        print("  Form-errors:", bad if bad else "NONE")
        print("  >>> STOP vor Publish")

    print("\nDONE: 2 Skills bis vor Publish. Payout/Step3 ggf. manuell.")


if __name__ == "__main__":
    main()
