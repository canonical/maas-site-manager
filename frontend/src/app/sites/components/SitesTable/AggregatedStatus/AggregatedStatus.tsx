import { Meter, meterColor as color } from "@canonical/maas-react-components";

import type { Site } from "@/app/apiclient";
import Popover from "@/app/base/components/Popover/Popover";

const AggregatedStatus = ({ stats, hideLabel }: { stats: NonNullable<Site["stats"]>; hideLabel?: boolean }) => {
  const { machines_deployed, machines_allocated, machines_ready, machines_error, machines_total } = stats;
  return (
    <>
      <div>
        <Popover
          content={
            <>
              <div className="p-popover__primary">
                <div className="u-vertically-center">
                  <i className="p-icon--status-deployed"></i>
                </div>
                <div className="u-align--right" data-testid="deployed">
                  {machines_deployed}
                </div>
                <div>Deployed</div>
                <div className="u-vertically-center">
                  <i className="p-icon--status-allocated"></i>
                </div>
                <div className="u-align--right" data-testid="allocated">
                  {machines_allocated}
                </div>
                <div>Allocated</div>
                <div className="u-vertically-center">
                  <i className="p-icon--status-ready"></i>
                </div>
                <div className="u-align--right" data-testid="ready">
                  {machines_ready}
                </div>
                <div>Ready / New</div>
              </div>
              <div className="p-popover__secondary">
                <div />
                <div className="u-align--right" data-testid="error">
                  {machines_error}
                </div>
                <div>Error</div>
              </div>
            </>
          }
        >
          <Meter
            aria-label={`${machines_deployed} of ${machines_total} deployed`}
            className="u-no-margin--bottom u-no-padding"
            data={[
              { color: "black", value: machines_deployed },
              { color: color.link, value: machines_allocated },
              { color: color.linkFaded, value: machines_ready },
            ]}
            size="small"
          >
            {hideLabel ? undefined : (
              <Meter.Label className="u-text--muted">
                {machines_deployed} of {machines_total} deployed
              </Meter.Label>
            )}
          </Meter>
        </Popover>
      </div>
    </>
  );
};

export default AggregatedStatus;
