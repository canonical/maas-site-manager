import { useMemo } from "react";

import { ExternalLink, Placeholder } from "@canonical/maas-react-components";
import { Button, Icon } from "@canonical/react-components";
import type { ColumnDef, OnChangeFn, RowSelectionState } from "@tanstack/react-table";

import type { Site } from "@/app/apiclient";
import LocalTime from "@/app/base/components/LocalTime";
import SortIndicator from "@/app/base/components/SortIndicator";
import TableActions from "@/app/base/components/TableActions";
import TooltipButton from "@/app/base/components/TooltipButton";
import type { Sidebar } from "@/app/context/AppLayoutContext";
import AggregatedStatus from "@/app/sites/components/SitesTable/AggregatedStatus";
import ConnectionInfo from "@/app/sites/components/SitesTable/ConnectionInfo";
import ColumnsVisibilityControl from "@/app/sites/components/SitesTable/SitesTableControls/ColumnsVisibilityControl";
import { createAccessor, getCountryName } from "@/utils";

export type SiteColumnDef = ColumnDef<Site, Partial<Site>>;

const useSitesTableColumns = ({
  setRowSelection,
  setSiteId,
  setSidebar,
}: {
  setRowSelection: OnChangeFn<RowSelectionState>;
  setSiteId: OnChangeFn<number | null>;
  setSidebar: (sidebar: Sidebar) => void;
}): SiteColumnDef[] => {
  return useMemo(
    () =>
      [
        {
          id: "name",
          accessorKey: "name",
          enableSorting: true,
          accessorFn: createAccessor(["name", "url", "name_unique"]),
          meta: {
            isInteractiveHeader: true,
            skeleton: () => (
              <div>
                <Placeholder variant="block" width="16ch" />
                <Placeholder variant="block" width="24ch" />
              </div>
            ),
          },
          header: (header) => (
            <>
              <Button
                appearance="link"
                className="p-button--column-header"
                onClick={(e) => {
                  e.stopPropagation();
                  const sortingFn = header.column.getToggleSortingHandler();
                  sortingFn && sortingFn(e);
                }}
                type="button"
              >
                Name
              </Button>
              {{
                asc: <Icon name={"chevron-up"}>ascending</Icon>,
                desc: <Icon name={"chevron-down"}>descending</Icon>,
              }[header?.column?.getIsSorted() as string] ?? null}
              <br />
              <span className="u-text--muted">URL</span>
            </>
          ),
          cell: ({ getValue }) => {
            return (
              <>
                <div>
                  {getValue().name}&nbsp;
                  {!getValue().name_unique ? (
                    <TooltipButton
                      buttonProps={{ "aria-label": "warning - name is not unique" }}
                      iconName="warning"
                      iconProps={{ className: "u-no-margin--left" }}
                      message={
                        <>
                          This MAAS name is not unique in Site Manager.
                          <br />
                          You can change this name in the MAAS site itself.
                        </>
                      }
                    ></TooltipButton>
                  ) : null}
                </div>
                <ExternalLink to={getValue().url || ""}>{getValue().url}</ExternalLink>
              </>
            );
          },
        },
        {
          id: "connection",
          // TODO: enable sorting once the back-end supports it for this key https://warthogs.atlassian.net/browse/MAASENG-1844
          enableSorting: false,
          accessorFn: createAccessor(["stats", "connection_status"]),
          meta: {
            skeleton: () => (
              <div>
                <Placeholder variant="block" width="12ch" />
                <Placeholder variant="block" width="16ch" />
              </div>
            ),
          },
          header: ({ header }) => (
            <>
              <div className="connection__text">
                Connection <SortIndicator header={header} />
              </div>
              <div className="connection__text u-text--muted">Last seen</div>
            </>
          ),
          cell: ({ getValue }) => {
            const { stats, connection_status } = getValue();
            return connection_status ? (
              <ConnectionInfo connection={connection_status} lastSeen={stats?.last_seen} />
            ) : null;
          },
        },
        {
          id: "address",
          enableSorting: false,
          accessorFn: createAccessor(["country", "city", "address", "postal_code"]),
          meta: {
            skeleton: () => (
              <div>
                <Placeholder variant="block" width="14ch" />
                <Placeholder variant="block" width="22ch" />
              </div>
            ),
          },
          header: ({ header }) => (
            <>
              <div>
                Country <SortIndicator header={header} />
              </div>
              <div className="u-text--muted">Address, city, postal code</div>
            </>
          ),
          cell: ({ getValue }) => {
            const { country, city, address, postal_code } = getValue();
            return (
              <>
                <div>{country ? getCountryName(country) : ""}</div>
                <div className="u-text--muted">
                  {address}, {city} {postal_code}
                </div>
              </>
            );
          },
        },
        {
          id: "time",
          accessorKey: "timezone",
          enableSorting: false,
          accessorFn: createAccessor(["timezone"]),
          header: "Local time (24hr)",
          meta: {
            skeleton: () => <Placeholder variant="block" width="10ch" />,
          },
          cell: ({ getValue }) => {
            const { timezone } = getValue();
            return timezone ? (
              <div>
                <LocalTime timezone={timezone} />
              </div>
            ) : null;
          },
        },
        {
          id: "machines",
          // TODO: enable sorting once the back-end supports it for this key https://warthogs.atlassian.net/browse/MAASENG-1844
          enableSorting: false,
          accessorFn: createAccessor("stats"),
          header: "Machines",
          meta: {
            skeleton: () => <Placeholder variant="block" width="5ch" />,
          },
          cell: ({ getValue }) => {
            const { stats } = getValue();
            return stats ? stats.machines_total : null;
          },
        },
        {
          id: "status",
          enableSorting: false,
          accessorFn: createAccessor("stats"),
          header: "Aggregated status",
          meta: {
            skeleton: () => (
              <div>
                <Placeholder variant="block" width="18ch" />
                <Placeholder variant="block" width="12ch" />
              </div>
            ),
          },
          cell: ({ getValue }) => {
            const { stats } = getValue();
            return stats ? <AggregatedStatus stats={stats} /> : null;
          },
        },
        {
          id: "actions",
          accessorKey: "id",
          accessorFn: createAccessor("id"),
          enableSorting: false,
          meta: {
            skeleton: () => null,
          },
          header: ({ table }) => <ColumnsVisibilityControl columns={table.getAllLeafColumns()} />,
          cell: ({ getValue }) => {
            const { id } = getValue();
            return (
              <TableActions
                className="u-align--right"
                hasBorder
                onDelete={() => {
                  if (id) {
                    setRowSelection({ [id]: true });
                    setSidebar("removeSites");
                  }
                }}
                onEdit={() => {
                  if (id) {
                    setSiteId(id);
                    setSidebar("editSite");
                  }
                }}
              />
            );
          },
        },
      ] as SiteColumnDef[],
    [setRowSelection, setSidebar, setSiteId],
  );
};

export default useSitesTableColumns;
