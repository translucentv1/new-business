"""Deeper inspection of Reddit submit page - title field in shadow DOM, iframe, etc."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_helper as c

expr = r"""
(function(){
  // inspect all elements with "titel" or "title" in any attribute
  const matches = [];
  const all = document.querySelectorAll('*');
  for (let i = 0; i < all.length; i++) {
    const el = all[i];
    const attrs = [...el.attributes].map(a => (a.value||'').toLowerCase()).join(' ');
    const text = (el.innerText || '').slice(0, 60);
    if (/titel|title/i.test(attrs) || /^titel/i.test(text) || /^title/i.test(text)) {
      if (el.offsetParent !== null) {
        matches.push({
          tag: el.tagName,
          role: el.getAttribute('role'),
          cls: (el.className||'').toString().slice(0,60),
          ph: el.placeholder || '',
          aria: el.getAttribute('aria-label') || '',
          val: (el.value || el.innerText || '').slice(0,60),
          hidden: el.hidden,
          type: el.type || el.getAttribute('type') || ''
        });
      }
    }
  }
  return JSON.stringify({
    matchCount: matches.length,
    matches: matches.slice(0, 10),
    placeholderElements: [...document.querySelectorAll('[placeholder]')]
      .filter(e=>e.offsetParent!==null)
      .map(e=>({tag:e.tagName, ph:e.placeholder, val:(e.value||'').slice(0,40)})),
    iframes: [...document.querySelectorAll('iframe')].map(f=>f.src||''),
    shadowRoots: [...document.querySelectorAll('*')]
      .filter(e=>e.shadowRoot)
      .map(e=>({tag:e.tagName, cls:(e.className||'').toString().slice(0,60)}))
      .slice(0, 5)
  });
})()
"""
print("=== Reddit submit deep inspection ===")
# Add: inspect custom web components in depth
expr2 = r"""
(function(){
  const title = document.querySelector('post-composer-title');
  if (!title) return JSON.stringify({err:'NO_TITLE_COMPONENT'});
  const shadow = title.shadowRoot;
  let inner = null;
  if (shadow) {
    const input = shadow.querySelector('input, textarea, [contenteditable]');
    if (input) {
      inner = {
        tag: input.tagName,
        ph: input.placeholder || '',
        aria: input.getAttribute('aria-label') || '',
        val: (input.value || input.innerText || '').slice(0, 80),
        ce: input.getAttribute('contenteditable'),
        inShadow: true
      };
    }
  }
  // check if title has child input/light DOM
  const lightInputs = [...title.querySelectorAll('input,textarea')].map(e=>({
    tag:e.tagName, ph:e.placeholder||'',val:(e.value||'').slice(0,40)
  }));
  return JSON.stringify({
    titleTag: title.tagName,
    hasShadow: !!shadow,
    shadowChildCount: shadow ? shadow.childNodes.length : 0,
    innerInput: inner,
    lightInputs,
    titleOuterHTML: title.outerHTML.slice(0, 400),
    titleInnerText: (title.innerText || '').slice(0, 200)
  });
})()
"""
print("=== Title component detail ===")
r2 = c.eval_tab("finanzen/submit", expr2)
print(r2)
r = c.eval_tab("finanzen/submit", expr)
print("=== Full deep inspection ===")
print(r)
