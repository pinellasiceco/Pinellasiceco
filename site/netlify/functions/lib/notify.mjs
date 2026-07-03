// Operator notification transport. IRON RULE: sends ONLY to OPERATOR_EMAIL.
// No parameter for arbitrary recipients on purpose — this system never
// emails a lead. Transport: Resend.

import { env, OPERATOR_EMAIL, NOTIFY_FROM } from './env.mjs';

export async function notifyOperator({ subject, text, html }, fetchImpl = fetch) {
  const to = OPERATOR_EMAIL();
  const key = env('RESEND_API_KEY');
  if (!to || !key) {
    console.error('[notify] OPERATOR_EMAIL or RESEND_API_KEY unset — notification not sent:', subject);
    return { sent: false, reason: 'missing-config' };
  }
  const res = await fetchImpl('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: NOTIFY_FROM(), to: [to], subject, text, ...(html ? { html } : {}) }),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    console.error('[notify] send failed', res.status, body.slice(0, 200));
    return { sent: false, reason: `http-${res.status}` };
  }
  return { sent: true };
}
