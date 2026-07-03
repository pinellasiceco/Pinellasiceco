// One-shot image pipeline: pulls brand assets + real service photos from the
// repo root, trims/resizes, emits WebP (photos) and PNG (icons/OG) into
// public/. Re-runnable; overwrites outputs.
import sharp from 'sharp';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '../..');
const OUT = path.resolve(import.meta.dirname, '../public');

const jobs = [];

function photo(src, name, width = 900) {
  jobs.push(async () => {
    const out = path.join(OUT, 'images', `${name}.webp`);
    const img = sharp(path.join(ROOT, src)).rotate().resize({ width, withoutEnlargement: true });
    await img.webp({ quality: 72 }).toFile(out);
    const meta = await sharp(out).metadata();
    return `${name}.webp ${meta.width}x${meta.height}`;
  });
}

await mkdir(path.join(OUT, 'images'), { recursive: true });

// --- Brand: stacked logo (no cleaning-only tagline), trimmed ---
jobs.push(async () => {
  await sharp(path.join(ROOT, '5B2CEC02-CD0A-4D3B-A4A4-413D2E277370.png'))
    .trim().resize({ width: 640, withoutEnlargement: true })
    .png().toFile(path.join(OUT, 'images', 'pinellas-ice-co-logo.png'));
  return 'pinellas-ice-co-logo.png';
});

// Cube mark → favicon PNGs + apple-touch-icon (white padding for iOS).
jobs.push(async () => {
  const cube = sharp(path.join(ROOT, 'IMG_0037.jpeg')).trim();
  const buf = await cube.png().toBuffer();
  await sharp(buf).resize(512, 512, { fit: 'contain', background: '#ffffff' })
    .png().toFile(path.join(OUT, 'icon-512.png'));
  await sharp(buf).resize(150, 150, { fit: 'contain', background: '#ffffff' })
    .extend({ top: 15, bottom: 15, left: 15, right: 15, background: '#ffffff' })
    .png().toFile(path.join(OUT, 'apple-touch-icon.png'));
  return 'favicons';
});

// OG default 1200x630: stacked logo centered on white.
jobs.push(async () => {
  const logo = await sharp(path.join(ROOT, '5B2CEC02-CD0A-4D3B-A4A4-413D2E277370.png'))
    .trim().resize({ height: 460, withoutEnlargement: true }).png().toBuffer();
  await sharp({ create: { width: 1200, height: 630, channels: 3, background: '#ffffff' } })
    .composite([{ input: logo, gravity: 'centre' }])
    .png({ compressionLevel: 9 }).toFile(path.join(OUT, 'og-default.png'));
  return 'og-default.png';
});

// Sanitized Ice certification shield (real program asset) — cleaning page.
photo('7400C4E1-A18C-4836-AF45-DE503D636E5B.png', 'sanitized-ice-certification-badge', 480);

// Real field photos (before/after composites + component shots).
photo('docs/before-after/img/ice-grid.jpeg', 'ice-machine-cleaning-before-after-pinellas', 1000);
photo('docs/before-after/img/evaporator-plates.jpeg', 'ice-machine-evaporator-cleaning-before-after', 900);
photo('docs/before-after/img/evaporator.jpeg', 'commercial-ice-machine-evaporator-service', 900);
photo('docs/before-after/img/condenser.webp', 'ice-machine-condenser-cleaning-tampa-bay', 900);
photo('docs/before-after/img/compressor.webp', 'commercial-ice-machine-compressor-repair', 900);
photo('docs/before-after/img/pipes.jpeg', 'ice-machine-water-line-service', 900);
photo('docs/before-after/img/pump.jpeg', 'ice-machine-pump-repair-service', 900);
photo('docs/before-after/img/distributor.webp', 'ice-machine-water-distributor-cleaning', 900);

const results = [];
for (const job of jobs) {
  try { results.push(await job()); }
  catch (e) { results.push(`FAILED: ${e.message}`); }
}
console.log(results.join('\n'));
