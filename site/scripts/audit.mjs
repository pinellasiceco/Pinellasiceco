// Build-output audit: SEO invariants, link integrity, image alts, hotlinks,
// and phone-number consistency (every tel: link must equal config PHONE_TEL).
// Run after `npm run build`. Exits 1 on any problem.
import fs from 'node:fs';
import path from 'node:path';

const dist = path.resolve(import.meta.dirname, '../dist');
const CANONICAL_TEL = '+17278556873';
const pages = [];
(function walk(d) {
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f);
    if (fs.statSync(p).isDirectory()) walk(p);
    else if (f.endsWith('.html')) pages.push(p);
  }
})(dist);

const problems = [];
const linkTargets = new Set(['/']);
for (const p of pages) linkTargets.add('/' + path.relative(dist, path.dirname(p)).replace(/\\/g, '/') + '/');

for (const p of pages) {
  const html = fs.readFileSync(p, 'utf8');
  const rel = '/' + path.relative(dist, p);
  const isPorted = rel.includes('ice-machine-data');
  const get = (re) => (html.match(re) || [])[1];
  if (!get(/<title>([^<]*)<\/title>/)) problems.push(`${rel}: no title`);
  if (!get(/name="description" content="([^"]*)"/)) problems.push(`${rel}: no meta description`);
  const canonical = get(/rel="canonical" href="([^"]*)"/);
  if (!canonical || !canonical.endsWith('/')) problems.push(`${rel}: bad canonical ${canonical}`);
  const h1s = (html.match(/<h1[\s>]/g) || []).length;
  if (h1s !== 1 && !isPorted) problems.push(`${rel}: ${h1s} h1 tags`);
  for (const m of html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)) {
    try { JSON.parse(m[1]); } catch { problems.push(`${rel}: INVALID JSON-LD`); }
  }
  // phone consistency: every tel: must be the canonical number
  for (const m of html.matchAll(/href="tel:([^"]*)"/g)) {
    if (m[1] !== CANONICAL_TEL) problems.push(`${rel}: non-canonical tel:${m[1]}`);
  }
  if (!html.includes(`tel:${CANONICAL_TEL}`) && !isPorted) problems.push(`${rel}: no click-to-call`);
  for (const m of html.matchAll(/href="(\/[^"#?]*)"/g)) {
    let u = m[1];
    if (/^\/(images|fonts|og|favicon|apple|_astro)/.test(u)) continue;
    if (!u.endsWith('/')) u += '/';
    if (!linkTargets.has(u)) problems.push(`${rel}: dead link ${m[1]}`);
  }
  for (const m of html.matchAll(/(?:src|href)="(https?:\/\/[^"]*)"/g)) {
    if (!m[1].startsWith('https://www.pinellasiceco.com') && !m[1].startsWith('https://schema.org') && !m[1].startsWith('https://www.googletagmanager.com'))
      problems.push(`${rel}: external asset ${m[1].slice(0, 60)}`);
  }
  for (const m of html.matchAll(/<img[^>]*>/g)) {
    if (!/alt="[^"]+"/.test(m[0])) problems.push(`${rel}: img missing alt: ${m[0].slice(0, 60)}`);
  }
}

console.log(`audited ${pages.length} pages`);
if (problems.length) {
  console.error(problems.join('\n'));
  process.exit(1);
}
console.log('AUDIT CLEAN');
