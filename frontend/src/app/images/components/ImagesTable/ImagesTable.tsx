import type { ReactElement } from "react";

import { GenericTable } from "@canonical/maas-react-components";

import useImagesTableColumns from "./useImagesTableColumns";
import { filterCells, filterHeaders } from "./useImagesTableColumns/useImagesTableColumns";

import { useSelectedImages } from "@/app/api/query/images";
import type { SelectedImage } from "@/app/apiclient";
import { useRowSelection } from "@/app/context";
import { isDev } from "@/constants";

export type ImageWithId = SelectedImage & { id: number | string };

const generateData = (selectedImages: SelectedImage[]): ImageWithId[] => {
  return selectedImages.map(
    (image): ImageWithId => ({
      ...image,
      id: image.selection_id ?? `custom-${image.custom_image_id}`,
    }),
  );
};

export const ImagesTable = (): ReactElement => {
  const { rowSelection, setRowSelection } = useRowSelection("images", { clearOnUnmount: true });
  const selectedImages = useSelectedImages();

  const columns = useImagesTableColumns();
  const data = selectedImages.data?.items ? generateData(selectedImages.data.items) : [];

  return (
    <GenericTable
      aria-label="images"
      className="images-table"
      columns={columns}
      data={data}
      debug={isDev}
      filterCells={filterCells}
      filterHeaders={filterHeaders}
      groupBy={["os"]}
      isLoading={selectedImages.isPending}
      loadingVariant="skeleton"
      noData="No images found."
      pinGroup={[{ value: "ubuntu", isTop: true }]}
      selection={{
        rowSelection,
        setRowSelection,
      }}
      showChevron
      sorting={[{ id: "release", desc: true }]}
    />
  );
};

export default ImagesTable;
