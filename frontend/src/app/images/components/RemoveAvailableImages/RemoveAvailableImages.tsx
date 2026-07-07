import type { ReactElement } from "react";

import { ContentSection, useSidePanel } from "@canonical/maas-react-components";
import { Button, Notification } from "@canonical/react-components";
import type { RowSelectionState } from "@tanstack/react-table";
import pluralize from "pluralize";

import { useDeleteCustomImage, useRemoveImagesFromSelection } from "@/app/api/query/images";
import { useRowSelection } from "@/app/context";

const getUpstreamAndCustomImageIds = (rowSelection: RowSelectionState) => {
  const upstreamImages = Object.keys(rowSelection).filter((key) => !key.startsWith("custom-"));
  const customImages = Object.keys(rowSelection).filter((key) => key.startsWith("custom-"));
  return {
    upstreamImageIds: upstreamImages.map((id) => Number(id)),
    customImageIds: customImages.map((id) => Number(id.split("-")[1])),
  };
};

export const RemoveAvailableImages = (): ReactElement => {
  const { rowSelection, clearRowSelection } = useRowSelection("images");
  const imagesCount = Object.keys(rowSelection).length;
  const { closeSidePanel } = useSidePanel();

  const deleteImagesMutation = useRemoveImagesFromSelection();
  const deleteCustomImagesMutation = useDeleteCustomImage();

  // close sidebar when there are no images selected
  useEffect(() => {
    if (!imagesCount) {
      closeSidePanel();
    }
  }, [imagesCount, closeSidePanel]);

  const imagesCountText = pluralize("available image", imagesCount || 0, true);

  return (
    <ContentSection>
      <ContentSection.Title>Remove {imagesCountText}</ContentSection.Title>
      <ContentSection.Content>
        {deleteImagesMutation.isError ? (
          <Notification severity="negative" title="Remove failed">
            {deleteImagesMutation.error.message}
          </Notification>
        ) : null}
        Are you sure you want to remove <strong>{imagesCountText}</strong> from the selection? This will also affect
        connected MAAS sites.
      </ContentSection.Content>
      <ContentSection.Footer>
        <Button
          appearance="base"
          onClick={() => {
            closeSidePanel();
            clearRowSelection();
          }}
          type="button"
        >
          Cancel
        </Button>
        <Button
          appearance="negative"
          onClick={() => {
            const { upstreamImageIds, customImageIds } = getUpstreamAndCustomImageIds(rowSelection);
            deleteImagesMutation.mutate({ body: { selection_ids: upstreamImageIds } });
            deleteCustomImagesMutation.mutate({ body: { asset_ids: customImageIds } });
            closeSidePanel();
            clearRowSelection();
          }}
          type="button"
        >
          Remove {imagesCountText}
        </Button>
      </ContentSection.Footer>
    </ContentSection>
  );
};

export default RemoveAvailableImages;
