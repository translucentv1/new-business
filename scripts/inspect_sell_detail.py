"""Dump exact select options + input placeholders of /sell form (read-only)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_helper as c

time.sleep(2)
data = c.eval_tab('sell', '''
(function(){
  var sels=[...document.querySelectorAll('select')].map(function(s){
    return {val:s.value, opts:[...s.options].map(o=>o.text.trim())};
  });
  var ins=[...document.querySelectorAll('input,textarea')].map(function(e){
    return {tag:e.tagName, type:e.type, ph:(e.placeholder||''), val:e.value.slice(0,20)};
  });
  return JSON.stringify({selects:sels, inputs:ins}, null, 1);
})()
''')
print(data)
