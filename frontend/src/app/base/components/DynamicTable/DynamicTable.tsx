import type { AriaAttributes, PropsWithChildren } from "react";
import { useState, useEffect, useLayoutEffect } from "react";

import { Placeholder } from "@canonical/maas-react-components";
import type { RowData, Table } from "@tanstack/react-table";
import classNames from "classnames";

import BREAKPOINTS from "@/app/base/breakpoints";

const DynamicTable = ({ className, children, ...props }: PropsWithChildren<{ className?: string }>) => {
  return (
    <table {...props} className={classNames("p-table-dynamic--legacy", className)}>
      {children}
    </table>
  );
};

const SkeletonRows = ({ columns }: { columns: { id: string }[] }) => (
  <>
    {Array.from({ length: 10 }, (_, index) => {
      return (
        <tr aria-hidden="true" key={index}>
          {columns.map((column, columnIndex) => {
            return (
              <td className={classNames(column.id, "u-text-overflow-clip")} key={columnIndex}>
                <Placeholder isPending style={{ opacity: 1 - index * 0.1 }} text="XXXxxxx.xxxxxxxxx" />
              </td>
            );
          })}
        </tr>
      );
    })}
  </>
);

const DynamicTableLoading = <TData extends RowData>({
  className,
  table,
}: {
  className?: string;
  table?: Table<TData>;
  placeholderLengths?: Record<string, string>;
}) => {
  const columns = table ? table.getAllColumns() : (Array.from({ length: 10 }).fill({ id: "" }) as { id: string }[]);

  return (
    <>
      <caption className="u-visually-hidden">Loading...</caption>
      <DynamicTableBody aria-busy="true" className={className}>
        <SkeletonRows columns={columns} />
      </DynamicTableBody>
    </>
  );
};
/**
 * sets a fixed height for the table body
 * allowing it to be scrolled independently of the page
 */
const DynamicTableBody = ({
  className,
  children,
  ...props
}: PropsWithChildren<AriaAttributes & { className?: string }>) => {
  const tableBodyRef = useRef<HTMLTableSectionElement>(null);
  const [offset, setOffset] = useState<number | null>(null);

  const handleResize = useCallback(() => {
    if (window.innerWidth > BREAKPOINTS.small) {
      const top = tableBodyRef.current?.getBoundingClientRect?.().top;
      if (top) setOffset(top + 1);
    } else {
      setOffset(null);
    }
  }, []);

  useLayoutEffect(() => {
    handleResize();
  }, [handleResize]);

  useEffect(() => {
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [handleResize]);

  return (
    <tbody
      className={className}
      ref={tableBodyRef}
      style={offset ? { height: `calc(100vh - ${offset}px)`, minHeight: `calc(100vh - ${offset}px)` } : undefined}
      {...props}
    >
      {children}
    </tbody>
  );
};
DynamicTable.Body = DynamicTableBody;
DynamicTable.Loading = DynamicTableLoading;

export default DynamicTable;
