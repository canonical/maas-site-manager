import { GenericTable } from "@canonical/maas-react-components";

import { useImageSourceTableColumns } from "./useImageSourceTableColumns/useImageSourceTableColumns";

import type { BootSource } from "@/app/apiclient";
import TableCaption from "@/app/base/components/TableCaption";

type ImageSourcesListTableProps = {
  data: BootSource[];
  error: Error | null;
  isPending: boolean;
};

const ImageSourceListTable = ({ data, error, isPending }: ImageSourcesListTableProps) => {
  const columns = useImageSourceTableColumns();

  return (
    <GenericTable
      aria-label="Image source list"
      className="image-source-table"
      columns={columns}
      data={data}
      isLoading={isPending}
      loadingVariant="skeleton"
      noData={
        error ? (
          <TableCaption>
            <TableCaption.Error error={error} />
          </TableCaption>
        ) : (
          "No image sources configured."
        )
      }
    />
  );
};

export default ImageSourceListTable;
