// Single source of truth for contact + analytics identity.
// The phone number here feeds the header, sticky call bar, LocalBusiness
// schema, footer, and form components. Page-body tel: links are audited
// against PHONE_TEL at build-verify time (scripts/audit.mjs).

export const PHONE_DISPLAY = '(727) 855-6873';
export const PHONE_TEL = '+17278556873';
export const PHONE_HREF = `tel:${PHONE_TEL}`;

// Response-time promise shown site-wide. [OPERATOR: confirm] the wording —
// it ships in the conservative "usually / during business hours" form.
export const RESPONSE_LINE = 'We call back fast — usually within the hour during business hours.';

// GA4 measurement ID. [OPERATOR: set GA4 ID] — leave empty to ship ZERO
// analytics JS. When set (e.g. 'G-XXXXXXXXXX'), BaseLayout injects gtag plus
// call-click / lead-form-submit event instrumentation.
export const GA4_ID = '';
