/* eslint-disable no-console */
import * as React from "react";

import * as ReactDOM from "react-dom/client";

import packageInfo from "../package.json";

import App from "@/App";
import { baseURL } from "@/app/api";
import { useMockData } from "@/constants";
import { getApiUrl } from "@/utils/test-urls";

/* c8 ignore next 4 */
if (useMockData) {
  const { worker } = await import("./mocks/browser");
  console.info("msw baseUrl %s", baseURL);
  console.info("msw API URL %s", getApiUrl(""));
  await worker.start({
    onUnhandledRequest(req) {
      const url = new URL(req.url);
      if (url.href.includes(baseURL)) {
        console.warn("Found an unhandled %s request to %s", req.method, url.href);
      }
    },
  });
}

const environment = process.env.NODE_ENV;
const version = packageInfo.version;
const release = import.meta.env.VITE_APP_VERSION;
if (environment !== "test") {
  console.log(`%cMAAS Site Manager \n${version} ${release}\n${environment}`, "color: #e95420; font-weight: bold;");
}

// Initialize map resources to lower load times
// and avoid reinitialising when navigating between pages
const hasMapResources = localStorage.getItem("hasAcceptedOsmTos");
if (!hasMapResources || hasMapResources === "false") {
  import("maplibre-gl").then((maplibregl) => {
    maplibregl.default.prewarm();
  });
}

// https://sentry.is.canonical.com/canonical/maas-site-manager/
import("@sentry/browser").then((Sentry) =>
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment,
    release,
    beforeSend: (event) => ({
      ...event,
      // send just the pathname of the current page excluding the origin
      // this allows for grouping of errors by route
      tags: { ...event.tags, url: window.location.pathname, version },
    }),
  }),
);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
