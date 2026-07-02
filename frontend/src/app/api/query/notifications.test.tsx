import type { ReactNode } from "react";

import { ToastNotificationProvider, useToastNotification } from "@canonical/react-components";

import type { AppNotification } from "./notifications";
import { useNotifications, useShowNotificationToasts } from "./notifications";

import { renderHook } from "@/utils/test-utils";

const wrapper = ({ children }: { children: ReactNode }) => (
  <ToastNotificationProvider autoDismissDelay={0}>{children}</ToastNotificationProvider>
);

const notification = (id: number, message = "Test notification"): AppNotification => ({
  id,
  category: "success",
  message,
});

describe("useShowNotificationToasts", () => {
  it("shows a toast for each notification", () => {
    const { result } = renderHook(
      () => {
        useShowNotificationToasts([notification(1), notification(2)]);
        return useToastNotification().notifications;
      },
      { wrapper },
    );

    expect(result.current).toHaveLength(2);
  });

  it("does not re-add notifications when re-rendered with a new array reference", () => {
    // Reproduces the infinite-loop scenario: the caller passes a brand-new
    // array (with the same content) on every render.
    const { result, rerender } = renderHook(
      () => {
        useShowNotificationToasts([notification(1)]);
        return useToastNotification().notifications;
      },
      { wrapper },
    );

    expect(result.current).toHaveLength(1);

    rerender();
    rerender();

    expect(result.current).toHaveLength(1);
  });

  it("shows newly added notifications without duplicating existing ones", () => {
    const { result, rerender } = renderHook(
      ({ items }: { items: AppNotification[] }) => {
        useShowNotificationToasts(items);
        return useToastNotification().notifications;
      },
      { wrapper, initialProps: { items: [notification(1)] } },
    );

    expect(result.current).toHaveLength(1);

    rerender({ items: [notification(1), notification(2)] });

    expect(result.current).toHaveLength(2);
  });
});

describe("useNotifications", () => {
  it("does not surface any toasts while the back-end endpoint is unavailable", () => {
    const { result } = renderHook(
      () => {
        useNotifications();
        return useToastNotification().notifications;
      },
      { wrapper },
    );

    expect(result.current).toHaveLength(0);
  });
});
