const CDP_PORT = 9223;
const CDP_BASE = `http://127.0.0.1:${CDP_PORT}`;

async function getTabs() {
  const res = await fetch(`${CDP_BASE}/json`);
  return await res.json();
}

async function findTab(keyword) {
  const tabs = await getTabs();
  return tabs.find(t => t.type === 'page' && t.url && t.url.toLowerCase().includes(keyword.toLowerCase()));
}

async function wsSend(wsUrl, payload, timeout = 15000) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const id = Math.floor(Math.random() * 1e6);
    const timer = setTimeout(() => {
      ws.close();
      reject(new Error(`WS timeout id=${id}`));
    }, timeout);

    ws.onopen = () => {
      ws.send(JSON.stringify({ ...payload, id }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id === id) {
        clearTimeout(timer);
        ws.close();
        resolve(msg);
      }
    };

    ws.onerror = (err) => {
      clearTimeout(timer);
      reject(err);
    };
  });
}

async function bringToFront(wsUrl) {
  return wsSend(wsUrl, { method: 'Page.bringToFront', params: {} });
}

async function evalExpr(wsUrl, expr, timeout = 15000) {
  await bringToFront(wsUrl);
  return wsSend(wsUrl, {
    method: 'Runtime.evaluate',
    params: { expression: expr, returnByValue: true, awaitPromise: true }
  }, timeout);
}

async function navigateTab(wsUrl, url) {
  await bringToFront(wsUrl);
  return wsSend(wsUrl, {
    method: 'Page.navigate',
    params: { url }
  }, 20000);
}

async function clickElement(wsUrl, selector) {
  await bringToFront(wsUrl);
  const expr = `
    (function(sel) {
      const el = document.querySelector(sel);
      if (!el) return 'NOT_FOUND:' + sel;
      el.click();
      return 'CLICKED:' + sel;
    })('${selector}')
  `;
  return evalExpr(wsUrl, expr);
}

async function setInputValue(wsUrl, selector, value) {
  await bringToFront(wsUrl);
  const expr = `
    (function(sel, val) {
      const el = document.querySelector(sel);
      if (!el) return 'NOT_FOUND:' + sel;
      const proto = el.tagName==='SELECT' ? HTMLSelectElement.prototype
        : el.tagName==='TEXTAREA' ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
      setter.call(el, val);
      el.dispatchEvent(new Event('input', {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
      el.dispatchEvent(new Event('blur', {bubbles:true}));
      return 'SET:' + el.value;
    })('${selector}', ${JSON.stringify(value)})
  `;
  return evalExpr(wsUrl, expr);
}

async function getPageText(wsUrl) {
  await bringToFront(wsUrl);
  return evalExpr(wsUrl, `document.body.innerText.slice(0, 5000)`);
}

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('=== CDP Reddit Poster ===');
  
  // Get browser websocket
  const verRes = await fetch(`${CDP_BASE}/json/version`);
  const ver = await verRes.json();
  const browserWs = ver.webSocketDebuggerUrl;
  console.log('Browser WS:', browserWs);

  // Create a new tab for Reddit
  const createRes = await wsSend(browserWs, {
    method: 'Target.createTarget',
    params: { url: 'https://www.reddit.com/r/Finanzen' }
  });
  console.log('Create tab:', createRes);

  if (createRes.error) {
    console.error('Create tab error:', createRes.error);
    return;
  }

  const targetId = createRes.result.targetId;
  console.log('Target ID:', targetId);

  // Wait for tab to load
  await wait(5000);

  // Find the new tab
  let tab = null;
  for (let i = 0; i < 10; i++) {
    const tabs = await getTabs();
    tab = tabs.find(t => t.type === 'page' && t.id === targetId);
    if (tab && tab.url && tab.url.includes('reddit')) break;
    await wait(1000);
  }

  if (!tab) {
    console.error('Tab not found');
    return;
  }

  console.log('Tab found:', tab.url, tab.webSocketDebuggerUrl);

  // Get page text to see where we are
  const text = await getPageText(tab.webSocketDebuggerUrl);
  console.log('Page text (first 2000):', text.slice(0, 2000));

  // Check if logged in
  if (text.includes('Log In') || text.includes('Anmelden')) {
    console.log('NOT LOGGED IN - need user to log in first');
  } else {
    console.log('Logged in!');
  }
}

main().catch(console.error);