import mapStyle from "./map-style.json";

import { basename, useMockData } from "@/constants";
export const osm: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap Contributors",
      maxzoom: 19,
    },
  },
  layers: [
    {
      id: "osm",
      type: "raster",
      source: "osm",
    },
  ],
};

// In mock/CI mode the pmtiles file and fonts are not downloaded (the
// download-map-assets.sh script exits early when CI=true), so we fall back to
// an empty style that lets the map initialise and fire its `load` event without
// making any external requests.  The markers layer that the tests exercise does
// not depend on background tiles.
export const naturalEarth: maplibregl.StyleSpecification = useMockData
  ? { version: 8, sources: {}, layers: [] }
  : {
      version: 8,
      glyphs: `${window.location.protocol}//${window.location.host}${basename}assets/fonts/{fontstack}/{range}.pbf`,
      sources: {
        naturalearth: {
          type: "vector",
          url: `pmtiles://${window.location.protocol}//${window.location.host}${basename}natural_earth.vector_v2.pmtiles`,
        },
      },
      layers: mapStyle.layers as maplibregl.LayerSpecification[],
    };
