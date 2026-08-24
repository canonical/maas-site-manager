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
    exclude: [...configDefaults.exclude, "**/tests/**"],
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
