import { useEffect } from "react";

import { useToastNotification } from "@canonical/react-components";

/**
 * The category of a back-end notification. Maps onto a toast notification
 * severity.
 */
export type NotificationCategory = "error" | "info" | "success" | "warning";

/**
 * The shape of a notification coming from the back-end.
 *
 * NOTE: the back-end does not expose a notifications endpoint yet. This type is
 * a placeholder describing the data we expect to receive, so that the mapping to
 * toast notifications is ready to be wired up. Replace it with the generated API
 * client types once the endpoint is available.
 */
export type AppNotification = {
  id: number;
  category: NotificationCategory;
  message: string;
};

type ToastNotificationHelper = ReturnType<typeof useToastNotification>;

/**
 * Build a stable toast notification id from a back-end notification id. Keeping
 * the ids in sync lets us map a dismissed toast back to the notification that
 * needs to be dismissed on the back-end.
 */
export const notificationToToastId = (id: AppNotification["id"]): string => `notification-${id}`;

/**
 * Surface a single back-end notification as a toast notification.
 */
const showNotificationToast = (toast: ToastNotificationHelper, item: AppNotification): void => {
  const id = notificationToToastId(item.id);
  switch (item.category) {
    case "success":
      toast.success(item.message, [], "", id);
      break;
    case "error":
      toast.failure("Error", null, item.message, [], id);
      break;
    case "warning":
      toast.caution(item.message, [], "Warning", id);
      break;
    case "info":
      toast.info(item.message, "", [], id);
      break;
  }
};

/**
 * Bridges back-end notifications to toast notifications.
 *
 * The back-end does not expose a notifications endpoint yet, so `items` is
 * currently an empty placeholder. Once the endpoint is available, fetch the
 * active notifications (e.g. with a generated `useListNotifications` query) and
 * assign them to `items`; each one will then be surfaced as a toast. A matching
 * dismiss handler can be passed to the `ToastNotificationProvider`'s `onDismiss`
 * prop to dismiss notifications on the back-end.
 */
export const useNotifications = (): void => {
  const toast = useToastNotification();

  // TODO(backend): replace with data from the notifications endpoint, e.g.
  //   const { data } = useListNotifications({ query: { only_active: true } });
  //   const items = data?.items ?? [];
  const items: AppNotification[] = [];

  useEffect(() => {
    items.forEach((item) => {
      showNotificationToast(toast, item);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);
};
