import ImageSourceList from "./ImageSourceList";

import { renderWithMemoryRouter, screen } from "@/utils/test-utils";

it("renders the image source list", () => {
  renderWithMemoryRouter(<ImageSourceList />);

  expect(screen.getByRole("heading", { name: /Source/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Add image source/i })).toBeInTheDocument();
  expect(screen.getByRole("table", { name: /Image source list/i })).toBeInTheDocument();
});

it.todo("opens the 'Add image source' side panel when 'Add image source' is clicked");

it.todo("opens the 'Edit image source' side panel when 'Edit image source' is clicked");

it.todo("opens the 'Delete image source' modal when 'Delete image source' is clicked");
