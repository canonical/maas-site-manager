import { ContentSection, MainToolbar } from "@canonical/maas-react-components";
import { Button } from "@canonical/react-components";

import ImageSourceListTable from "./components/ImageSourceListTable";

import { useImageSources } from "@/app/api/query/imageSources";
import { useAppLayoutContext } from "@/app/context";

const ImageSourceList = () => {
  const { setSidebar } = useAppLayoutContext();
  const { data, error, isPending } = useImageSources();

  return (
    <ContentSection>
      <ContentSection.Header>
        <MainToolbar>
          <MainToolbar.Title>Source</MainToolbar.Title>
          <MainToolbar.Controls>
            <Button
              appearance="positive"
              onClick={() => {
                setSidebar("addBootSource");
              }}
            >
              Add image source
            </Button>
          </MainToolbar.Controls>
        </MainToolbar>
      </ContentSection.Header>
      <ContentSection.Content>
        <ImageSourceListTable data={data.items} error={error} isPending={isPending} />
      </ContentSection.Content>
    </ContentSection>
  );
};

export default ImageSourceList;
