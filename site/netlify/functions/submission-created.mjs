// Netlify invokes this for EVERY Netlify Forms submission (event-triggered by
// its reserved name). Thin wrapper around triage core.
//
// IRON RULE: notifies the operator only. Sends nothing to leads or anyone
// external. Off switch: OPS_TRIAGE_ENABLED=false (leads still dead-lettered).

import { agentEnabled } from './lib/env.mjs';
import { leadStore, deadLetter } from './lib/lead-store.mjs';
import { runTriage } from './lib/triage-core.mjs';

export default async (req) => {
  const body = await req.json();
  const store = leadStore();

  if (!agentEnabled('OPS_TRIAGE_ENABLED')) {
    await deadLetter(store, body, 'triage disabled (OPS_TRIAGE_ENABLED=false)');
    return new Response('triage disabled; payload logged', { status: 200 });
  }

  const result = await runTriage(body, { store });
  return Response.json(result);
};
