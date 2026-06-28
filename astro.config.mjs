// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://grcmigrate.com',
  output: 'static',
  integrations: [
    sitemap({
      customPages: [
        'https://grcmigrate.com/',
        'https://grcmigrate.com/vanta-to-drata-migration',
        'https://grcmigrate.com/drata-to-vanta-migration',
        'https://grcmigrate.com/vanta-renewal-options',
        'https://grcmigrate.com/drata-renewal-options',
        'https://grcmigrate.com/migration-cost-calculator',
        'https://grcmigrate.com/migration-assessment',
        'https://grcmigrate.com/how-to-choose-grc-platform',
        'https://grcmigrate.com/vanta-vs-drata-comparison',
        'https://grcmigrate.com/grc-platform-checklist',
        'https://grcmigrate.com/signs-your-grc-platform-isnt-scaling',
        'https://grcmigrate.com/consultation',
        'https://grcmigrate.com/blog',
      ],
      filter: (page) => !page.includes('/thank-you'),
    }),
  ],
});
