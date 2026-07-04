// Post-revamp form contract test: the BUILT repair page's form must carry
// the Netlify attributes, honeypot, segmentation fields, and field names the
// triage pipeline expects — and a submission assembled from those exact
// fields must flow through runTriage.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { runTriage } from '../../netlify/functions/lib/triage-core.mjs';

process.env.ANTHROPIC_API_KEY = 'test-key';

const html = readFileSync(
  new URL('../../dist/ice-machine-repair/index.html', import.meta.url), 'utf8');
const formMatch = html.match(/<form[^>]*name="lead-capture"[\s\S]*?<\/form>/);

test('built repair form keeps Netlify contract', () => {
  assert.ok(formMatch, 'lead-capture form present in built HTML');
  const form = formMatch[0];
  assert.match(form, /data-netlify="true"/);
  assert.match(form, /data-netlify-honeypot="bot-field"/);
  assert.match(form, /name="bot-field"/);
  assert.match(form, /name="form-name" value="lead-capture"/);
  assert.match(form, /name="segment" value="repair"/);
  assert.match(form, /name="page" value="ice-machine-repair"/);
  assert.match(form, /name="urgency"/);
  assert.match(form, /Machine is down now/);
  for (const f of ['name', 'phone', 'business', 'email', 'city', 'message']) {
    assert.match(form, new RegExp(`name="${f}"`), `field ${f} present`);
  }
});

test('submission built from the real form fields flows through triage', async () => {
  const names = [...formMatch[0].matchAll(/name="([^"]+)"/g)].map((m) => m[1]);
  const data = {};
  for (const n of names) data[n] = '';
  Object.assign(data, {
    'form-name': 'lead-capture', segment: 'repair', page: 'ice-machine-repair',
    name: 'Test Owner', phone: '727-555-9999', urgency: 'Machine is down now',
    message: 'Hoshizaki KM-500, no ice since last night',
  });
  const store = new Map();
  const sent = [];
  const result = await runTriage({ payload: { form_name: 'lead-capture', data } }, {
    store: { setJSON: async (k, v) => store.set(k, v), get: async (k) => store.get(k) },
    notify: async (e) => { sent.push(e); return { sent: true }; },
    fetchImpl: async () => ({
      ok: true,
      json: async () => ({ content: [{ text: JSON.stringify({ tier: 'HOT', segment: 'repair-urgent', reasoning: 'down machine', headline: 'repair-urgent, restaurant, test', suggested_action: 'call now' }) }] }),
    }),
  });
  assert.equal(result.action, 'triaged');
  assert.equal(result.tier, 'HOT');
  assert.equal(sent.length, 1);
  const saved = [...store.values()][0];
  assert.equal(saved.fields.urgency, 'Machine is down now');
  assert.ok(!('bot-field' in saved.fields), 'honeypot stripped');
});
