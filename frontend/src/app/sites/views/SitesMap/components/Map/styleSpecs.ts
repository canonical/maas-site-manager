import type { LayerSpecification, StyleSpecification } from "maplibre-gl";

import mapStyle from "./map-style.json";

import { basename } from "@/constants";
export const osm: StyleSpecification = {
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

export const naturalEarth: StyleSpecification = {
  version: 8,
  glyphs: `${window.location.protocol}//${window.location.host}${basename}assets/fonts/{fontstack}/{range}.pbf`,
  sources: {
    naturalearth: {
      type: "vector",
      url: `pmtiles://${window.location.protocol}//${window.location.host}${basename}natural_earth.vector_v2.pmtiles`,
    },
  },
  layers: mapStyle.layers as LayerSpecification[],
};
