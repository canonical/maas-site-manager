import type { ReactNode } from "react";

import maplibregl from "maplibre-gl";
import { createPortal } from "react-dom";

import { useMap } from "@/app/context/MapContext";

interface PopupProps {
  children: ReactNode;
  coordinates: [number, number];
  className?: string;
  offset?: number;
  padding?: number;
}

const Popup = forwardRef(({ children, coordinates, className, offset = 0, padding = 15 }: PopupProps, ref) => {
  const map = useMap();
  const container = useMemo(() => {
    return document.createElement("div");
  }, []);

  const popup = useMemo(() => {
    const options = { closeOnClick: false, className };
    const popupInstance = new maplibregl.Popup({
      ...options,
      closeButton: false,
      offset: offset + padding,
      closeOnMove: false,
    });
    const { x, y } = map.project(coordinates);
    // adjust to account for the height of the popup
    popupInstance.setLngLat(map.unproject([x, y - offset]));
    return popupInstance;
  }, [coordinates, className, map, offset, padding]);

  useImperativeHandle(ref, () => ({
    open: () => popup.addTo(map),
    close: () => popup.remove(),
    getElement: () => popup.getElement(),
    isOpen: () => popup.isOpen(),
  }));

  useLayoutEffect(() => {
    popup.setDOMContent(container).addTo(map);
    return () => {
      popup?.remove?.();
    };
  }, [map, popup, container]);

  return container ? createPortal(children, container) : null;
});

export default Popup;
