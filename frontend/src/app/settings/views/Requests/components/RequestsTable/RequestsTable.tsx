import { ExternalLink, GenericTable } from "@canonical/maas-react-components";

import { useEnrollmentRequests } from "@/app/api/query/enrollmentRequests";
import TableCaption from "@/app/base/components/TableCaption";
import docsUrls from "@/app/base/docsUrls";
import usePagination from "@/app/base/hooks/usePagination";
import { useRowSelection } from "@/app/context/RowSelectionContext/RowSelectionContext";
import { useRequestsTableColumns } from "@/app/settings/views/Requests/components/RequestsTable/useRequestsTableColumns/useRequestsTableColumns";
import { isDev } from "@/constants";

const DEFAULT_PAGE_SIZE = 50;

const RequestsTable = () => {
  const { page, debouncedPage, size, handlePageSizeChange, setPage } = usePagination(DEFAULT_PAGE_SIZE);
  const { error, data, isPending } = useEnrollmentRequests({
    query: {
      page: debouncedPage,
      size,
    },
  });

  const { rowSelection, setRowSelection } = useRowSelection("requests", {
    clearOnUnmount: true,
    currentPage: page,
    pageSize: size,
  });

  const columns = useRequestsTableColumns();

  return (
    <GenericTable
      aria-label="Requests table"
      className="requests-table"
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
            <TableCaption.Title>No outstanding requests</TableCaption.Title>
            <TableCaption.Description>
              You have to request an enrollment in the site-manager-agent.
              <br />
              <ExternalLink to={docsUrls.enrollmentRequest}>Read more about it in the documentation.</ExternalLink>
            </TableCaption.Description>
          </TableCaption>
        )
      }
      pagination={{
        currentPage: page,
        itemsPerPage: size,
        totalItems: data?.total || 0,
        handlePageSizeChange,
        dataContext: "requests",
        setCurrentPage: setPage,
        isPending,
      }}
      selection={{ rowSelection, setRowSelection }}
      variant="full-height"
    />
  );
};

export default RequestsTable;
