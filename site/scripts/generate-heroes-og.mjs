// Hero backgrounds (desktop-only CSS backgrounds) + per-money-page OG images.
// Sources: scratch stock downloads (CC0 ice close-up; Unsplash bar interior —
// Unsplash license, no attribution required) — pass paths via argv or use
// the defaults below. Re-runnable.
import sharp from 'sharp';
import path from 'node:path';
import { mkdir } from 'node:fs/promises';

const STOCK = process.argv[2] || '/tmp/claude-0/-home-user/72669147-7f0b-5a03-af05-5e84db5b33a8/scratchpad/stock';
const PUB = path.resolve(import.meta.dirname, '../public');
await mkdir(path.join(PUB, 'images'), { recursive: true });
await mkdir(path.join(PUB, 'og'), { recursive: true });

// Navy duotone treatment: desaturate, darken, navy overlay — mixed stock
// reads as one brand and text stays readable on top.
async function heroBg(src, name, width = 1600) {
  const base = await sharp(src).resize({ width, withoutEnlargement: true })
    .modulate({ saturation: 0.55, brightness: 0.75 })
    .toBuffer();
  const { width: w, height: h } = await sharp(base).metadata();
  await sharp(base)
    .composite([{
      input: Buffer.from(
        `<svg width="${w}" height="${h}"><rect width="100%" height="100%" fill="#0E1C3A" fill-opacity="0.62"/></svg>`
      ),
      blend: 'over',
    }])
    .webp({ quality: 62 }).toFile(path.join(PUB, 'images', `${name}.webp`));
  const meta = await sharp(path.join(PUB, 'images', `${name}.webp`)).metadata();
  console.log(`${name}.webp ${meta.width}x${meta.height}`);
}

await heroBg(path.join(STOCK, 'ice1.jpg'), 'hero-ice-machine-service-tampa-bay');
await heroBg(path.join(STOCK, '1514933651103-005eec06c04b.jpg'), 'hero-commercial-bar-tampa-bay');

// OG images: navy gradient + logo + headline per money page.
const LOGO = path.resolve(import.meta.dirname, '../../5B2CEC02-CD0A-4D3B-A4A4-413D2E277370.png');
const PAGES = [
  ['og-home', 'Commercial Ice Machine Repair,', 'Sales & Leasing — Tampa Bay'],
  ['og-repair', 'Ice Machine Down?', 'Get It Running — Tampa Bay'],
  ['og-sales', 'Commercial Ice Machines', 'New & Used — Sized Right'],
  ['og-leasing', 'Ice Machine Leasing', 'Service Included — Tampa Bay'],
  ['og-cleaning', 'Documented Ice Machine', 'Cleaning — ATP Verified'],
];

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const logoBuf = await sharp(LOGO).trim().resize({ height: 200 }).png().toBuffer();
for (const [name, raw1, raw2] of PAGES) {
  const l1 = esc(raw1), l2 = esc(raw2);
  const svg = `<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0E1C3A"/><stop offset="1" stop-color="#1D3C6E"/>
    </linearGradient></defs>
    <rect width="1200" height="630" fill="url(#g)"/>
    <text x="80" y="330" font-family="Arial, Helvetica, sans-serif" font-size="56" font-weight="800" fill="#FFFFFF">${l1}</text>
    <text x="80" y="400" font-family="Arial, Helvetica, sans-serif" font-size="56" font-weight="800" fill="#6FB4E8">${l2}</text>
    <text x="80" y="490" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="600" fill="#C6D4E6">(727) 855-6873 · pinellasiceco.com</text>
  </svg>`;
  await sharp(Buffer.from(svg))
    .composite([{ input: logoBuf, top: 60, left: 80 }])
    .png({ compressionLevel: 9 })
    .toFile(path.join(PUB, 'og', `${name}.png`));
  console.log(`og/${name}.png`);
}
