import { ToastNotificationProvider, useToastNotification } from "@canonical/react-components";

import StatusBar from "./StatusBar";

import { render, screen, userEvent } from "@/utils/test-utils";

const ToastTrigger = () => {
  const { success } = useToastNotification();
  return (
    <button onClick={() => success("Test notification")} type="button">
      Fire notification
    </button>
  );
};

const renderStatusBar = (withTrigger = false) =>
  render(
    <ToastNotificationProvider>
      <StatusBar />
      {withTrigger ? <ToastTrigger /> : null}
    </ToastNotificationProvider>,
  );

it("renders the application version", () => {
  renderStatusBar();

  expect(screen.getByText(/MAAS Site Manager/i)).toBeInTheDocument();
});

it("does not render the notifications toggle when there are no notifications", () => {
  renderStatusBar();

  expect(screen.queryByRole("button", { name: /expand notifications list/i })).not.toBeInTheDocument();
});

it("renders the notifications toggle with a count once a notification is added", async () => {
  renderStatusBar(true);

  await userEvent.click(screen.getByRole("button", { name: /fire notification/i }));

  const toggle = await screen.findByRole("button", { name: /expand notifications list/i });
  expect(toggle).toBeInTheDocument();
  expect(toggle).toHaveTextContent("1");
});

it("toggles the notifications list view when the toggle is clicked", async () => {
  renderStatusBar(true);

  await userEvent.click(screen.getByRole("button", { name: /fire notification/i }));

  const toggle = await screen.findByRole("button", { name: /expand notifications list/i });
  expect(toggle).not.toHaveClass("is-active");

  await userEvent.click(toggle);

  expect(screen.getByRole("button", { name: /expand notifications list/i })).toHaveClass("is-active");
});
