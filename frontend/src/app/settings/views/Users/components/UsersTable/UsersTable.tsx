import { GenericTable } from "@canonical/maas-react-components";
import type { SortingState } from "@tanstack/react-table";

import type { SortBy, UserSortKey } from "@/app/api/handlers";
import { useUsers } from "@/app/api/query/users";
import TableCaption from "@/app/base/components/TableCaption/TableCaption";
import usePagination from "@/app/base/hooks/usePagination";
import { useUsersTableColumns } from "@/app/settings/views/Users/components/UsersTable/useUsersTableColumns/useUsersTableColumn";
import { isDev } from "@/constants";
import { getSortBy, parseSearchTextToUrlFreeTextSearch } from "@/utils";

const DEFAULT_PAGE_SIZE = 50;

type UsersTableProps = {
  debounceSearchText: string;
};

const UsersTable = ({ debounceSearchText }: UsersTableProps) => {
  const { page, debouncedPage, size, handlePageSizeChange, setPage } = usePagination(DEFAULT_PAGE_SIZE);

  const [sorting, setSorting] = useState<SortingState>([]);
  const sortBy = getSortBy(sorting) as SortBy<UserSortKey>;

  const { data, error, isPending } = useUsers({
    query: {
      page: debouncedPage,
      size,
      sort_by: sortBy,
      search_text: parseSearchTextToUrlFreeTextSearch(debounceSearchText),
    },
  });

  const columns = useUsersTableColumns();

  useEffect(() => {
    setPage(1);
  }, [debounceSearchText, setPage]);

  return (
    <GenericTable
      aria-label="Users list"
      className="users-table"
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
          "No users found."
        )
      }
      pagination={{
        currentPage: page,
        itemsPerPage: size,
        totalItems: data?.total || 0,
        handlePageSizeChange,
        dataContext: "users",
        setCurrentPage: setPage,
        isPending,
      }}
      setSorting={setSorting}
      sorting={sorting}
      variant="full-height"
    />
  );
};

export default UsersTable;
