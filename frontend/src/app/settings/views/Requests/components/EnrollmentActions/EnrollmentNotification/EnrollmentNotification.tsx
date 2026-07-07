import { Notification } from "@canonical/react-components";
import pluralize from "pluralize";

import type { PendingSitesPostRequest } from "@/app/apiclient";
import { useNavigate } from "@/utils/router";

const EnrollmentNotification = ({ accept, ids }: Partial<PendingSitesPostRequest>) => {
  const navigate = useNavigate();

  return (
    <Notification
      actions={[{ label: "Go to Sites", onClick: () => navigate("/sites") }]}
      role="alert"
      severity="information"
      title={accept ? "Accepted" : "Denied"}
    >
      {accept ? "Accepted" : "Denied"} enrollment request for {pluralize("MAAS sites", ids?.length, true)}.{" "}
      {accept ? "See more data of this site in the Sites page." : null}
    </Notification>
  );
};

export default EnrollmentNotification;
