import * as timezoneMock from "timezone-mock";

import ConnectionInfo, { connectionIcons, connectionLabels } from "./ConnectionInfo";

import { ConnectionStatus } from "@/app/apiclient";
import { connections } from "@/mocks/factories";
import { render, screen } from "@/utils/test-utils";

beforeEach(() => {
  vi.useFakeTimers();
  timezoneMock.register("Etc/GMT");
});

afterEach(() => {
  timezoneMock.unregister();
  vi.useRealTimers();
});

connections.forEach((connection) => {
  it(`displays correct connection status icon and label for ${connection} connection`, async () => {
    const { container } = render(<ConnectionInfo connection={connection} />);
    expect(screen.getByText(connectionLabels[connection])).toBeInTheDocument();

    expect(container.querySelector(".status-icon")).toHaveClass(connectionIcons[connection]);
  });
});

it("displays last seen text relative to local time correctly", () => {
  const date = new Date("2000-01-01T12:00:00Z");
  vi.setSystemTime(date);
  render(<ConnectionInfo connection={connections[0]} lastSeen="2000-01-01T11:58:00Z" />);
  expect(screen.getByText("2 minutes ago")).toBeInTheDocument();
});

it("displays 'waiting for first' text for the unknown status", () => {
  render(<ConnectionInfo connection={ConnectionStatus.UNKNOWN} />);
  expect(screen.getByText(/waiting for first heartbeat/i)).toBeInTheDocument();
});
