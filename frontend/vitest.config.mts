import { configDefaults, coverageConfigDefaults, defineConfig, Plugin } from "vitest/config";
import AutoImport from "unplugin-auto-import/vite";
import * as path from "path";

export default defineConfig({
  plugins: [
    AutoImport({
      imports: ["react", "vitest"],
      dts: true,
      eslintrc: {
        enabled: true,
      },
    }) as Plugin,
  ],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  // mock-web-worker.ts runs maplibre-gl's TypeScript sources, whose style-layer subclasses
  // redeclare fields set by the base constructor. Vite 8 (Oxc) compiles them with
  // `useDefineForClassFields: true` semantics, resetting those fields to undefined; this pair
  // restores the legacy (`useDefineForClassFields: false`) behaviour they rely on.
  oxc: {
    typescript: { removeClassFieldsWithoutInitializer: true },
    assumptions: { setPublicClassFields: true },
  },
  test: {
    environment: "jsdom",
    globals: true,
    server: {
      deps: {
        // Inline maas-react-components so its bundle shares the app's single
        // react-router instance; otherwise the library's SidePanel useLocation()
        // reads a separate Router context and throws.
        inline: ["vitest-canvas-mock", /@canonical\/maas-react-components/],
      },
    },
    setupFiles: ["./mock-web-worker.ts", "./setupTests.ts"],
    // Vitest 4+ no longer excludes dist/ and cypress/ by default.
    exclude: [...configDefaults.exclude, "**/dist/**", "**/cypress/**", "**/tests/**"],
    coverage: {
      // exclude index files as they're only used to export other files
      // exclude pages as they're covered by playwright tests
      // exclude mock Resolvers:https://github.com/mswjs/msw/discussions/942#discussioncomment-1485279
      exclude: [...coverageConfigDefaults.exclude, "src/mocks/**/*"],
      include: ["src/**/*.{ts,tsx}"],
      reporter: [["text"], ["html"], ["cobertura", { file: "../../.cover/cobertura-coverage-frontend.xml" }]],
      provider: "istanbul",
    },
    clearMocks: true,
  },
});
