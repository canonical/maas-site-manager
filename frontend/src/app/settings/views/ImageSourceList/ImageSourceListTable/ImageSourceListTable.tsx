import { DynamicTable } from "@canonical/maas-react-components";
import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";

import { useImageSourceTableColumns } from "../hooks";

import type { BootSource } from "@/app/apiclient";
import TableCaption from "@/app/base/components/TableCaption";

type Props = {
  data: BootSource[];
  error: Error | null;
  isPending: boolean;
};

const ImageSourceListTable = ({ data, error, isPending }: Props) => {
  const columns = useImageSourceTableColumns();
  const imageSourceTable = useReactTable<BootSource>({
    data: data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    enableSorting: false,
  });

  return (
    <DynamicTable aria-label="Image source list" className="image-source-table" variant="regular">
      <thead>
        {imageSourceTable.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <th className={header.column.id} colSpan={header.colSpan} key={header.id}>
                {flexRender(header.column.columnDef.header, header.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      {error ? (
        <TableCaption inTable>
          <TableCaption.Error error={error} />
        </TableCaption>
      ) : isPending ? (
        <DynamicTable.Loading table={imageSourceTable} />
      ) : (
        <DynamicTable.Body>
          {imageSourceTable.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td className={cell.column.id} key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </DynamicTable.Body>
      )}
    </DynamicTable>
  );
};

export default ImageSourceListTable;
