import { useSidePanel } from "@canonical/maas-react-components";
import type { GeoJSONSource } from "maplibre-gl";

import { lazySidePanel } from "@/app/base/sidePanel";
import { useMap } from "@/app/context/MapContext";
import { useSiteDetailsContext } from "@/app/context/SiteDetailsContext";
import Popup from "@/app/sites/views/SitesMap/components/Map/MarkersLayer/Popup";
import SiteSummary from "@/app/sites/views/SitesMap/components/Map/SiteSummary";
import { useMarkers, usePopup } from "@/app/sites/views/SitesMap/components/Map/hooks";

const SiteDetails = lazySidePanel(() => import("@/app/sites/components/SiteDetails"));

const markerHeight = 47;
const markerOffset = parseFloat((markerHeight / 2).toFixed(1));

const createSourceOptions = (geojson: GeoJSON.FeatureCollection) =>
  ({
    type: "geojson",
    data: geojson,
    cluster: true,
    clusterMaxZoom: 14,
    clusterRadius: 100,
  }) as const;

const createMarkerLayerOptions = () =>
  ({
    id: "markers",
    type: "circle",
    source: "markers",
    paint: {
      "circle-color": "transparent",
    },
  }) as const;

const createClusterLayerOptions = () =>
  ({
    id: "clusters",
    type: "circle",
    source: "markers",
    paint: {
      "circle-color": "transparent",
    },
  }) as const;

const MarkersLayer = ({ geojson }: { geojson: GeoJSON.FeatureCollection }) => {
  const map = useMap();
  const { openSidePanel } = useSidePanel();
  const { setSelected: setSiteId } = useSiteDetailsContext();
  const { popupRef, popup, showPopup, hidePopup, handleMouseEnter } = usePopup();

  const handleMarkerClick = useCallback(
    (id: number) => {
      if (id) {
        setSiteId(id);
        openSidePanel({ component: SiteDetails, title: "Site details" });
      }
      hidePopup({ isImmediate: true });
    },
    [setSiteId, openSidePanel, hidePopup],
  );

  useMarkers({
    eventHandlers: {
      mouseenter:
        ({ properties, coords }) =>
        () => {
          showPopup({ id: properties.id!, coords });
        },
      click:
        ({ properties }) =>
        () => {
          handleMarkerClick(properties.id!);
        },
      mouseout:
        ({ marker }) =>
        (e: MouseEvent) => {
          // ignore mouseout events within marker itself or popup
          const relatedTarget = (e.relatedTarget as Node) || undefined;
          if (marker.getElement().contains(relatedTarget)) {
            e.preventDefault();
          } else {
            hidePopup();
          }
        },
    },
  });

  const handleMapLoad = useCallback(() => {
    if (!map.getSource("markers")) {
      map.addSource("markers", createSourceOptions(geojson));
      // add a transparent layer to make features available for queries and custom rendering
      map.addLayer(createMarkerLayerOptions());
      map.addLayer(createClusterLayerOptions());
    }
  }, [geojson, map]);

  useEffect(() => {
    if (!map || !geojson) return;
    map.on("load", handleMapLoad);
    if (map.isStyleLoaded()) {
      const source = map.getSource("markers") as GeoJSONSource;
      source?.setData?.(geojson);
    }
  }, [map, geojson, handleMapLoad]);

  return popup ? (
    <Popup className="popup-container" coordinates={popup.coords} offset={markerOffset} ref={popupRef}>
      <SiteSummary
        id={popup.id}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => {
          hidePopup();
        }}
      />
    </Popup>
  ) : null;
};

export default MarkersLayer;
