import RemoveButton from "./RemoveButton";

import { render, screen, userEvent } from "@/utils/test-utils";

it("can render with default options", () => {
  render(<RemoveButton />);
  expect(screen.getByRole("button", { name: "Remove" })).toBeInTheDocument();
});

it("can display a custom label", () => {
  render(<RemoveButton label="Be gone!" />);
  expect(screen.getByRole("button", { name: "Be gone!" })).toBeInTheDocument();
});

it("can be disabled", () => {
  const { rerender } = render(<RemoveButton />);
  expect(screen.getByRole("button", { name: "Remove" })).not.toBeAriaDisabled();

  rerender(<RemoveButton disabled />);
  expect(screen.getByRole("button", { name: "Remove" })).toBeAriaDisabled();
});

it("can show the 'delete' icon", () => {
  render(<RemoveButton showDeleteIcon />);
  expect(screen.getByRole("button", { name: "Remove" }).firstChild).toHaveClass("p-icon--delete");
});

it("can call a provided function on click", async () => {
  const onClick = vi.fn();
  render(<RemoveButton onClick={onClick} />);
  await userEvent.click(screen.getByRole("button", { name: "Remove" }));
  expect(onClick).toHaveBeenCalled();
});

it("can have different types", () => {
  const { rerender } = render(<RemoveButton />);
  expect(screen.getByRole("button", { name: "Remove" })).not.toHaveAttribute("type");

  rerender(<RemoveButton type="button" />);
  expect(screen.getByRole("button", { name: "Remove" })).toHaveAttribute("type", "button");

  rerender(<RemoveButton type="reset" />);
  expect(screen.getByRole("button", { name: "Remove" })).toHaveAttribute("type", "reset");

  rerender(<RemoveButton type="submit" />);
  expect(screen.getByRole("button", { name: "Remove" })).toHaveAttribute("type", "submit");
});
