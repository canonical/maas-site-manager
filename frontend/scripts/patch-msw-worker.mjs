// Re-applies the same-origin bypass to the MSW service worker.
//
// MSW's `workerDirectory` config (see package.json) installs a postinstall hook
// that rewrites public/mockServiceWorker.js on every `yarn install`, which wipes
// our hand-applied performance guard. This script runs as our own postinstall
// hook (after MSW's) and re-injects the guard idempotently, so the optimization
// survives installs and MSW upgrades.
//
// The guard makes the worker bypass same-origin requests. Every mock handler in
// this project targets a cross-origin URL (the API at VITE_API_URL and external
// tile servers), so same-origin requests are only the Vite dev server's modules
// and static assets. Letting the worker intercept them adds a worker<->client
// round-trip per request, slowing cold dev loads by hundreds of module fetches.
//
// The script never fails the install: if the worker is missing or its template
// changes so the anchor can't be found, it warns and exits 0.

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const workerPath = resolve(scriptDir, "../public/mockServiceWorker.js");

// A signature that is unique to our guard, used to detect an already-patched
// worker so the script is idempotent.
const GUARD_SIGNATURE = "origin === self.location.origin";

// Matches the "Bypass navigation requests" block inside the fetch listener,
// regardless of quote style or trailing semicolons (MSW's generated template
// differs from the prettier-formatted committed copy). The trailing-semicolon
// presence is captured so the injected code matches the surrounding style. Only
// the single newline that terminates the block is consumed, so the blank line
// that follows it in the source is preserved as separation after the guard.
const ANCHOR = /if\s*\(\s*event\.request\.mode\s*===\s*['"]navigate['"]\s*\)\s*\{\s*return(;?)\s*\}[ \t]*\n/;

function buildGuard(semicolon) {
  return `
  // Performance: bypass same-origin requests (re-applied by scripts/patch-msw-worker.mjs).
  // Every mock handler in this project targets a cross-origin URL (the API at
  // VITE_API_URL and external tile servers), so same-origin requests are only the
  // Vite dev server's modules and static assets. Intercepting them adds a
  // worker<->client round-trip per request, which slows cold dev loads. The worker
  // is only registered when mock data is enabled in development; production never
  // registers it. Remove this guard (and this script) if you add a handler for a
  // same-origin request.
  if (new URL(event.request.url).origin === self.location.origin) {
    return${semicolon}
  }
`;
}

function main() {
  if (!existsSync(workerPath)) {
    // Nothing to patch yet (e.g. worker not generated). Don't break the install.
    return;
  }

  const source = readFileSync(workerPath, "utf8");

  if (source.includes(GUARD_SIGNATURE)) {
    // Already patched.
    return;
  }

  const match = source.match(ANCHOR);
  if (!match) {
    console.warn(
      "[patch-msw-worker] Could not find the navigation-bypass anchor in " +
        "public/mockServiceWorker.js; the same-origin bypass was NOT applied. " +
        "The MSW worker template may have changed — update scripts/patch-msw-worker.mjs.",
    );
    return;
  }

  const semicolon = match[1] ?? "";
  const patched = source.replace(match[0], `${match[0]}${buildGuard(semicolon)}`);
  writeFileSync(workerPath, patched, "utf8");
  console.log("[patch-msw-worker] Applied same-origin bypass to public/mockServiceWorker.js");
}

main();
