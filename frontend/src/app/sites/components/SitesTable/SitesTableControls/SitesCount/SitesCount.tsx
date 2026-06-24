import pluralize from "pluralize";

import type { UseSitesResult } from "@/app/api/query/sites";
import Placeholder from "@/app/base/components/Placeholder";

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
