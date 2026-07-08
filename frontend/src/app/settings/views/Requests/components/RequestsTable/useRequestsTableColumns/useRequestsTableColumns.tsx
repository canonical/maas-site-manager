import { ExternalLink } from "@canonical/maas-react-components";
import type { ColumnDef } from "@tanstack/react-table";

import type { PendingSite } from "@/app/apiclient";
import DateTime from "@/app/settings/views/Requests/components/DateTime";

type RequestColumnDef = ColumnDef<PendingSite, Partial<PendingSite>>;

export const useRequestsTableColumns = () => {
  return useMemo<RequestColumnDef[]>(
    () => [
      {
        id: "name",
        accessorKey: "name",
        header: "Name",
      },
      {
        id: "url",
        accessorKey: "url",
        header: "URL",
        cell: ({
          row: {
            original: { url },
          },
        }) => <ExternalLink to={url}>{url}</ExternalLink>,
      },
      {
        id: "created",
        accessorKey: "created",
        header: "Time of request (UTC)",
        cell: ({
          row: {
            original: { created },
          },
        }) => <DateTime value={created} />,
      },
    ],
    [],
  );
};
