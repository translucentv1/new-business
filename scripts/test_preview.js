// test_preview.js — extrahiert das <script> aus gig.html, stubbt das DOM und
// ruft preview() mit echten Eingaben auf. Beweist, dass die Sofort-Vorschau
// ohne Server funktioniert (GitHub Pages ist statisch).
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('gig.html', 'utf8');
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('FAIL: kein <script> gefunden'); process.exit(1); }

const fields = { req: '', tier: '3.99', out: '' };
const sandbox = {
  document: {
    getElementById(id) {
      return {
        get value() { return fields[id]; },
        set value(v) { fields[id] = v; },
        get textContent() { return fields.out; },
        set textContent(v) { fields.out = v; },
      };
    },
  },
  window: { open() {} },
  console,
};
vm.createContext(sandbox);
vm.runInContext(m[1], sandbox);

// Netzwerk bewusst NICHT bereitgestellt: faellt der Code auf fetch zurueck,
// wirft er ReferenceError -> Test schlaegt fehl. Genau das wollen wir pruefen.
const cases = [
  ['Ich brauche eine PowerPoint Praesentation ueber Nachhaltigkeit fuer den Vorstand', '14.99'],
  ['Businessplan fuer ein kleines Cafe in Leipzig, fuer die Bank', '7.99'],
  ['Ein Python Skript das eine CSV in JSON umwandelt', '3.99'],
  ['Bewerbung als Data Analyst bei einer Versicherung', '7.99'],
  ['irgendwas', '3.99'],
  ['', '3.99'],
];

let fails = 0;
for (const [req, tier] of cases) {
  fields.req = req; fields.tier = tier; fields.out = '';
  try {
    sandbox.preview();
  } catch (e) {
    console.log(`FAIL (throw) req=${JSON.stringify(req)}: ${e}`);
    fails++; continue;
  }
  const out = fields.out;
  const label = req === '' ? '(leer)' : req.slice(0, 45);
  if (req === '') {
    const ok = out.includes('Bitte beschreibe');
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${label} -> ${out}`);
    if (!ok) fails++;
    continue;
  }
  const ok = out.includes('SOFORT-VORSCHAU') && out.includes('Erkannter Auftragstyp')
    && out.includes('Gliederung') && out.length > 200;
  if (!ok) fails++;
  const typ = (out.match(/Erkannter Auftragstyp: (.*)/) || [])[1];
  const pak = (out.match(/Paket: (.*)/) || [])[1];
  console.log(`${ok ? 'OK  ' : 'FAIL'} ${label.padEnd(46)} | ${typ} | ${pak} | ${out.length} Zeichen`);
}

console.log('\n--- VOLLE AUSGABE (PowerPoint / Premium) ---');
fields.req = 'Ich brauche eine PowerPoint Praesentation ueber Nachhaltigkeit fuer den Vorstand';
fields.tier = '14.99'; fields.out = '';
sandbox.preview();
console.log(fields.out);

console.log(`\nERGEBNIS: ${fails === 0 ? 'ALLE TESTS GRUEN' : fails + ' FEHLER'}`);
process.exit(fails === 0 ? 0 : 1);
