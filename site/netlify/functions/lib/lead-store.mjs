// Durable lead log on Netlify Blobs — JSON-lines semantics inside each
// record (events array). Store name "pic-leads": this is Pinellas Ice Co's
// namespace, fully separate from any other business's lead store. This site
// deploys as its own Netlify site, so blobs are isolated at the site level
// too — zero data mingling by construction.

import { getStore } from '@netlify/blobs';

export const SCHEMA_VERSION = 1;

export function leadStore(opts = {}) {
  return getStore({ name: 'pic-leads', consistency: 'strong', ...opts });
}

export function newLeadRecord({ id, form, fields, segment, tier, triage }) {
  const now = new Date().toISOString();
  return {
    schema_version: SCHEMA_VERSION,
    id,
    created_at: now,
    form,
    segment: segment || null, // repair|sales|lease|cleaning|general (form-declared)
    status: 'new',
    fields,
    tier_assigned: tier || null,
    triage: triage || null, // triage.segment may refine the form-declared one
    events: [{ at: now, type: 'created', form }],
  };
}

export async function saveLead(store, record) {
  await store.setJSON(record.id, record);
  return record;
}

export async function deadLetter(store, payload, reason) {
  const key = `deadletter/${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  await store.setJSON(key, { schema_version: SCHEMA_VERSION, reason, payload, at: new Date().toISOString() });
  return key;
}
