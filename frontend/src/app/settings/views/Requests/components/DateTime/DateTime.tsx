import * as Sentry from "@sentry/browser";
import { withErrorBoundary } from "react-error-boundary";

import { formatUTCDateString } from "@/utils";
const DateTime = ({ value }: { value: string }) => <time dateTime={value}>{formatUTCDateString(value)}</time>;

const DateTimeWithErrorBoundary = withErrorBoundary(DateTime, {
  fallback: <div>Invalid time value</div>,
  onError(error) {
    Sentry.captureException(new Error("Invalid time value", { cause: error }));
  },
});

export default DateTimeWithErrorBoundary;
