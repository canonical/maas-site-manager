import { ExternalLink, useSidePanel } from "@canonical/maas-react-components";
import { Button, Icon, Notification, Spinner } from "@canonical/react-components";
import classNames from "classnames";
import get from "lodash/get";

import { useSite } from "@/app/api/query/sites";
import ErrorMessage from "@/app/base/components/ErrorMessage";
import LocalTime from "@/app/base/components/LocalTime/LocalTime";
import RemoveButton from "@/app/base/components/RemoveButton";
import { lazySidePanel, type ReturnablePanelProps } from "@/app/base/sidePanel";
import { useRowSelection } from "@/app/context";
import type { SiteDetailsContextValue } from "@/app/context/SiteDetailsContext";
import { useSiteDetailsContext } from "@/app/context/SiteDetailsContext";
import {
  connectionIcons,
  connectionLabels,
  getLastSeenText,
} from "@/app/sites/components/SitesTable/ConnectionInfo/ConnectionInfo";
import { getCountryName } from "@/utils";

const EditSite = lazySidePanel(() => import("@/app/sites/components/EditSite"));
const RemoveSites = lazySidePanel(() => import("@/app/sites/components/RemoveSites"));
const SiteDetailsPanel = lazySidePanel(() => import("@/app/sites/components/SiteDetails"));

const SiteDetailsContent = ({ id }: { id: NonNullable<SiteDetailsContextValue["selected"]> }) => {
  const { data: site, error, isPending } = useSite({ path: { id } });
  const { openSidePanel, closeSidePanel } = useSidePanel();
  const { setRowSelection } = useRowSelection("sites");
  const stats = site?.stats;

  const reopenSiteDetails = () => {
    openSidePanel({ component: SiteDetailsPanel, title: "Site details" });
  };

  useEffect(() => {
    const marker = document.getElementById(`site-marker-${id}`);
    if (marker) {
      marker.classList.add("site-marker--active");
    }

    // remove marker hover style on unmount
    return () => {
      const marker = document.getElementById(`site-marker-${id}`);
      if (marker) {
        marker.classList.remove("site-marker--active");
      }
    };
  }, [id]);

  return (
    <div className="site-details">
      <Button
        appearance="base"
        aria-label="Close"
        className="site-details__close-button"
        hasIcon
        onClick={() => {
          closeSidePanel();
        }}
      >
        <Icon name="close" />
      </Button>
      {error ? (
        <Notification severity="negative" title="Error">
          <ErrorMessage error={error} />
        </Notification>
      ) : site ? (
        <>
          <h3 className="p-heading--4 site-details__name">{site.name}</h3>
          {site.url ? <ExternalLink to={site.url}>{site.url}</ExternalLink> : null}
          <table className="site-details__table">
            <tbody>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Status</td>
                <td
                  className={classNames(
                    "site-details__table-item",
                    "connection__text",
                    "status-icon",
                    { "u-text--muted": site.connection_status === "unknown" },
                    get(connectionIcons, site.connection_status),
                  )}
                >
                  {get(connectionLabels, site.connection_status)}
                  <span className="u-text--muted site-details__last-seen">
                    {stats
                      ? getLastSeenText({
                          connection: site.connection_status,
                          lastSeen: stats.last_seen,
                          format: "long",
                        })
                      : null}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Country</td>
                <td className="site-details__table-item">{site.country ? getCountryName(site.country) : null}</td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Administrative region</td>
                <td className="site-details__table-item">{site.state}</td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Address</td>
                <td className="site-details__table-item">{site.address}</td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">City</td>
                <td className="site-details__table-item">{site.city}</td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Postal code</td>
                <td className="site-details__table-item">{site.postal_code}</td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Local time</td>
                <td className="site-details__table-item">
                  {site.timezone ? <LocalTime timezone={site.timezone} /> : null}
                </td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Machines</td>
                <td className="site-details__table-item">{stats?.machines_total}</td>
              </tr>
              <tr>
                <td className="u-text--muted site-details__table-row-label">Machines status</td>
                <td className="site-details__table-item">
                  {stats ? (
                    <span className="site-details__machines-statuses">
                      <i className="p-icon--status-deployed"></i>
                      <span className="site-details__machines-status-count" data-testid="deployed-machines">
                        {stats.machines_deployed}
                      </span>
                      <span>Deployed</span>

                      <i className="p-icon--status-allocated"></i>
                      <span className="site-details__machines-status-count" data-testid="allocated-machines">
                        {stats.machines_allocated}
                      </span>
                      <span>Allocated</span>

                      <i className="p-icon--status-ready"></i>
                      <span className="site-details__machines-status-count" data-testid="ready-machines">
                        {stats.machines_ready}
                      </span>
                      <span>Ready / New</span>

                      <span></span>
                      <span className="site-details__machines-status-count" data-testid="error-machines">
                        {stats.machines_error}
                      </span>
                      <span>Error</span>
                    </span>
                  ) : null}
                </td>
              </tr>
            </tbody>
          </table>
          <hr />
          <span className="u-flex u-flex--justify-end">
            <Button
              appearance="base"
              onClick={() => {
                openSidePanel<ReturnablePanelProps>({
                  component: EditSite,
                  title: "Edit site",
                  props: { onClose: reopenSiteDetails },
                });
              }}
            >
              <Icon name="edit" /> Edit
            </Button>
            <RemoveButton
              onClick={() => {
                setRowSelection({ [site.id]: true });
                openSidePanel<ReturnablePanelProps>({
                  component: RemoveSites,
                  title: "Remove sites",
                  props: { onClose: reopenSiteDetails },
                });
              }}
              showDeleteIcon
            />
          </span>
        </>
      ) : isPending ? (
        <Spinner />
      ) : null}
    </div>
  );
};

const SiteDetails = () => {
  const { selected: siteId } = useSiteDetailsContext();

  return siteId ? <SiteDetailsContent id={siteId} /> : null;
};

export default SiteDetails;
