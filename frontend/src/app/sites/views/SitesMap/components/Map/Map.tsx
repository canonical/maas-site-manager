import { Spinner } from "@canonical/react-components";
import type { LngLatLike, MapOptions } from "maplibre-gl";
import { LngLat } from "maplibre-gl";
import useLocalStorageState from "use-local-storage-state";

import MarkersLayer from "./MarkersLayer";
import { naturalEarth, osm } from "./styleSpecs";
import type { MapProps } from "./types";
import { getGeoJson } from "./utils";

import { useCurrentUser } from "@/app/api/query/users";
import type { MapSettingsStorageState } from "@/app/settings/views/MapSettings/MapSettings";
import MapContainer from "@/app/sites/views/SitesMap/components/Map/MapContainer";

const Map: React.FC<MapProps> = ({ markers }) => {
  const [hasAcceptedOsmTos] = useLocalStorageState<MapSettingsStorageState>("hasAcceptedOsmTos", {
    storageSync: true,
    defaultValue: {},
  });

  const [bounds, setBounds] = useState<{
    minLng: number;
    maxLng: number;
    minLat: number;
    maxLat: number;
  } | null>(null);

  useEffect(() => {
    if (!markers || markers.length === 0 || bounds !== null) return;

    const newBounds = markers.reduce(
      (acc, marker) => {
        const [lng, lat] = marker.position;
        return {
          minLng: Math.min(acc.minLng, lng),
          maxLng: Math.max(acc.maxLng, lng),
          minLat: Math.min(acc.minLat, lat),
          maxLat: Math.max(acc.maxLat, lat),
        };
      },
      {
        minLng: 180,
        maxLng: -180,
        minLat: 90,
        maxLat: -90,
      },
    );

    setBounds(newBounds);
  }, [markers, bounds]);

  const center = useMemo(() => {
    if (!bounds) return null;
    const centerLng = (bounds.minLng + bounds.maxLng) / 2;
    const centerLat = (bounds.minLat + bounds.maxLat) / 2;
    return [centerLng, centerLat] as LngLatLike;
  }, [bounds]);

  const { data: currentUser, isPending, isSuccess } = useCurrentUser();
  const geojson = useMemo(() => (markers ? getGeoJson(markers) : null), [markers]);

  if (isPending) {
    return <Spinner text="Loading..." />;
  }

  if (!isSuccess || !currentUser) {
    return null;
  }

  const style = hasAcceptedOsmTos[currentUser.username] ? osm : naturalEarth;

  const customAttribution =
    style === osm ? `<a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>` : undefined;
  const isTest = process.env.NODE_ENV === "test";
  const initialOptions: MapOptions = {
    container: "map",
    style,
    dragRotate: false,
    ...(!isTest &&
      bounds && { bounds: [new LngLat(bounds!.minLng, bounds!.minLat), new LngLat(bounds!.maxLng, bounds!.maxLat)] }),
    trackResize: true,
    ...(isTest ? { center: [0, 0] } : center && { center: center }),
    zoom: 3,
    maxZoom: 17,
    renderWorldCopies: true,
  };

  return (
    <MapContainer className="map" customAttribution={customAttribution} initialOptions={initialOptions}>
      {geojson ? <MarkersLayer geojson={geojson} /> : null}
    </MapContainer>
  );
};

export default Map;
