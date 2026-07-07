import type { ReactElement } from "react";

import { ContentSection, MainToolbar, useSidePanel } from "@canonical/maas-react-components";
import { Button } from "@canonical/react-components";

import ImagesTable from "../../components/ImagesTable";

import RemoveButton from "@/app/base/components/RemoveButton";
import { lazySidePanel } from "@/app/base/sidePanel";
import { useRowSelection } from "@/app/context";

const RemoveAvailableImages = lazySidePanel(() => import("@/app/images/components/RemoveAvailableImages"));
const AddToAvailableImages = lazySidePanel(() => import("@/app/images/components/AddToAvailableImages"));
const UploadCustomImage = lazySidePanel(() => import("@/app/images/components/UploadCustomImage"));

const ImagesList = (): ReactElement => {
  const { rowSelection } = useRowSelection("images");
  const isDeleteDisabled = Object.keys(rowSelection).length <= 0;
  const { openSidePanel } = useSidePanel();

  return (
    <ContentSection>
      <ContentSection.Header>
        <MainToolbar>
          <MainToolbar.Title>Images</MainToolbar.Title>
          <MainToolbar.Controls>
            <RemoveButton
              disabled={isDeleteDisabled}
              label="Remove available images"
              onClick={() => {
                openSidePanel({ component: RemoveAvailableImages, title: "Remove available images" });
              }}
              type="button"
            />
            <Button
              onClick={() => {
                openSidePanel({ component: AddToAvailableImages, title: "Add to available images" });
              }}
              type="button"
            >
              Add to available images
            </Button>
            <Button
              onClick={() => {
                openSidePanel({ component: UploadCustomImage, title: "Upload custom image" });
              }}
              type="button"
            >
              Upload custom image
            </Button>
          </MainToolbar.Controls>
        </MainToolbar>
      </ContentSection.Header>
      <ContentSection.Content>
        <ImagesTable />
      </ContentSection.Content>
    </ContentSection>
  );
};

export default ImagesList;
