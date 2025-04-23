import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import AutoImport from "unplugin-auto-import/vite";
import stylelint from "vite-plugin-stylelint";
import * as path from "path";

const commitHash = require("child_process").execSync("git rev-parse --short HEAD").toString();
// https://vitejs.dev/config/

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, "./");

  return {
    base: env.VITE_BASE_URL,
    envDir: "./",
    css: {
      preprocessorOptions: {
        scss: {
          api: "modern",
          quietDeps: true,
          silenceDeprecations: ["import", "global-builtin"],
        },
      },
    },
    define: {
      "import.meta.env.VITE_APP_VERSION": JSON.stringify(commitHash),
      "process.env": env,
    },
    plugins: [
      react(),
      AutoImport({
        imports: ["react", "vitest"],
        dts: true,
        eslintrc: {
          enabled: true,
        },
      }),
      stylelint(),
    ],
    server: { port: Number(env.VITE_UI_PORT), host: Boolean(env.VITE_HOST_MODE) },
    resolve: {
      alias: { "@": path.resolve(__dirname, "src") },
    },
    build: {
      chunkSizeWarningLimit: 1600,
      rollupOptions: {
        output: {
          sanitizeFileName: false,
          manualChunks: {
            react: ["react", "react-dom"],
            canonicalComponents: ["@canonical/react-components", "@canonical/maas-react-components"],
            formik: ["formik"],
            yup: ["yup"],
          },
        },
      },
    },
    experimental: {
      renderBuiltUrl(filename: string, { hostType }: { hostType: "js" | "css" | "html" }) {
        if (hostType === "js") {
          return { runtime: `window.__assetsPath__(${JSON.stringify(filename)})` };
        }
        return;
      },
    },
  };
});
