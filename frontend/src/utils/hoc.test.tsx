/* eslint-disable no-console */
import { expect, vi } from "vitest";

import { lazyWithErrorBoundary } from "./hoc";

import { render, screen } from "@/utils/test-utils";

// Component that throws an error during render for testing error boundary
const ThrowError = () => {
  throw new Error("Custom error message");
};

it("renders the error boundary on component load failure", async () => {
  // Suppress console errors for this test
  const originalConsoleError = console.error;
  console.error = vi.fn();

  const LazyComponent = lazyWithErrorBoundary(() => Promise.resolve({ default: ThrowError }));
  render(<LazyComponent />);
  const errorElement = await screen.findByText(/Custom error message/i);
  expect(errorElement).toBeInTheDocument();

  console.error = originalConsoleError;
});
