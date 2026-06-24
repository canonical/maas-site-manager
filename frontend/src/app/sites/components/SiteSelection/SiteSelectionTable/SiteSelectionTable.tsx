import { ExternalLink } from "@canonical/maas-react-components";
import { Button, Icon, Tooltip } from "@canonical/react-components";
import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import classNames from "classnames";
import pick from "lodash/fp/pick";

import type { Site } from "@/app/apiclient";
import type { SiteColumnDef } from "@/app/sites/components/SitesTable/useSitesTableColumns/useSitesTableColumns";

type Props = {
  selectedSites: Site[];
};
const createAccessor =
  <T, K extends keyof T>(keys: K | K[]) =>
  (row: T) =>
    pick(keys, row);

const SiteSelectionTable = ({ selectedSites }: Props) => {
  const columns = useMemo<SiteColumnDef[]>(
    () => [
      {
        id: "name",
        accessorKey: "name",
        enableSorting: false,
        accessorFn: createAccessor(["name", "url", "name_unique"]),
        header: () => (
          <>
            <div>Name</div>
            <div className="u-text--muted">URL</div>
          </>
        ),
        cell: ({ getValue }) => {
          return (
            <>
              <div>{getValue().name}&nbsp;</div>
              <ExternalLink to={getValue().url || ""}>{getValue().url}</ExternalLink>
            </>
          );
        },
      },
      {
        id: "actions",
        accessorKey: "id",
        enableSorting: false,
        header: () => <div className="u-visually-hidden">Actions</div>,
        cell: () => (
          <div className="u-align--right">
            <Tooltip message={<>Remove from selection</>} position="left">
              <Button
                appearance="base"
                aria-label="unselect"
                className="is-dense u-table-cell-padding-overlap site-selection-action-btn"
                hasIcon
              >
                <Icon name="close" />
              </Button>
            </Tooltip>
          </div>
        ),
      },
    ],
    [],
  );

  const table = useReactTable<Site>({
    data: selectedSites,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });
  return (
    <table aria-label="selected sites" className="selected-sites">
      <thead>
        {table.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => {
              return (
                <th
                  className={classNames(header.column.id, {
                    "p-button--table-header": header?.column?.getCanSort(),
                  })}
                  colSpan={header.colSpan}
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                >
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              );
            })}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map((row) => {
          return (
            <tr
              className={classNames(
                { "sites-table-row--muted": row.original.connection_status === "unknown" },
                "site-selection-row",
              )}
              key={row.id}
            >
              {row.getVisibleCells().map((cell) => {
                return (
                  <td className={`${cell.column.id}`} key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default SiteSelectionTable;
