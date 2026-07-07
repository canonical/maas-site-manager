import { Placeholder, useSidePanel } from "@canonical/maas-react-components";
import { Button, Icon, Tooltip } from "@canonical/react-components";
import type { ColumnDef } from "@tanstack/react-table";

import type { BootSource } from "@/app/apiclient";
import { lazySidePanel } from "@/app/base/sidePanel";
import { useBootSourceContext } from "@/app/context/BootSourceContext";
import { createAccessor } from "@/utils";

const EditCustomImagesSourceForm = lazySidePanel(
  () => import("@/app/settings/views/Source/components/ImageSourceForm/EditCustomImagesSourceForm"),
);
const EditImageSourceForm = lazySidePanel(
  () => import("@/app/settings/views/Source/components/ImageSourceForm/EditImageSourceForm"),
);
const DeleteImageSource = lazySidePanel(() => import("@/app/settings/views/Source/components/DeleteImageSource"));

type BootSourceColumnDef = ColumnDef<BootSource, Partial<BootSource>>;

export const useImageSourceTableColumns = () => {
  const { openSidePanel } = useSidePanel();
  const { setSelected } = useBootSourceContext();

  return useMemo<BootSourceColumnDef[]>(
    () => [
      {
        id: "name",
        enableSorting: true,
        accessorFn: createAccessor("name"),
        accessorKey: "name",
        meta: {
          skeleton: () => <Placeholder variant="block" width="12ch" />,
        },
        cell: ({ getValue }) => {
          const { name } = getValue();
          return <div>{name}</div>;
        },
      },
      {
        id: "url",
        enableSorting: false,
        accessorFn: createAccessor("url"),
        accessorKey: "url",
        meta: {
          skeleton: () => <Placeholder variant="block" width="28ch" />,
        },
        header: "Source",
        cell: ({ getValue }) => {
          const { url } = getValue();
          return (
            <div>
              {url === "custom" ? (
                <>
                  Custom images{" "}
                  <Tooltip
                    message="This row represents the custom images that can be uploaded to MAAS Site Manager. You can edit its priority in this screen."
                    position="right"
                  >
                    <Icon name="help" />
                  </Tooltip>
                </>
              ) : (
                url
              )}
            </div>
          );
        },
      },
      // TODO: re-activate status once missing fields are added
      // {
      //   id: "status",
      //   enableSorting: false,
      //   header: () => <div className="status-text">Status</div>,
      //   accessorFn: createAccessor(["status", "url"]),
      //   accessorKey: "status",
      //   cell: ({ getValue }) => {
      //     const { status, url } = getValue();
      //     if (url !== "custom") {
      //       return (
      //         <div
      //           className={classNames("status-icon", {
      //             "is-lost": BootSourceStatus[status] !== BootSourceStatus.connected,
      //             "is-stable": BootSourceStatus[status] === BootSourceStatus.connected,
      //           })}
      //         >
      //           {BootSourceStatus[status]}
      //         </div>
      //       );
      //     } else {
      //       return <div />;
      //     }
      //   },
      // },
      {
        id: "syncing",
        enableSorting: false,
        accessorFn: createAccessor(["sync_interval", "url"]),
        accessorKey: "syncing",
        meta: {
          skeleton: () => <Placeholder variant="block" width="2ch" />,
        },
        header: "Syncing",
        cell: ({ getValue }) => {
          const { sync_interval, url } = getValue();
          if (url === "custom") {
            return <div />;
          }

          return (
            <div>
              {sync_interval! > 0 ? (
                <Icon name="task-outstanding">Source is syncing</Icon>
              ) : (
                <Icon name="error-grey">Source is not syncing</Icon>
              )}
            </div>
          );
        },
      },
      // TODO: re-activate total_images once missing fields are added
      // {
      //   id: "total_images",
      //   enableSorting: false,
      //   header: () => <div>Number of images</div>,
      //   accessorFn: createAccessor("total_images"),
      //   accessorKey: "total_images",
      //   cell: ({ getValue }) => {
      //     const { total_images } = getValue();
      //     return <div>{total_images}</div>;
      //   },
      // },
      {
        id: "keyring",
        enableSorting: false,
        accessorFn: createAccessor(["keyring", "url"]),
        accessorKey: "keyring",
        meta: {
          skeleton: () => <Placeholder variant="block" width="2ch" />,
        },
        header: "Signed with GPG key",
        cell: ({ getValue }) => {
          const { keyring, url } = getValue();
          if (url === "custom") {
            return <div />;
          } else if (!keyring) {
            return <Icon name="error-grey">Not signed with GPG key</Icon>;
          } else {
            return <Icon name="task-outstanding">Signed with GPG key</Icon>;
          }
        },
      },
      {
        id: "priority",
        enableSorting: true,
        accessorFn: createAccessor("priority"),
        accessorKey: "priority",
        meta: {
          skeleton: () => <Placeholder variant="block" width="4ch" />,
        },
        header: () => (
          <>
            Priority
            <Tooltip
              message="If the same image is available from several sources, the image from the source with the higher priority takes precedence. 1 is the highest priority."
              position="btm-center"
            >
              <Icon name="help" />
            </Tooltip>
          </>
        ),
        cell: ({ getValue }) => {
          const { priority } = getValue();
          return <div>{priority}</div>;
        },
      },
      {
        id: "actions",
        enableSorting: false,
        accessorFn: createAccessor(["url", "id"]),
        accessorKey: "url",
        meta: {
          skeleton: () => (
            <div>
              <Placeholder variant="block" width="2ch" />
              <Placeholder variant="block" width="2ch" />
            </div>
          ),
        },
        header: "Actions",
        cell: ({ getValue }) => {
          const { url, id } = getValue();
          return (
            <div>
              <Button
                appearance="base"
                aria-label="Edit image source"
                className="is-dense u-table-cell-padding-overlap"
                // TODO: enable this once side panel is available https://warthogs.atlassian.net/browse/MAASENG-4381
                onClick={() => {
                  setSelected(id!);
                  if (url === "custom") {
                    openSidePanel({ component: EditCustomImagesSourceForm, title: "Edit custom images" });
                  } else {
                    openSidePanel({ component: EditImageSourceForm, title: "Edit image source" });
                  }
                }}
              >
                <Icon name="edit" />
              </Button>
              {url !== "custom" && (
                <Button
                  appearance="base"
                  aria-label="Delete image source"
                  className="is-dense u-table-cell-padding-overlap"
                  onClick={() => {
                    setSelected(id!);
                    openSidePanel({ component: DeleteImageSource, title: "Delete image source" });
                  }}
                >
                  <Icon name="delete" />
                </Button>
              )}
            </div>
          );
        },
      },
    ],
    [openSidePanel, setSelected],
  );
};
