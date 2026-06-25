import { useCallback, useMemo, useState } from "react";

import type { ColumnDef, Column, Row, Getter } from "@tanstack/react-table";
import { flexRender, useReactTable, getCoreRowModel } from "@tanstack/react-table";

import type { useTokens } from "@/app/api/query/tokens";
import type { Token } from "@/app/apiclient";
import CopyButton from "@/app/base/components/CopyButton";
import DynamicTable from "@/app/base/components/DynamicTable";
import SelectAllCheckbox from "@/app/base/components/SelectAllCheckbox";
import TableCaption from "@/app/base/components/TableCaption";
import TooltipButton from "@/app/base/components/TooltipButton";
import { useRowSelection } from "@/app/context";
import { copyToClipboard, createAccessor, formatDistanceToNow, formatUTCDateString } from "@/utils";

export type TokenColumnDef = ColumnDef<Token, Partial<Token>>;
export type TokenColumn = Column<Token>;

const TokensTable = ({
  data,
  error,
  isPending,
}: Pick<ReturnType<typeof useTokens>, "data" | "error" | "isPending">) => {
  const [copiedText, setCopiedText] = useState("");

  const { rowSelection, setRowSelection } = useRowSelection("tokens", { clearOnUnmount: true });
  const isTokenCopied = useCallback((token: string) => token === copiedText, [copiedText]);

  const resetCopiedText = (timeout = 500) => {
    setTimeout(() => {
      setCopiedText("");
    }, timeout);
  };

  const handleTokenCopy = useCallback((token: string) => {
    copyToClipboard(token, setCopiedText);
    resetCopiedText();
  }, []);

  const columns = useMemo<TokenColumnDef[]>(
    () => [
      {
        id: "select",
        accessorKey: "value",
        header: ({ table }) => <SelectAllCheckbox table={table} tableId="tokens" />,
        cell: ({ row, getValue }: { row: Row<Token>; getValue: Getter<Token["value"]> }) => (
          <label className="p-checkbox--inline">
            <input
              aria-label={getValue()}
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
        ),
      },
      {
        id: "token",
        header: () => <div>Token</div>,
        accessorFn: createAccessor("value"),
        cell: ({ getValue }) => {
          const { value } = getValue();
          return (
            <div
              className="token-cell"
              onClick={() => {
                handleTokenCopy(value!);
              }}
            >
              <span className="token-text">{value}</span>
              <CopyButton isCopied={isTokenCopied(value!)} value={value || ""} />
            </div>
          );
        },
      },
      {
        id: "expirationTime",
        accessorFn: createAccessor("expired"),
        header: () => <div>Time until expiration</div>,
        cell: ({ getValue }) => {
          const { expired } = getValue();
          return (
            <TooltipButton message={expired ? `${formatUTCDateString(expired)} (UTC)` : null} position="btm-center">
              {expired ? formatDistanceToNow(expired) : null}
            </TooltipButton>
          );
        },
      },
      {
        id: "created",
        accessorFn: createAccessor("created"),
        header: () => <div>Created (UTC)</div>,
        cell: ({ getValue }) => {
          const { created } = getValue();
          return <div>{created ? formatUTCDateString(created) : null}</div>;
        },
      },
    ],
    [handleTokenCopy, isTokenCopied],
  );

  const noItems = useMemo<Token[]>(() => [], []);

  const tokenTable = useReactTable<Token>({
    data: data?.items || noItems,
    columns,
    state: {
      rowSelection,
    },
    getRowId: (row) => `${row.id}`,
    manualPagination: true,
    enableRowSelection: true,
    getCoreRowModel: getCoreRowModel(),
    enableMultiRowSelection: true,
    onRowSelectionChange: setRowSelection,
  });

  return (
    <DynamicTable aria-label="tokens" className="tokens-table u-no-margin--bottom">
      <thead>
        {tokenTable.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <th className={`tokens-table__col-${header.column.id}`} colSpan={header.colSpan} key={header.id}>
                {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      {error ? (
        <TableCaption inTable>
          <TableCaption.Error error={{ body: error }} />
        </TableCaption>
      ) : isPending ? (
        <DynamicTable.Loading table={tokenTable} />
      ) : tokenTable.getRowModel().rows.length < 1 ? (
        <TableCaption inTable>
          <TableCaption.Title>No tokens available</TableCaption.Title>
          <TableCaption.Description>
            Generate new tokens and follow the instructions above to enroll MAAS sites.
          </TableCaption.Description>
        </TableCaption>
      ) : (
        <DynamicTable.Body>
          {tokenTable.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => {
                return (
                  <td className={`tokens-table__col-${cell.column.id}`} key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                );
              })}
            </tr>
          ))}
        </DynamicTable.Body>
      )}
    </DynamicTable>
  );
};

export default TokensTable;
