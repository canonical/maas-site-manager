import { ContentSection, MainToolbar, useSidePanel } from "@canonical/maas-react-components";
import { Button } from "@canonical/react-components";

import ImageSourceListTable from "./components/ImageSourceListTable";

import { useImageSources } from "@/app/api/query/imageSources";
import { lazySidePanel } from "@/app/base/sidePanel";

const AddImageSourceForm = lazySidePanel(
  () => import("@/app/settings/views/Source/components/ImageSourceForm/AddImageSourceForm"),
);

const ImageSourceList = () => {
  const { openSidePanel } = useSidePanel();
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
                openSidePanel({ component: AddImageSourceForm, title: "Add image source" });
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
