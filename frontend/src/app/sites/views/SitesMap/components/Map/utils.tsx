import type { FeatureCollection } from "geojson";
import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";

import type { SiteMarkerType } from "./types";

/**
 * Renders the React element to an HTML string synchronously.
 * This is required as MapLibreGL only accepts HTML.
 * Note: this should be used cautiously and sparingly.
 * @see {@link https://react.dev/reference/react-dom/server/renderToString#removing-rendertostring-from-the-client-code}
 */
export const renderToHtmlString = (element: React.ReactNode): string => {
  const div = document.createElement("div");
  const root = createRoot(div);

  flushSync(() => {
    root.render(element);
  });

  return div.innerHTML;
};

export const createElementFromHTML = (htmlString: string): HTMLDivElement => {
  const div = document.createElement("div");
  div.innerHTML = htmlString.trim();
  return div;
};

export const getGeoJson = (markers: SiteMarkerType[]): FeatureCollection => ({
  type: "FeatureCollection",
  features: markers
    .filter((marker) => marker.position !== null && marker.position !== undefined)
    .map((marker) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: marker.position,
      },
      properties: {
        id: marker.id,
      },
    })),
});
