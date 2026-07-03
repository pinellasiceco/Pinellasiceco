// Core triage logic — pure functions + injectable I/O (ported from the GRC
// pattern, simplified to sensor scope: classify, tier, notify operator, log.
// NO auto-replies to leads, NO routing, NO payments.
//
// Fail-safe contract: any error → operator notified with the raw payload AND
// the raw payload dead-lettered. A lead never vanishes.

import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { env, ANTHROPIC_MODEL } from './env.mjs';
import { notifyOperator } from './notify.mjs';
import { newLeadRecord, saveLead, deadLetter } from './lead-store.mjs';

// The one lead form (segment travels as a hidden field).
export const TRIAGED_FORMS = new Set(['lead-capture']);

export function extractFields(submission) {
  // Netlify submission-created payload: { payload: { form_name, data, ... } }
  const p = submission?.payload || {};
  const data = { ...(p.data || {}) };
  delete data['bot-field'];
  delete data['form-name'];
  return {
    form: p.form_name || data.form_name || 'unknown',
    fields: data,
    segment: data.segment || null,
    page: data.page || null,
  };
}

export async function loadPrompt(name) {
  const candidates = [
    join(process.cwd(), 'ops', 'prompts', name),
    join('/var/task', 'ops', 'prompts', name),
    fileURLToPath(new URL(`../../../ops/prompts/${name}`, import.meta.url)),
  ];
  let lastErr;
  for (const p of candidates) {
    try { return await readFile(p, 'utf8'); } catch (e) { lastErr = e; }
  }
  throw lastErr;
}

export async function claudeTriage({ form, fields, segment, page }, fetchImpl = fetch) {
  const key = env('ANTHROPIC_API_KEY');
  if (!key) throw new Error('ANTHROPIC_API_KEY unset');
  const prompt = await loadPrompt('triage.md');
  const user = [
    `Form: ${form}`,
    segment ? `Form-declared segment: ${segment}` : null,
    page ? `Submitted from page: ${page}` : null,
    `Raw fields:\n${JSON.stringify(fields, null, 2)}`,
  ].filter(Boolean).join('\n\n');

  const res = await fetchImpl('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: ANTHROPIC_MODEL(),
      max_tokens: 400,
      temperature: 0.2,
      system: prompt,
      messages: [{ role: 'user', content: user }],
    }),
  });
  if (!res.ok) throw new Error(`anthropic http ${res.status}`);
  const data = await res.json();
  const text = (data.content || []).map(b => b.text || '').join('');
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) throw new Error('no JSON in triage response');
  const parsed = JSON.parse(match[0]);
  if (!['HOT', 'WARM', 'LOW', 'JUNK'].includes(parsed.tier)) throw new Error(`bad tier ${parsed.tier}`);
  const SEGMENTS = ['repair-urgent', 'repair-routine', 'sales', 'lease', 'cleaning', 'unknown'];
  if (!SEGMENTS.includes(parsed.segment)) parsed.segment = 'unknown';
  return parsed;
}

const TIER_EMOJI = { HOT: '🧊🔥', WARM: '🧊', LOW: '·', JUNK: '🗑' };

export function formatEmail({ id, form, fields, triage }) {
  // Subject-line tiered: "🧊🔥 HOT — repair-urgent, restaurant, Clearwater"
  const subject = `${TIER_EMOJI[triage.tier]} ${triage.tier} — ${triage.headline}`;
  const text = [
    `Tier: ${triage.tier}`,
    `Segment: ${triage.segment}`,
    `Why: ${triage.reasoning}`,
    `Suggested action: ${triage.suggested_action}`,
    '',
    `Lead id: ${id}`,
    `Form: ${form}`,
    '',
    'Raw fields:',
    ...Object.entries(fields).map(([k, v]) => `  ${k}: ${v}`),
  ].join('\n');
  const html = `<div style="font-family:system-ui,sans-serif;max-width:640px">
    <h2 style="color:#16294E;margin-bottom:4px">${triage.tier} — ${escapeHtml(triage.headline)}</h2>
    <p style="color:#46536C"><strong>Segment:</strong> ${escapeHtml(triage.segment)}<br>
    <strong>Why:</strong> ${escapeHtml(triage.reasoning)}<br>
    <strong>Suggested action:</strong> ${escapeHtml(triage.suggested_action)}</p>
    <table style="border-collapse:collapse;font-size:14px">${Object.entries(fields)
      .map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;color:#6E7A92">${escapeHtml(k)}</td><td style="padding:4px 0"><strong>${escapeHtml(String(v))}</strong></td></tr>`)
      .join('')}</table>
    <p style="color:#9aa5b5;font-size:12px">Lead ${escapeHtml(id)} · form ${escapeHtml(form)}</p>
  </div>`;
  return { subject, text, html };
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function leadId(form) {
  const d = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  return `${d}-${form}-${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Main entry. deps: { store, fetchImpl, notify } injectable for tests.
 */
export async function runTriage(submission, deps = {}) {
  const store = deps.store;
  const notify = deps.notify || notifyOperator;
  const fetchImpl = deps.fetchImpl || fetch;

  const { form, fields, segment, page } = extractFields(submission);
  const id = leadId(form);

  if (!TRIAGED_FORMS.has(form)) {
    // Unknown form: log it and tell the operator rather than guessing.
    await saveLead(store, newLeadRecord({ id, form, fields, segment }));
    await notify({ subject: `⚠️ Unrecognized form submission (${form}) — logged`, text: JSON.stringify(fields, null, 2) }, fetchImpl);
    return { id, action: 'logged-unknown' };
  }

  try {
    const triage = await claudeTriage({ form, fields, segment, page }, fetchImpl);
    const lead = newLeadRecord({ id, form, fields, segment, tier: triage.tier, triage });
    await saveLead(store, lead);

    if (triage.tier === 'JUNK') {
      // Logged, not notified — the log is the record; junk never pages anyone.
      return { id, action: 'logged-junk' };
    }

    await notify(formatEmail({ id, form, fields, triage }), fetchImpl);
    return { id, action: 'triaged', tier: triage.tier };
  } catch (err) {
    // FAIL SAFE: raw payload to operator + dead letter. Never swallow a lead.
    const raw = JSON.stringify({ form, segment, page, fields }, null, 2);
    await saveLead(store, newLeadRecord({ id, form, fields, segment })).catch(async () => {
      await deadLetter(store, { form, fields }, `save-failed after: ${err.message}`).catch(() => {});
    });
    await notify({
      subject: `⚠️ TRIAGE FAILED — raw lead attached (${form})`,
      text: `Triage error: ${err.message}\n\nLead id: ${id}\n\nRaw submission:\n${raw}`,
    }, fetchImpl);
    return { id, action: 'failed-safe', error: err.message };
  }
}
