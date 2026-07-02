import type { ReactElement } from "react";

import { AppStatus, Button, Icon, ICONS, useToastNotification } from "@canonical/react-components";
import classNames from "classnames";

import packageInfo from "../../../../../package.json";

import { useNotifications } from "@/app/api/query/notifications";

/**
 * The severity icons shown in the notification toggle, in display order. The
 * severities match the keys of `countBySeverity` from `useToastNotification`.
 */
const SEVERITY_ICONS = [
  { severity: "positive", icon: ICONS.success },
  { severity: "caution", icon: ICONS.warning },
  { severity: "negative", icon: ICONS.error },
  { severity: "information", icon: ICONS.information },
] as const;

/**
 * The application status bar. It sits in the Vanilla application layout's
 * `.l-status` area and hosts the toast notification center: a toggle that opens
 * the list of active notifications.
 */
const StatusBar = (): ReactElement => {
  const { notifications, countBySeverity, isListView, toggleListView } = useToastNotification();

  // Surface any back-end notifications as toasts. This is a no-op until the
  // back-end notifications endpoint is available (see useNotifications).
  useNotifications();

  const hasNotifications = notifications.length > 0;
  const notificationIcons = SEVERITY_ICONS.filter(({ severity }) => countBySeverity[severity]).map(
    ({ severity, icon }) => <Icon key={severity} name={icon} />,
  );

  return (
    <AppStatus>
      <p className="status-bar__version u-text--muted">MAAS Site Manager {packageInfo.version}</p>
      {hasNotifications ? (
        <Button
          aria-label="Expand notifications list"
          className={classNames("status-bar__notifications-toggle", { "is-active": isListView })}
          onClick={toggleListView}
          type="button"
        >
          {notificationIcons}
          <span className="status-bar__notifications-count">{notifications.length}</span>
          <Icon name={isListView ? ICONS.chevronDown : ICONS.chevronUp} />
        </Button>
      ) : null}
    </AppStatus>
  );
};

export default StatusBar;
