import type { Dispatch, SetStateAction } from "react";

import { ContentSection, GenericTable } from "@canonical/maas-react-components";
import type { SortingState } from "@tanstack/react-table";
import useLocalStorageState from "use-local-storage-state";

import type { UseSitesResult } from "@/app/api/query/sites";
import type { SitesGetResponse } from "@/app/apiclient";
import TableCaption from "@/app/base/components/TableCaption/TableCaption";
import { useAppLayoutContext } from "@/app/context";
import { useRowSelection } from "@/app/context/RowSelectionContext/RowSelectionContext";
import { useSiteDetailsContext } from "@/app/context/SiteDetailsContext";
import NoSites from "@/app/sites/components/NoSites";
import SitesTableControls from "@/app/sites/components/SitesTable/SitesTableControls/SitesTableControls";
import useSitesTableColumns from "@/app/sites/components/SitesTable/useSitesTableColumns/useSitesTableColumns";
import { isDev } from "@/constants";

export type Site = SitesGetResponse["items"][number];

const SitesTable = ({
  data,
  isPending,
  error,
  searchText,
  setSearchText,
  paginationProps,
  sorting,
  setSorting,
}: Pick<UseSitesResult, "data" | "error" | "isPending"> & {
  searchText: string;
  setSearchText: (text: string) => void;
  paginationProps: {
    currentPage: number;
    itemsPerPage: number;
    totalItems: number;
    handlePageSizeChange: (size: number) => void;
    dataContext: string;
    setCurrentPage: (page: number) => void;
    isPending: boolean;
    pageSizes?: number[];
  };
  sorting: SortingState;
  setSorting: Dispatch<SetStateAction<SortingState>>;
}) => {
  const [columnVisibility, setColumnVisibility] = useLocalStorageState("sitesTableColumnVisibility", {
    defaultValue: {},
  });
  const { rowSelection, setRowSelection } = useRowSelection("sites", {
    clearOnUnmount: true,
    currentPage: paginationProps.currentPage,
    pageSize: paginationProps.itemsPerPage,
  });
  const { setSelected: setSiteId } = useSiteDetailsContext();
  const { setSidebar } = useAppLayoutContext();

  const columns = useSitesTableColumns({ setRowSelection, setSiteId, setSidebar });

  return (
    <ContentSection>
      <ContentSection.Header>
        <SitesTableControls
          isPending={isPending}
          searchText={searchText}
          setSearchText={setSearchText}
          totalSites={data?.total ?? null}
        />
      </ContentSection.Header>
      <GenericTable
        aria-label="Sites table"
        className="sites-table"
        columnVisibility={{ columnVisibility, setColumnVisibility }}
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
            <NoSites />
          )
        }
        pagination={paginationProps}
        selection={{
          rowSelection,
          setRowSelection,
          rowSelectionLabelKey: "name",
        }}
        setSorting={setSorting}
        sorting={sorting}
        variant="full-height"
      />
    </ContentSection>
  );
};

export default SitesTable;
