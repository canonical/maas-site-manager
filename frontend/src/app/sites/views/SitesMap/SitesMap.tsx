import { useState } from "react";

import { ContentSection } from "@canonical/maas-react-components";

import { useSitesCoordinates } from "@/app/api/query/sites";
import SitesTableControls from "@/app/sites/components/SitesTable/SitesTableControls/SitesTableControls";
import Map from "@/app/sites/views/SitesMap/components/Map";
import SitesHiddenButton from "@/app/sites/views/SitesMap/components/Map/SitesHiddenButton/SitesHiddenButton";
import { formatSiteMarker } from "@/utils";

const SitesMap = () => {
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const { data, isPending } = useSitesCoordinates();

  if (isFirstVisit) {
    setIsFirstVisit(false);
  }

  return (
    <ContentSection className="sites-map">
      <ContentSection.Header className="sites-map__controls-wrapper">
        <SitesTableControls isPending={isPending} totalSites={data?.length ?? null} />
      </ContentSection.Header>
      <section aria-label="sites map">
        {/* Make sure to  filter out sites without coordinates, otherwise they get rendered at 0,0 */}
        <Map markers={data?.filter((site) => site.coordinates).map?.(formatSiteMarker) ?? null} />
      </section>
      {data?.some((site) => site.coordinates === null) ? <SitesHiddenButton /> : null}
    </ContentSection>
  );
};

export default SitesMap;
