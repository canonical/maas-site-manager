import type { DOMAttributes } from "react";

import { ExternalLink } from "@canonical/maas-react-components";
import { Button, Card, Icon, Notification, Spinner } from "@canonical/react-components";
import classNames from "classnames";
import get from "lodash/get";

import { useSite } from "@/app/api/query/sites";
import type { Site } from "@/app/apiclient";
import ErrorMessage from "@/app/base/components/ErrorMessage/ErrorMessage";
import { useAppLayoutContext } from "@/app/context";
import { useSiteDetailsContext } from "@/app/context/SiteDetailsContext";
import AggregatedStatus from "@/app/sites/components/SitesTable/AggregatedStatus/AggregatedStatus";
import {
  connectionIcons,
  connectionLabels,
  getLastSeenText,
} from "@/app/sites/components/SitesTable/ConnectionInfo/ConnectionInfo";

interface SiteSummaryProps extends DOMAttributes<HTMLElement> {
  id: Site["id"];
}
const SiteSummary = ({ id, ...props }: SiteSummaryProps) => {
  const { data: site, error, isPending } = useSite({ path: { id } });
  const { setSidebar } = useAppLayoutContext();
  const { setSelected: setSiteId } = useSiteDetailsContext();
  const { stats } = site || {};

  const handleMouseOver = () => {
    // keep marker hover style when hovering over site summary
    const marker = document.getElementById(`site-marker-${id}`);
    if (marker) {
      marker.classList.add("site-marker--active");
    }
  };

  useEffect(() => {
    // remove marker hover style on unmount
    return () => {
      const marker = document.getElementById(`site-marker-${id}`);
      if (marker) {
        marker.classList.remove("site-marker--active");
      }
    };
  }, [id]);

  return (
    <Card className="site-summary" onMouseOver={handleMouseOver} title="Site details" {...props}>
      {error ? (
        <Notification severity="negative" title="Error while fetching site">
          <ErrorMessage error={error} />
        </Notification>
      ) : site ? (
        <>
          <div>
            <span className="site-summary__header">
              <h4 className="site-summary__name u-truncate">{site.name}</h4>
              <span>Site ID: {id}</span>
              <Button
                appearance="base"
                className="site-summary__button--edit"
                onClick={() => {
                  setSiteId(id);
                  setSidebar("editSite");
                }}
              >
                <Icon name="edit" /> Edit
              </Button>
            </span>
            {site.url ? <ExternalLink to={site.url}>{site.url}</ExternalLink> : null}
          </div>
          <table className="site-summary__table">
            <tbody>
              <tr>
                <td className="u-text--muted site-summary__table-item">Status</td>
                <td
                  className={classNames(
                    "connection__text",
                    "status-icon",
                    get(connectionIcons, site.connection_status),
                  )}
                >
                  {get(connectionLabels, site.connection_status)}
                  <span className="u-text--muted site-summary__last-seen">
                    {stats
                      ? getLastSeenText({
                          lastSeen: stats.last_seen,
                          connection: site.connection_status,
                          format: "long",
                        })
                      : null}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="u-text--muted site-summary__table-item">Machines</td>
                <td>{stats?.machines_total}</td>
              </tr>
              <tr>
                <td className="u-text--muted site-summary__table-item">Machine status</td>
                <td className="site-summary__table-meter-wrapper">
                  {stats ? <AggregatedStatus hideLabel stats={stats} /> : null}
                </td>
              </tr>
            </tbody>
          </table>
        </>
      ) : isPending ? (
        <Spinner />
      ) : null}
    </Card>
  );
};

export default SiteSummary;
