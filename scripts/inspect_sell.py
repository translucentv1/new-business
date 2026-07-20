"""Inspect the live /sell form DOM (read-only). Run: python scripts/inspect_sell.py"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_helper as c

time.sleep(2)
dom = c.eval_tab('sell', '''
(function(){
  var out=[];
  document.querySelectorAll('input,select,textarea').forEach(function(e){
    out.push(e.tagName+'#'+e.id+'@'+e.name+'['+e.type+'] ph='+((e.placeholder||'').slice(0,30)));
  });
  var btns=[];
  document.querySelectorAll('button').forEach(function(b){ if(b.innerText.trim()) btns.push('BTN:'+b.innerText.trim().slice(0,25)); });
  return out.join('\\n')+'\\n---BUTTONS---\\n'+btns.join(' | ');
})()
''')
print(dom)
