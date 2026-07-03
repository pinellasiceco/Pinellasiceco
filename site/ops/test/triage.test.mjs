import test from 'node:test';
import assert from 'node:assert/strict';
import { runTriage, extractFields, formatEmail } from '../../netlify/functions/lib/triage-core.mjs';

process.env.ANTHROPIC_API_KEY = 'test-key';

function fakeStore() {
  const data = new Map();
  return {
    data,
    async setJSON(k, v) { data.set(k, v); },
    async get(k) { return data.get(k) ?? null; },
  };
}

function fakeClaude(json) {
  return async (url) => {
    if (url.includes('anthropic')) {
      return { ok: true, json: async () => ({ content: [{ text: JSON.stringify(json) }] }) };
    }
    throw new Error(`unexpected fetch ${url}`);
  };
}

const submission = (data) => ({ payload: { form_name: 'lead-capture', data } });

test('extractFields strips honeypot and form-name', () => {
  const { form, fields, segment } = extractFields(submission({
    'bot-field': '', 'form-name': 'lead-capture', segment: 'repair', name: 'Sam', urgency: 'Emergency — machine is down now',
  }));
  assert.equal(form, 'lead-capture');
  assert.equal(segment, 'repair');
  assert.ok(!('bot-field' in fields));
  assert.ok(!('form-name' in fields));
});

test('HOT repair lead: saved + operator notified with tiered subject', async () => {
  const store = fakeStore();
  const sent = [];
  const result = await runTriage(submission({
    segment: 'repair', page: 'ice-machine-repair', name: 'Sam', business: 'Crabby Sam\'s',
    phone: '727-555-0000', city: 'Clearwater', urgency: 'Emergency — machine is down now',
  }), {
    store,
    notify: async (email) => { sent.push(email); return { sent: true }; },
    fetchImpl: fakeClaude({
      tier: 'HOT', segment: 'repair-urgent',
      reasoning: 'machine down at a restaurant', headline: 'repair-urgent, restaurant, Clearwater',
      suggested_action: 'call back within the hour',
    }),
  });
  assert.equal(result.action, 'triaged');
  assert.equal(result.tier, 'HOT');
  assert.equal(sent.length, 1);
  assert.match(sent[0].subject, /HOT — repair-urgent, restaurant, Clearwater/);
  const saved = store.data.get(result.id);
  assert.equal(saved.segment, 'repair');
  assert.equal(saved.triage.segment, 'repair-urgent');
});

test('JUNK: logged, NOT notified', async () => {
  const store = fakeStore();
  const sent = [];
  const result = await runTriage(submission({ segment: 'general', name: 'xxx', message: 'buy backlinks' }), {
    store,
    notify: async (e) => { sent.push(e); },
    fetchImpl: fakeClaude({ tier: 'JUNK', segment: 'unknown', reasoning: 'spam', headline: 'spam', suggested_action: 'ignore' }),
  });
  assert.equal(result.action, 'logged-junk');
  assert.equal(sent.length, 0);
  assert.equal(store.data.get(result.id).tier_assigned, 'JUNK');
});

test('fail-safe: triage error still saves lead and notifies raw payload', async () => {
  const store = fakeStore();
  const sent = [];
  const result = await runTriage(submission({ segment: 'sales', name: 'Pat', phone: '813-555-1111' }), {
    store,
    notify: async (e) => { sent.push(e); },
    fetchImpl: async () => ({ ok: false, status: 500 }),
  });
  assert.equal(result.action, 'failed-safe');
  assert.equal(sent.length, 1);
  assert.match(sent[0].subject, /TRIAGE FAILED/);
  assert.ok(store.data.get(result.id), 'lead persisted despite triage failure');
});

test('unknown form: logged + flagged, never guessed', async () => {
  const store = fakeStore();
  const sent = [];
  const result = await runTriage({ payload: { form_name: 'mystery-form', data: { a: 1 } } }, {
    store,
    notify: async (e) => { sent.push(e); },
    fetchImpl: async () => { throw new Error('should not call claude'); },
  });
  assert.equal(result.action, 'logged-unknown');
  assert.match(sent[0].subject, /Unrecognized form/);
});

test('formatEmail escapes HTML in fields', () => {
  const { html } = formatEmail({
    id: 'x', form: 'lead-capture',
    fields: { message: '<script>alert(1)</script>' },
    triage: { tier: 'WARM', segment: 'cleaning', reasoning: 'r', headline: 'h', suggested_action: 's' },
  });
  assert.ok(!html.includes('<script>alert'));
  assert.ok(html.includes('&lt;script&gt;'));
});
