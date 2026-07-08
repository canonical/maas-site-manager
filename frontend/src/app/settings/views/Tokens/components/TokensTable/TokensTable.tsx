import { GenericTable } from "@canonical/maas-react-components";

import { useTokens } from "@/app/api/query/tokens";
import TableCaption from "@/app/base/components/TableCaption";
import type usePagination from "@/app/base/hooks/usePagination";
import type { useRowSelection } from "@/app/context";
import { useTokensTableColumns } from "@/app/settings/views/Tokens/components/TokensTable/useTokensTableColumns/useTokensTableColumns";
import { isDev } from "@/constants";

type TokensTableProps = Omit<ReturnType<typeof usePagination>, "handleNextClick" | "handlePreviousClick"> &
  Omit<ReturnType<typeof useRowSelection>, "clearRowSelection">;

const TokensTable = ({
  page,
  debouncedPage,
  size,
  handlePageSizeChange,
  setPage,
  rowSelection,
  setRowSelection,
}: TokensTableProps) => {
  const { error, data, isPending } = useTokens({
    query: { page: debouncedPage, size },
  });

  const columns = useTokensTableColumns();

  return (
    <GenericTable
      aria-label="Tokens table"
      className="tokens-table"
      columns={columns}
      data={data?.items ?? []}
      debug={isDev}
      isLoading={isPending}
      loadingVariant="skeleton"
      noData={
        error ? (
          <TableCaption>
            <TableCaption.Error error={error} />
          </TableCaption>
        ) : (
          <TableCaption>
            <TableCaption.Title>No tokens available</TableCaption.Title>
            <TableCaption.Description>
              Generate new tokens and follow the instructions above to enroll MAAS sites.
            </TableCaption.Description>
          </TableCaption>
        )
      }
      pagination={{
        currentPage: page,
        itemsPerPage: size,
        totalItems: data?.total || 0,
        handlePageSizeChange,
        dataContext: "tokens",
        setCurrentPage: setPage,
        isPending,
      }}
      selection={{ rowSelection, setRowSelection }}
      variant="full-height"
    />
  );
};

export default TokensTable;
