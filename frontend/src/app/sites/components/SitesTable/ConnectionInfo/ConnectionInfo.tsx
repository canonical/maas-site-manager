import { ExternalLink } from "@canonical/maas-react-components";
import classNames from "classnames";
import get from "lodash/get";

import type { Site, SiteData } from "@/app/apiclient";
import TooltipButton from "@/app/base/components/TooltipButton";
import docsUrls from "@/app/base/docsUrls";
import { formatDistanceToNow } from "@/utils";

export const connectionIcons: Record<Site["connection_status"], string> = {
  stable: "is-stable",
  lost: "is-lost",
  unknown: "is-unknown",
} as const;
export const connectionLabels: Record<Site["connection_status"], string> = {
  stable: "Stable",
  lost: "Lost",
  unknown: "Waiting for first heartbeat",
} as const;

type ConnectionInfoProps = { connection: Site["connection_status"]; lastSeen?: SiteData["last_seen"] };

export const getLastSeenText = ({
  connection,
  lastSeen,
  format = "long",
}: ConnectionInfoProps & { format: "long" | "short" }) => {
  if (!lastSeen) {
    return null;
  }
  const description = connection === "unknown" ? "since" : "last seen";
  return `${format === "long" ? description : ""} ${formatDistanceToNow(lastSeen)}`;
};

const ConnectionInfo = ({ connection, lastSeen }: ConnectionInfoProps) => {
  return (
    <>
      <TooltipButton
        message={
          connection === "unknown" ? (
            "Haven't received a heartbeat from this site yet"
          ) : connection === "stable" ? (
            "Received a heartbeat in the expected interval of 5 minutes"
          ) : (
            <>
              Haven't received a heartbeat in the expected interval of 5 minutes.
              <br />
              <ExternalLink to={docsUrls.troubleshooting}>
                Check the documentation for troubleshooting steps.
              </ExternalLink>
            </>
          )
        }
        position="btm-center"
      >
        <div className={classNames("connection__text", "status-icon", get(connectionIcons, connection))}>
          {get(connectionLabels, connection)}
        </div>
      </TooltipButton>
      <div className="connection__text u-text--muted">
        <time dateTime={lastSeen}>
          {getLastSeenText({ connection, lastSeen, format: connection === "unknown" ? "long" : "short" })}
        </time>
      </div>
    </>
  );
};

export default ConnectionInfo;
