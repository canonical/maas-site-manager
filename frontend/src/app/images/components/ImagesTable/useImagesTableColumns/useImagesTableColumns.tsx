import { useMemo } from "react";

import { formatBytes, Placeholder } from "@canonical/maas-react-components";
import { Icon } from "@canonical/react-components";
import type { Column, ColumnDef, Header, Row, Table } from "@tanstack/react-table";
import pluralize from "pluralize";

import TableActions from "@/app/base/components/TableActions";
import { useAppLayoutContext } from "@/app/context";
import { ChangeSourceDropdown } from "@/app/images/components/ImagesTable/ChangeSourceDropdown";
import type { ImageWithId } from "@/app/images/components/ImagesTable/ImagesTable";
import SyncStatus from "@/app/images/components/ImagesTable/SyncStatus";
import { toTitleCase } from "@/utils";

export type ImageColumnDef = ColumnDef<ImageWithId, Partial<ImageWithId>>;

export const filterHeaders = (header: Header<ImageWithId, unknown>) => header.column.id !== "os";

export const filterCells = (row: Row<ImageWithId>, column: Column<ImageWithId>) => {
  if (row.getIsGrouped()) {
    return ["select", "os"].includes(column.id);
  } else {
    return column.id !== "os";
  }
};

const useImagesTableColumns = () => {
  const { setSidebar } = useAppLayoutContext();

  return useMemo<ImageColumnDef[]>(
    () =>
      [
        {
          id: "os",
          accessorKey: "os",
          meta: {
            skeleton: () => (
              <div>
                <Placeholder variant="block" width="16ch" />
                <Placeholder variant="block" width="8ch" />
              </div>
            ),
          },
          cell: ({ row }: { row: Row<ImageWithId> }) => {
            return (
              <div>
                <div>
                  <strong>{toTitleCase(row.original.os)}</strong>
                </div>
                <small className="u-text--muted">{pluralize("image", row.getLeafRows().length ?? 0, true)}</small>
              </div>
            );
          },
        },
        {
          id: "release",
          accessorKey: "release",
          enableSorting: true,
          header: () => "Release title",
          meta: {
            skeleton: () => <Placeholder variant="block" width="18ch" />,
          },
          cell: ({
            row: {
              original: { release },
            },
          }: {
            row: Row<ImageWithId>;
          }) => release ?? "—",
        },
        {
          id: "arch",
          accessorKey: "arch",
          enableSorting: false,
          header: () => "Architecture",
          meta: {
            skeleton: () => <Placeholder variant="block" width="8ch" />,
          },
        },
        {
          id: "size",
          accessorKey: "size",
          enableSorting: false,
          header: () => "Size",
          meta: {
            skeleton: () => <Placeholder variant="block" width="9ch" />,
          },
          cell: ({
            row: {
              original: { size },
            },
          }: {
            row: Row<ImageWithId>;
          }) => {
            const { value, unit } = formatBytes({ value: size, unit: "B" });
            return `${value} ${unit}`;
          },
        },
        {
          id: "status",
          accessorKey: "status",
          enableSorting: false,
          header: () => "Status",
          meta: {
            skeleton: () => (
              <div>
                <Placeholder variant="block" width="20ch" />
              </div>
            ),
          },
          cell: ({ row: { original: image } }: { row: Row<ImageWithId> }) => <SyncStatus image={image} />,
        },
        {
          id: "custom",
          accessorKey: "is_custom_image",
          enableSorting: false,
          header: "Custom",
          meta: {
            skeleton: () => <Placeholder variant="block" width="2ch" />,
          },
          cell: ({
            row: {
              original: { custom_image_id },
            },
          }: {
            row: Row<ImageWithId>;
          }) => (!!custom_image_id ? <Icon aria-label="checked" name="task-outstanding" role="img" /> : null),
        },
        {
          id: "source",
          accessorKey: "source",
          enableSorting: false,
          header: () => "Source",
          meta: {
            skeleton: () => <Placeholder variant="block" width="14ch" />,
          },
          cell: ({ row: { original } }: { row: Row<ImageWithId> }) => <ChangeSourceDropdown image={original} />,
        },
        {
          id: "action",
          accessorKey: "id",
          header: () => "Action",
          enableSorting: false,
          meta: {
            skeleton: () => null,
          },
          cell: ({ row }: { table: Table<ImageWithId>; row: Row<ImageWithId> }) => {
            const id = row.original.selection_id ?? row.original.custom_image_id;
            return (
              <TableActions
                className="u-align--right"
                deleteDisabled={row.getIsGrouped() ? !row.getCanSelectSubRows() : !row.getCanSelect()}
                hasBorder
                isDense={false}
                onDelete={() => {
                  if (id) {
                    if (!row.getIsSelected()) {
                      row.toggleSelected();
                    }
                    setSidebar("removeAvailableImages");
                  }
                }}
              />
            );
          },
        },
      ] as ImageColumnDef[],
    [setSidebar],
  );
};
export default useImagesTableColumns;
