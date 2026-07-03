// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://www.pinellasiceco.com',
  output: 'static',
  // One canonical URL convention from day one (GRC's trailing-slash lesson):
  // directory build format + trailing slash everywhere. Netlify 301s the
  // slash-less form to the slash form in a single hop.
  trailingSlash: 'always',
  build: { format: 'directory' },
  integrations: [
    sitemap({
      // Sitemap emits canonicals only: no thank-you page, no ops surfaces.
      filter: (page) => !page.includes('/thank-you'),
      // Ported static page (public/ice-machine-data/) — outside Astro's routes.
      customPages: ['https://www.pinellasiceco.com/ice-machine-data/'],
    }),
  ],
});
