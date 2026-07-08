import { Placeholder } from "@canonical/maas-react-components";
import pluralize from "pluralize";

import type { UseSitesResult } from "@/app/api/query/sites";

const SitesCount = ({
  totalSites,
  isPending,
}: Pick<UseSitesResult, "isPending"> & {
  totalSites: number | null;
}) =>
  isPending ? (
    <Placeholder height="1rem" variant="block" width="10ch" />
  ) : (
    <span>{`${pluralize("MAAS sites", totalSites || 0, !!totalSites)}`}</span>
  );

export default SitesCount;
