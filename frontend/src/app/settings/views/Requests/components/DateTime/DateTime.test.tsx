/* eslint-disable no-console */
import * as timezoneMock from "timezone-mock";

import DateTime from "./DateTime";

import { render, screen } from "@/utils/test-utils";

beforeEach(() => {
  vi.useFakeTimers();
  timezoneMock.register("Etc/GMT+8");
});

afterEach(() => {
  timezoneMock.unregister();
  vi.useRealTimers();
});

it("renders time in a correct format", () => {
  render(<DateTime value="2023-01-23T09:36:00.000Z" />);
  expect(screen.getByText("2023-01-23 09:36")).toBeInTheDocument();
});

it("renders invalid time fallback value correctly", () => {
  // Suppress console errors for this test
  const originalConsoleError = console.error;
  console.error = vi.fn();

  render(<DateTime value="" />);
  expect(screen.getByText("Invalid time value")).toBeInTheDocument();

  console.error = originalConsoleError;
});
