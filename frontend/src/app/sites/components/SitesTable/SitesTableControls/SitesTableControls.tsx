import { MainToolbar } from "@canonical/maas-react-components";
import { SearchBox } from "@canonical/react-components";
import classNames from "classnames";

import SitesCount from "./SitesCount";
import SitesViewControl from "./SitesViewControl";

import type { UseSitesResult } from "@/app/api/query/sites";
import RemoveButton from "@/app/base/components/RemoveButton";
import { useAppLayoutContext } from "@/app/context/AppLayoutContext";
import { useRowSelection } from "@/app/context/RowSelectionContext/RowSelectionContext";
import { useLocation } from "@/utils/router";

const SitesTableControls = ({
  totalSites,
  isPending,
  setSearchText,
  searchText,
}: Pick<UseSitesResult, "isPending"> & {
  totalSites: number | null;
  isPending: boolean;
  setSearchText?: (text: string) => void;
  searchText?: string;
}) => {
  const { pathname } = useLocation();
  const { setSidebar } = useAppLayoutContext();
  const { rowSelection } = useRowSelection("sites");
  const isRemoveDisabled = Object.keys(rowSelection).length <= 0;
  const isMapView = pathname === "/sites/map";

  return (
    <span className={classNames("sites-table-controls", { "is-map-view": isMapView })}>
      <MainToolbar>
        <MainToolbar.Title>
          <SitesCount isPending={isPending} totalSites={totalSites} />
        </MainToolbar.Title>
        <MainToolbar.Controls>
          {setSearchText && (
            <SearchBox
              aria-label="Search and filter"
              className="sites-table-controls__search"
              externallyControlled
              onChange={setSearchText}
              placeholder="Search and filter"
              value={searchText}
            />
          )}
          <span className="remove-button__wrapper">
            <RemoveButton
              disabled={isRemoveDisabled}
              onClick={() => {
                setSidebar("removeSites");
              }}
              showDeleteIcon
              type="button"
            />
          </span>
          <SitesViewControl />
        </MainToolbar.Controls>
      </MainToolbar>
    </span>
  );
};

export default SitesTableControls;
