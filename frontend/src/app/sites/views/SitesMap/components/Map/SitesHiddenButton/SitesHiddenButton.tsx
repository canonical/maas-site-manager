import { useSidePanel } from "@canonical/maas-react-components";
import { Button, Icon, Tooltip } from "@canonical/react-components";

import { lazySidePanel } from "@/app/base/sidePanel";

const SitesMissingData = lazySidePanel(() => import("@/app/sites/components/SitesMissingData"));

const MAP_Z_INDEX = 18;

const SitesHiddenButton = () => {
  const { openSidePanel } = useSidePanel();

  return (
    <div className="sites-hidden-btn-container">
      <Tooltip
        message={
          <span className="sites-hidden-message u-align-text--right">
            Some MAAS sites are not shown.
            <br />
            Click to find out more
          </span>
        }
        position="left"
        zIndex={MAP_Z_INDEX + 1}
      >
        <Button
          aria-label="show missing sites"
          className="sites-hidden-btn"
          hasIcon
          onClick={() => {
            openSidePanel({ component: SitesMissingData, title: "Sites with missing data" });
          }}
        >
          <Icon name="warning" />
        </Button>
      </Tooltip>
    </div>
  );
};

export default SitesHiddenButton;
