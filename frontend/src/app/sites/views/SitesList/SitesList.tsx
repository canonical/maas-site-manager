import { useEffect, useState } from "react";

import type { SortingState } from "@tanstack/react-table";

import type { SitesSortKey, SortBy } from "@/app/api/handlers";
import { useSites } from "@/app/api/query/sites";
import useDebounce from "@/app/base/hooks/useDebouncedValue";
import usePagination from "@/app/base/hooks/usePagination";
import SitesTable from "@/app/sites/components/SitesTable";
import { getSortBy } from "@/utils";
import { useSearchParams, useNavigate } from "@/utils/router";

const DEFAULT_PAGE_SIZE = 50;

const SitesList = () => {
  const { page, debouncedPage, size, handlePageSizeChange, setPage } = usePagination(DEFAULT_PAGE_SIZE);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const [searchText, setSearchText] = useState(searchParams.get("q") || "");
  const debounceSearchText = useDebounce(searchText);
  const [sorting, setSorting] = useState<SortingState>([]);
  const sortBy = getSortBy(sorting) as SortBy<SitesSortKey>;

  const { error, data, isPending } = useSites({
    query: {
      page: debouncedPage,
      size,
      sort_by: sortBy,
      q: searchParams.get("q"),
    },
  });

  useEffect(() => {
    setPage(1);
  }, [searchText, setPage]);

  useEffect(() => {
    if (isFirstVisit) {
      setIsFirstVisit(false);
      return;
    }

    if (!debounceSearchText) {
      navigate("/sites/list");
      return;
    }
    const params = { q: debounceSearchText };
    const urlParams = new URLSearchParams(params);
    navigate({ pathname: "/sites/list", search: urlParams.toString() });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounceSearchText, navigate]);

  return (
    <SitesTable
      data={data}
      error={error}
      isPending={isPending}
      paginationProps={{
        currentPage: page,
        dataContext: "MAAS Sites",
        handlePageSizeChange,
        isPending,
        itemsPerPage: size,
        setCurrentPage: setPage,
        totalItems: data?.total || 0,
      }}
      searchText={searchText}
      setSearchText={setSearchText}
      setSorting={setSorting}
      sorting={sorting}
    />
  );
};

export default SitesList;
