const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  testMatch: ['**/*.spec.js'],
  timeout: 90000,
  retries: 1,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  use: {
    baseURL: 'http://localhost:8080',
    headless: true,
    serviceWorkers: 'block',
  },
  webServer: {
    command: 'python3 -m http.server 8080',
    port: 8080,
    reuseExistingServer: true,
    timeout: 10000,
  },
});
