import { useMemo } from "react";

import { ExternalLink } from "@canonical/maas-react-components";
import { useReactTable, flexRender, getCoreRowModel } from "@tanstack/react-table";
import type { Column, ColumnDef } from "@tanstack/react-table";

import type { UseEnrollmentRequestsResult } from "@/app/api/query/enrollmentRequests";
import type { PendingSite } from "@/app/apiclient";
import DynamicTable from "@/app/base/components/DynamicTable/DynamicTable";
import SelectAllCheckbox from "@/app/base/components/SelectAllCheckbox";
import TableCaption from "@/app/base/components/TableCaption";
import docsUrls from "@/app/base/docsUrls";
import { useRowSelection } from "@/app/context/RowSelectionContext/RowSelectionContext";
import DateTime from "@/app/settings/views/RequestsList/components/DateTime";
import { isDev } from "@/constants";

export type EnrollmentRequestsColumnDef = ColumnDef<PendingSite, PendingSite[keyof PendingSite]>;
export type EnrollmentRequestsColumn = Column<PendingSite>;

const RequestsTable = ({
  currentPage,
  data,
  error,
  isPending,
  pageSize,
}: Pick<UseEnrollmentRequestsResult, "data" | "error" | "isPending"> & {
  currentPage: number;
  pageSize: number;
}) => {
  const { rowSelection, setRowSelection } = useRowSelection("requests", {
    clearOnUnmount: true,
    currentPage,
    pageSize,
  });
  const columns = useMemo<EnrollmentRequestsColumnDef[]>(
    () => [
      {
        id: "select",
        accessorKey: "name",
        header: ({ table }) => <SelectAllCheckbox table={table} tableId="requests" />,
        cell: ({ row, getValue }) => {
          return (
            <label className="p-checkbox--inline">
              <input
                aria-label={`select ${getValue()}`}
                className="p-checkbox__input"
                type="checkbox"
                {...{
                  checked: row.getIsSelected(),
                  disabled: !row.getCanSelect(),
                  onChange: row.getToggleSelectedHandler(),
                }}
              />
              <span className="p-checkbox__label" />
            </label>
          );
        },
      },
      {
        id: "name",
        accessorKey: "name",
        header: () => <div>Name</div>,
      },
      {
        id: "url",
        accessorKey: "url",
        header: () => <div>URL</div>,
        cell: ({ getValue }) => <ExternalLink to={String(getValue())}>{getValue()}</ExternalLink>,
      },
      {
        id: "created",
        accessorKey: "created",
        header: () => <div>Time of request (UTC)</div>,
        cell: ({ getValue }) => <DateTime value={String(getValue())} />,
      },
    ],
    [],
  );

  // wrap the empty array in useMemo to avoid re-rendering the empty table on every render
  const noItems = useMemo<PendingSite[]>(() => [], []);
  const table = useReactTable<PendingSite>({
    data: data?.items || noItems,
    columns,
    state: {
      rowSelection,
    },
    getRowId: (row) => `${row.id}`,
    manualPagination: true,
    enableRowSelection: true,
    enableMultiRowSelection: true,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    debugTable: isDev,
    debugHeaders: isDev,
    debugColumns: isDev,
  });

  return (
    <DynamicTable aria-label="enrollment requests" className="sites-table">
      <thead>
        {table.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => {
              return (
                <th className={`${header.column.id}`} colSpan={header.colSpan} key={header.id}>
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              );
            })}
          </tr>
        ))}
      </thead>
      {error ? (
        <TableCaption inTable>
          <TableCaption.Error error={{ body: error }} />
        </TableCaption>
      ) : isPending ? (
        <DynamicTable.Loading table={table} />
      ) : table.getRowModel().rows.length < 1 ? (
        <TableCaption inTable>
          <TableCaption.Title>No outstanding requests</TableCaption.Title>
          <TableCaption.Description>
            You have to request an enrollment in the site-manager-agent.
            <br />
            <ExternalLink to={docsUrls.enrollmentRequest}>Read more about it in the documentation.</ExternalLink>
          </TableCaption.Description>
        </TableCaption>
      ) : (
        <DynamicTable.Body>
          {table.getRowModel().rows.map((row) => {
            return (
              <tr key={row.id}>
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
        </DynamicTable.Body>
      )}
    </DynamicTable>
  );
};

export default RequestsTable;
