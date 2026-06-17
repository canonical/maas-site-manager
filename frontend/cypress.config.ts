import { defineConfig } from "cypress";

export default defineConfig({
  defaultCommandTimeout: 10000,
  e2e: {
    // block analytics
    blockHosts: ["www.googletagmanager.com", "www.google-analytics.com", "sentry.is.canonical.com"],
    setupNodeEvents(on, config) {
      on("task", {
        log(args) {
          console.log(args);

          return null;
        },
        table(message) {
          console.table(message);

          return null;
        },
      });
      return config;
    },
    baseUrl: "http://localhost:8405",
    specPattern: "cypress/e2e/**/*.{js,jsx,ts,tsx}",
    viewportHeight: 1300,
    viewportWidth: 1440,
  },
  env: {
    password: "admin",
    email: "admin@example.com",
  },
});
