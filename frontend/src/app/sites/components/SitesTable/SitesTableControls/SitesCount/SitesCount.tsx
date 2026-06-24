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
    <Placeholder isPending={isPending} text="xx" />
  ) : (
    <span>{`${pluralize("MAAS sites", totalSites || 0, !!totalSites)}`}</span>
  );

export default SitesCount;
