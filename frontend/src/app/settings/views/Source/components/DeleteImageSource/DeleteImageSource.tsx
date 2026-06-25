import { ContentSection } from "@canonical/maas-react-components";
import { ActionButton, Button, Spinner } from "@canonical/react-components";

import { useDeleteImageSource, useImageSource } from "@/app/api/query/imageSources";
import { useAppLayoutContext } from "@/app/context";
import { useBootSourceContext } from "@/app/context/BootSourceContext";

const DeleteImageSource = () => {
  const { selected: id } = useBootSourceContext();
  const { setSidebar } = useAppLayoutContext();

  const { data: imageSource, isPending } = useImageSource({ path: { id: id! } });
  const deleteImageSource = useDeleteImageSource();

  return (
    <ContentSection>
      {isPending || !imageSource ? (
        <Spinner text="Loading..." />
      ) : (
        <>
          <ContentSection.Title className="p-heading--4">Remove {imageSource?.url}?</ContentSection.Title>
          <ContentSection.Content>
            <p>Are you sure you want to remove {imageSource?.url} as an image source in MAAS Site Manager?</p>
            <p>
              Removing an image source will remove all images that were pulled from this source in MAAS Site Manager and
              all connected MAAS sites.
            </p>
            <hr />
            <div className="u-flex u-flex--justify-end u-padding-top--medium">
              <Button
                appearance="base"
                onClick={() => {
                  setSidebar(null);
                }}
                type="button"
              >
                Cancel
              </Button>
              <ActionButton
                appearance="negative"
                onClick={() => {
                  deleteImageSource.mutate({ path: { id: id! } });
                  setSidebar(null);
                }}
                type="submit"
              >
                Remove image source
              </ActionButton>
            </div>
          </ContentSection.Content>
        </>
      )}
    </ContentSection>
  );
};

export default DeleteImageSource;
