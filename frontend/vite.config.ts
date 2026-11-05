import react from "@vitejs/plugin-react-swc";
import childProcess from "child_process";
import fs from "fs";
import * as path from "path";
import AutoImport from "unplugin-auto-import/vite";
import { defineConfig, loadEnv, type Plugin } from "vite";
import stylelint from "vite-plugin-stylelint";

const commitHash = childProcess.execSync("git rev-parse --short HEAD").toString();
// https://vitejs.dev/config/

function excludeMsw(): Plugin {
  return {
    name: "exclude-msw",
    resolveId(source) {
      return source === "virtual-module" ? source : null;
    },
    renderStart(outputOptions) {
      const outDir = outputOptions.dir;
      if (!outDir) return;
      const msWorker = path.resolve(outDir, "mockServiceWorker.js");
      fs.rm(msWorker, () => console.log(`Deleted ${msWorker}`));
    },
  };
}

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
      excludeMsw(),
      AutoImport({
        imports: ["react", "vitest"],
        dts: true,
        eslintrc: {
          enabled: true,
        },
      }),
      stylelint(),
    ],
    server: {
      port: Number(env.VITE_UI_PORT),
      host: Boolean(env.VITE_HOST_MODE),
      // Eagerly transform the always-loaded entry modules (and the heavy
      // global stylesheet that pulls in all of vanilla-framework) while the
      // dependency optimizer is running, so the browser's first request for
      // them is served from cache instead of triggering a cold compile.
      warmup: {
        clientFiles: ["./src/main.tsx", "./src/App.tsx", "./src/routes/routes.tsx", "./src/styles/App.scss"],
      },
    },
    resolve: {
      alias: { "@": path.resolve(__dirname, "src") },
    },
    build: {
      chunkSizeWarningLimit: 1600,
      rolldownOptions: {
        output: {
          sanitizeFileName: false,
          // Rolldown (Vite 8) has no object-form `manualChunks`; `codeSplitting.groups` replaces it.
          codeSplitting: {
            groups: [
              { name: "react", test: /[\\/]node_modules[\\/](react|react-dom|scheduler|formik)[\\/]/ },
              {
                name: "canonicalComponents",
                test: /[\\/]node_modules[\\/]@canonical[\\/](react-components|maas-react-components)[\\/]/,
              },
              { name: "yup", test: /[\\/]node_modules[\\/]yup[\\/]/ },
            ],
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
