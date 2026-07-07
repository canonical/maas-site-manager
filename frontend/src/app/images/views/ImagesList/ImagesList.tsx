import type { ReactElement } from "react";

import { MainToolbar, ContentSection, useSidePanel } from "@canonical/maas-react-components";
import { Button } from "@canonical/react-components";

import ImagesTable from "../../components/ImagesTable";

import RemoveButton from "@/app/base/components/RemoveButton";
import { sidePanels } from "@/app/base/sidePanels";
import { useRowSelection } from "@/app/context";

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
                openSidePanel(sidePanels.removeAvailableImages);
              }}
              type="button"
            />
            <Button
              onClick={() => {
                openSidePanel(sidePanels.addToAvailableImages);
              }}
              type="button"
            >
              Add to available images
            </Button>
            <Button
              onClick={() => {
                openSidePanel(sidePanels.uploadCustomImage);
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
