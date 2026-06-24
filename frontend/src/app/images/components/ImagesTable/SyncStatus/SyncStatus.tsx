import { Placeholder } from "@canonical/maas-react-components";
import { Icon } from "@canonical/react-components";

import type { SelectedImage } from "@/app/apiclient";

const SyncedStatus = () => {
  return (
    <div>
      <Icon aria-hidden="true" name="success" /> Synced to MAAS sites
    </div>
  );
};

const QueuedStatus = () => (
  <div>
    <Icon aria-hidden="true" className="u-animation--spin" name="spinner" /> Queued for download
  </div>
);

const DownloadingStatus = ({ image }: { image: SelectedImage }) => (
  <div>
    <Icon aria-hidden="true" className="u-animation--spin" name="spinner" /> Downloading{" "}
    {(image.downloaded / image.size) * 100}%
  </div>
);

const syncStatusComponents = {
  synced: SyncedStatus,
  queued: QueuedStatus,
  downloading: DownloadingStatus,
};

type Status = keyof typeof syncStatusComponents;
type SyncStatusProps = { status: Status; image: SelectedImage };
const SyncStatus = ({ status, image }: SyncStatusProps) => {
  const StatusComponent = syncStatusComponents[status];
  return StatusComponent ? <StatusComponent image={image} /> : null;
};

const getImageStatus = (image: SelectedImage): Status | null => {
  if (image.downloaded === 0) {
    return "queued";
  } else if (image.downloaded < image.size) {
    return "downloading";
  } else if (image.downloaded === image.size) {
    return "synced";
  }
  return null;
};

const SyncStatusContainer = ({ image }: { image: SelectedImage }) => {
  const status = getImageStatus(image);
  return status ? <SyncStatus image={image} status={status} /> : <Placeholder isPending />;
};

export default SyncStatusContainer;
