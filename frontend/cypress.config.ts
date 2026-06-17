import { defineConfig } from "cypress";

export default defineConfig({
  defaultCommandTimeout: 10000,
  e2e: {
    // block analytics
    blockHosts: ["www.googletagmanager.com", "www.google-analytics.com", "sentry.is.canonical.com"],
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      // The sites map is rendered with MapLibre GL, which requires a WebGL
      // context. CI runners have no GPU, so the browser must fall back to
      // software rendering (SwiftShader). Chromium 136+ (bundled with the
      // Electron used by Cypress 15) disables this fallback by default, which
      // causes the map to render nothing and the site markers to never appear.
      // Re-enable software WebGL so the map renders in headless CI.
      on("before:browser:launch", (browser, launchOptions) => {
        if (browser.family === "chromium") {
          launchOptions.args.push("--enable-unsafe-swiftshader");
          launchOptions.args.push("--use-gl=angle");
          launchOptions.args.push("--use-angle=swiftshader");
          launchOptions.args.push("--ignore-gpu-blocklist");
        }
        return launchOptions;
      });

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
