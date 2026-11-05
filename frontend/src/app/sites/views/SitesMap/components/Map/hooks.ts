import { useCallback, useEffect, useRef } from "react";

import type { MapSourceDataEvent } from "maplibre-gl";
import maplibregl from "maplibre-gl";

import { useMap } from "@/app/context/MapContext";
import {
  createCustomClusterIcon,
  getClusterSize,
  getSiteMarker,
} from "@/app/sites/views/SitesMap/components/Map/SiteMarker";

type Coordinates = [number, number];
type MarkerID = number;
type Markers = Map<MarkerID, maplibregl.Marker>;

interface MarkerProperties {
  id?: MarkerID;
  cluster?: boolean;
  cluster_id?: MarkerID;
  point_count?: number;
}

interface Feature {
  geometry: {
    coordinates: number[];
  };
  properties: MarkerProperties;
}

interface MarkerEventHandlers {
  click?: (props: MarkerProps) => (e: Event) => void;
  [key: string]: ((props: MarkerProps) => (e: MouseEvent) => void) | undefined;
}

interface MarkerProps {
  marker: maplibregl.Marker;
  properties: MarkerProperties;
  coords: Coordinates;
}

interface UseMarkers {
  eventHandlers: MarkerEventHandlers;
}

const getMaxClusterCount = (features: Feature[]): number => {
  return features.reduce((max, { properties }) => {
    if (properties?.cluster && properties.point_count) {
      return Math.max(max, properties.point_count);
    }
    return max;
  }, 0);
};

const extractCoordinates = (geometry: Feature["geometry"]): Coordinates | null => {
  if ("coordinates" in geometry && geometry.coordinates.length === 2) {
    return geometry.coordinates as Coordinates;
  }
  return null;
};

const getFeatureId = (properties: MarkerProperties): MarkerID | null => {
  return properties.id || properties.cluster_id || null;
};

export const useMarkers = ({ eventHandlers }: UseMarkers) => {
  const map = useMap();
  const markers = useRef<Markers>(new Map());
  const visibleMarkers = useRef<Set<MarkerID>>(new Set());

  const handleClusterExpansion = useCallback(
    async (coords: Coordinates, clusterId: MarkerID) => {
      try {
        const source = map.getSource("markers") as maplibregl.GeoJSONSource;
        const zoom = await source.getClusterExpansionZoom(clusterId);

        map.easeTo({
          center: coords,
          zoom,
        });
      } catch (error) {
        throw new Error(`Failed to get cluster expansion zoom: ${error}`);
      }
    },
    [map],
  );

  const attachEventHandlers = useCallback(
    (element: HTMLDivElement, markerProps: MarkerProps) => {
      const handleKeyPress = (e: KeyboardEvent) => {
        if (e.key === "Enter" && eventHandlers.click) {
          eventHandlers.click(markerProps)(e);
        }
      };

      Object.entries(eventHandlers).forEach(([eventName, handler]) => {
        if (handler) {
          element.addEventListener(eventName, handler(markerProps) as EventListener);
        }
      });

      if (eventHandlers.click) {
        element.addEventListener("keypress", handleKeyPress);
      }
    },
    [eventHandlers],
  );

  const attachClusterHandlers = useCallback(
    (element: HTMLDivElement, coords: Coordinates, clusterId: MarkerID) => {
      const handleClick = () => handleClusterExpansion(coords, clusterId);
      const handleKeyPress = (e: KeyboardEvent) => {
        if (e.key === "Enter") {
          return handleClusterExpansion(coords, clusterId);
        }
      };

      element.addEventListener("click", handleClick);
      element.addEventListener("keypress", handleKeyPress);
    },
    [handleClusterExpansion],
  );

  const createRegularMarker = useCallback(
    (coords: Coordinates, properties: MarkerProperties) => {
      const element = getSiteMarker("base", properties.id!);
      const marker = new maplibregl.Marker({
        element,
        anchor: "bottom",
      }).setLngLat(coords);

      attachEventHandlers(element, { marker, properties, coords });
      return marker;
    },
    [attachEventHandlers],
  );

  const createClusterMarker = useCallback(
    (coords: Coordinates, properties: MarkerProperties, maxCount: number) => {
      const element = createCustomClusterIcon("base", properties.point_count!, maxCount);
      const marker = new maplibregl.Marker({
        element,
        anchor: "center",
      }).setLngLat(coords);

      attachClusterHandlers(element, coords, properties.cluster_id!);
      return marker;
    },
    [attachClusterHandlers],
  );

  const updateClusterMarkerSize = useCallback((marker: maplibregl.Marker, pointCount: number, maxCount: number) => {
    const clusterIcon = marker.getElement().firstElementChild as HTMLElement;
    const newSize = `${getClusterSize(pointCount, maxCount)}px`;

    clusterIcon.style.width = newSize;
    clusterIcon.style.height = newSize;

    return marker;
  }, []);

  const processFeatures = useCallback(() => {
    if (!map) return;

    const availableLayers = [];
    if (map.getLayer("clusters")) availableLayers.push("clusters");
    if (map.getLayer("markers")) availableLayers.push("markers");

    if (availableLayers.length === 0) return;

    const features = map.queryRenderedFeatures(undefined, {
      layers: availableLayers,
    }) as Feature[];

    const maxCount = getMaxClusterCount(features);
    const currentMarkerIds = new Set<MarkerID>();

    for (const feature of features) {
      const coords = extractCoordinates(feature.geometry);
      const id = getFeatureId(feature.properties);

      if (!coords || id === null) continue;

      currentMarkerIds.add(id);
      let marker = markers.current.get(id);

      if (!marker) {
        marker = feature.properties.cluster
          ? createClusterMarker(coords, feature.properties, maxCount)
          : createRegularMarker(coords, feature.properties);

        markers.current.set(id, marker);
      } else {
        if (feature.properties.cluster) {
          marker = updateClusterMarkerSize(marker, feature.properties.point_count!, maxCount);
        }
        marker.setLngLat(coords);
      }

      if (!visibleMarkers.current.has(id)) {
        marker.addTo(map);
        visibleMarkers.current.add(id);
      }
    }

    for (const [id, marker] of markers.current.entries()) {
      if (!currentMarkerIds.has(id)) {
        marker.remove();
        markers.current.delete(id);
        visibleMarkers.current.delete(id);
      }
    }
  }, [map, createRegularMarker, createClusterMarker, updateClusterMarkerSize]);

  useEffect(() => {
    if (!map) return;

    const handleMapUpdate = () => {
      requestAnimationFrame(() => {
        processFeatures();
      });
    };

    const handleSourceData = (e: MapSourceDataEvent) => {
      if (e.sourceId === "markers" && e.isSourceLoaded) {
        setTimeout(() => {
          processFeatures();
        }, 0);
      }
    };

    map.on("moveend", handleMapUpdate);
    map.on("zoomend", handleMapUpdate);
    map.on("sourcedata", handleSourceData);
    map.on("move", handleMapUpdate);
    map.on("zoom", handleMapUpdate);

    const initialRender = () => {
      if (map.loaded()) {
        processFeatures();
      } else {
        map.once("load", processFeatures);
      }
    };

    setTimeout(initialRender, 100);

    return () => {
      map.off("moveend", handleMapUpdate);
      map.off("zoomend", handleMapUpdate);
      map.off("sourcedata", handleSourceData);
      map.off("move", handleMapUpdate);
      map.off("zoom", handleMapUpdate);
    };
  }, [map, processFeatures]);

  return {
    updateMarkers: processFeatures,
  };
};

export const usePopup = () => {
  const popupRef = useRef<HTMLElement>(null);
  const [popup, setPopup] = useState<{ id: number; coords: [number, number] } | null>(null);
  const { withDelay, resetDelay } = useWithDelay();

  const showPopup = ({ id, coords }: { id: number; coords: MarkerProps["coords"] }) => {
    resetDelay();
    withDelay(() => {
      setPopup({ id, coords });
    });
  };

  const hidePopup = ({ isImmediate = false }: { isImmediate?: boolean } = {}) => {
    resetDelay();
    if (isImmediate) {
      setPopup(null);
    } else {
      withDelay(() => {
        setPopup(null);
      });
    }
  };

  const handleMouseEnter = () => {
    resetDelay();
  };

  return { popupRef, popup, showPopup, hidePopup, handleMouseEnter };
};

const MARKER_HOVER_DELAY = 750;
export const useWithDelay = (delay = MARKER_HOVER_DELAY) => {
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const resetDelay = () => {
    clearTimeout(timeoutRef.current);
  };

  const withDelay = (fn: () => unknown) => {
    resetDelay();
    timeoutRef.current = setTimeout(fn, delay);
  };

  return { withDelay, resetDelay };
};
