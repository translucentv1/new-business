"""Post on r/Finanzen via CDP, using hy3's proven cdp_helper module.

Strategy:
1. Navigate to reddit.com/r/Finanzen/submit
2. Dump actual form structure (what's the real title field?) - skip assumption
3. If Title field is contenteditable div (not input): handle div correctly
4. Fill Title + Body via native React setter
5. NOT auto-click Post - allow user gate so we comply with irreversible-action rule
"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp_helper as c

POST_TITLE = (
    "Kleines 3-Topf-System, mit dem ich seit einem halben Jahr zum ersten Mal "
    "weiss, wohin mein Geld geht (kostenlos nachbaubar)"
)
POST_BODY = (
    "Ich habe Jahre lang versucht, ein perfektes Budgeting-Setup hinzubekommen "
    "und immer wieder aufgegeben, weil es zu kompliziert wurde. Was haengen "
    "geblieben ist, ist dumm einfach:\n\n"
    "1. **Drei Toepfe:** Fixkosten / Flex (Lebensmittel, Freizeit) / Sparen. "
    "Alles ausser Fix landet erst mal im Flex-Topf.\n"
    "2. **Woechentlicher 10-Min-Check** statt monatlich. Sonntagabend: "
    "Flex-Topf sichten, uebriggebliebenes zur Haelfte in Sparen. Mehr braucht "
    "es bei mir nicht.\n"
    "3. **Ein einziges Sheet/Notion** als \"externes Gehirn\" - nicht fuer "
    "Motivation, sondern damit ich nicht im Kopf rechnen muss.\n\n"
    "Das Prinzip oben reicht voellig, kein Tool noetig. Falls jemand das fertig "
    "strukturierte Template (Notion + Google-Sheets, mit deutscher Kategorien-"
    "Logik und Monats-/Jahres-Auswertung) statt selbstbauen will: Ich habe "
    "eins aufbereitet - Link in den Kommentaren. Ist kein Muss."
)


def explore_submit():
    """Find every editable field on the submit page."""
    return c.eval_tab("finanzen/submit", r"""
    (function(){
      const result = {inputs: [], textareas: [], cedit: [], rt: []};
      function desc(el, tag) {
        try {
          return {
            tag: tag || el.tagName,
            role: el.getAttribute('role'),
            ce: el.getAttribute('contenteditable'),
            ph: el.placeholder || el.getAttribute('aria-label') || '',
            label: el.getAttribute('label') || '',
            value: (el.value || el.innerText || '').slice(0, 80),
            cls: (el.className || '').toString().slice(0, 80)
          };
        } catch(e) { return {err: e.message}; }
      }
      // include hidden too, but flag them
      document.querySelectorAll('input').forEach((el, i) => {
        if (el.offsetParent !== null) result.inputs.push({i, ...desc(el)});
      });
      document.querySelectorAll('textarea').forEach((el, i) => {
        if (el.offsetParent !== null) result.textareas.push({i, ...desc(el)});
      });
      document.querySelectorAll('[contenteditable=true]').forEach((el, i) => {
        if (el.offsetParent !== null) result.cedit.push({i, ...desc(el)});
      });
      document.querySelectorAll('[role=textbox]').forEach((el, i) => {
        if (el.offsetParent !== null) result.rt.push({i, ...desc(el)});
      });
      return JSON.stringify(result);
    })()
    """)


def set_ce_div(text, idx_cedit_field):
    """Set a contenteditable=true div to text via native input event."""
    js = r"""
    (function(text, idx){
      const divs = [...document.querySelectorAll('[contenteditable=true]')]
        .filter(e => e.offsetParent !== null);
      const el = divs[idx];
      if (!el) return 'NO_CE_DIV:'+idx+'of'+divs.length;
      el.focus();
      // Clear existing content
      el.innerText = text;
      // Dispatch React-compatible input event
      const evt = new InputEvent('input', {bubbles: true, data: text, inputType: 'insertText'});
      el.dispatchEvent(evt);
      el.dispatchEvent(new Event('change', {bubbles: true}));
      // Some SPAs need a keyup/keydown too
      el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: ' '}));
      return 'SET:'+el.innerText.length;
    })(%r, %d)
    """ % (repr(text), idx_cedit_field)
    return c.eval_tab("finanzen/submit", js)


def main_logic():
    print("=== Navigating to reddit submit ===")
    c.navigate_tab("finanzen", "https://www.reddit.com/r/Finanzen/submit")
    time.sleep(5)
    print("=== Exploring form structure ===")
    raw = explore_submit()
    if not raw:
        print("ERR: empty explore")
        return
    try:
        data = json.loads(raw)
        print(json.dumps(data, indent=2)[:3000])
    except Exception as e:
        print(f"ERR parsing: {e}")
        print(str(raw)[:800])
        return
    print()
    # Determine which fields to fill
    inputs = data.get("inputs", [])
    cedit = data.get("cedit", [])
    rt = data.get("rt", [])
    # Reddit new submit form: title is an <input>, body is contenteditable div OR textarea
    title_input_idx = None
    for el in inputs:
        ph = (el.get("ph") or "").lower()
        if "titel" in ph or "title" in ph:
            title_input_idx = el.get("i")
            break
    body_ce_idx = None
    for el in cedit:
        ph = (el.get("ph") or "").lower()
        if "text" in ph or "beitragstext" in ph or "body" in ph:
            body_ce_idx = el.get("i")
            break
    if body_ce_idx is None and cedit:
        body_ce_idx = 0
    print(f"title_input_idx={title_input_idx}, body_ce_idx={body_ce_idx}")
    # Fill title
    if title_input_idx is not None:
        js_set_input = r"""
        (function(text, idx){
          const el = document.querySelectorAll('input')[idx];
          if (!el) return 'NO_INPUT:'+idx;
          const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
          s.call(el, text);
          el.dispatchEvent(new Event('input', {bubbles: true}));
          el.dispatchEvent(new Event('change', {bubbles: true}));
          el.dispatchEvent(new Event('blur', {bubbles: true}));
          return 'TITLE:'+el.value.length;
        })(%r, %d)
        """ % (repr(POST_TITLE), title_input_idx)
        r = c.eval_tab("finanzen/submit", js_set_input)
        print(f"Title fill: {r}")
    else:
        print("WARN: no title input found by placeholder. Try cedit 0?")
    # Fill body
    if body_ce_idx is not None:
        r = set_ce_div(POST_BODY, body_ce_idx)
        print(f"Body fill: {r}")
    else:
        print("WARN: no body contenteditable found")
    # Re-explore after fill
    time.sleep(2)
    print("=== State after fill ===")
    raw2 = explore_submit()
    try:
        data2 = json.loads(raw2)
        print(json.dumps({
            "inputs": [(el["i"], (el["value"] or "")[:60], el["ph"]) for el in data2.get("inputs",[])],
            "cedit": [(el["i"], (el["value"] or "")[:60]) for el in data2.get("cedit",[])]
        })[:1500])
    except Exception:
        print(str(raw2)[:500])
    print()
    print("=== STOP - not auto-clicking Post ===")


main_logic()
