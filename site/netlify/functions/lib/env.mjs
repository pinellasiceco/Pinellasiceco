// Central env access. No in-code default for OPERATOR_EMAIL (recipient-only
// identity value — documented in .env.example, never in a public artifact).

export function env(name, fallback = undefined) {
  const v = process.env[name];
  return v === undefined || v === '' ? fallback : v;
}

export function agentEnabled(flag) {
  return env(flag, 'true').toLowerCase() !== 'false';
}

export const ANTHROPIC_MODEL = () => env('ANTHROPIC_MODEL', 'claude-haiku-4-5-20251001');
export const OPERATOR_EMAIL = () => env('OPERATOR_EMAIL');
export const NOTIFY_FROM = () => env('NOTIFY_FROM_EMAIL', 'Pinellas Ice Ops <onboarding@resend.dev>');
