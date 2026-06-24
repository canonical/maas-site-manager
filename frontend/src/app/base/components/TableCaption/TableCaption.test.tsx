import TableCaption from "./TableCaption";

import { render, screen } from "@/utils/test-utils";

test("TableCaption.Title displays title", () => {
  render(<TableCaption.Title>Test Title</TableCaption.Title>);
  expect(screen.getByText("Test Title")).toBeInTheDocument();
});

test("TableCaption.Title displays title", () => {
  render(<TableCaption.Description>Test description</TableCaption.Description>);
  expect(screen.getByText("Test description")).toBeInTheDocument();
});

test("TableCaption.Error renders error message", () => {
  const error = new Error("Test error message");
  render(<TableCaption.Error error={error} />);
  expect(screen.getByText("Test error message")).toBeInTheDocument();
});
