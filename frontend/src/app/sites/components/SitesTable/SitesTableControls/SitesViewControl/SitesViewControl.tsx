import { Button, Icon, Tooltip } from "@canonical/react-components";

import { Link, useLocation } from "@/utils/router";

const SitesViewControl = () => {
  const { pathname, search } = useLocation();
  return (
    <div className="p-segmented-control">
      <div aria-label="sites view control" className="p-segmented-control__list sites-view-control" role="tablist">
        <Tooltip
          className="u-flex"
          positionElementClassName="u-flex"
          tooltipClassName="sites-view-control__map-tooltip"
        >
          <Button
            aria-selected={pathname === "/sites/map"}
            className="p-segmented-control__button"
            element={Link}
            id="map"
            role="tab"
            to={{ pathname: "/sites/map", search }}
          >
            <Icon name="map" />
            <span>Map</span>
          </Button>
        </Tooltip>
        <Button
          aria-selected={pathname === "/sites/list"}
          className="p-segmented-control__button"
          element={Link}
          id="table"
          role="tab"
          to={{ pathname: "/sites/list", search }}
        >
          <Icon name="switcher-environments" />
          <span>Table</span>
        </Button>
      </div>
    </div>
  );
};

export default SitesViewControl;
