import type { MenuLink } from "@canonical/react-components";
import { ContextualMenu } from "@canonical/react-components";

import {
  useAddImagesToSelection,
  useGetAlternativesForImage,
  useRemoveImagesFromSelection,
} from "@/app/api/query/images";
import type { SelectedImage } from "@/app/apiclient";

const ChangeSourceDropdown = ({ image }: { image: SelectedImage }) => {
  const [isOpen, setIsOpen] = useState(false);
  const getAlternativeImages = useGetAlternativesForImage(
    {
      query: { os: image.os, release: image.release, arch: image.arch },
    },
    isOpen,
  );
  const deleteImagesMutation = useRemoveImagesFromSelection();
  const addImagesToSelection = useAddImagesToSelection();

  const alternativeImages = getAlternativeImages.data?.items ?? [];

  return (
    <div>
      <span>{image.boot_source_name}</span>
      {!image.custom_image_id ? (
        <ContextualMenu
          className="p-table-menu"
          hasToggleIcon
          links={[
            "Change source:",
            ...alternativeImages.map((alternative): MenuLink => ({
              disabled: alternative.id === image.boot_source_id,
              children: alternative.name,
              onClick: () => {
                deleteImagesMutation.mutateAsync({ body: { selection_ids: [image.selection_id!] } }).then(() => {
                  addImagesToSelection.mutate({ body: { selection_ids: [alternative.selection_id] } });
                });
              },
            })),
          ]}
          onToggleMenu={(open: boolean) => {
            setIsOpen(open);
          }}
          position="right"
          toggleAppearance="base"
          toggleClassName="u-no-margin--bottom p-table-menu__toggle"
        />
      ) : null}
    </div>
  );
};

export default ChangeSourceDropdown;
