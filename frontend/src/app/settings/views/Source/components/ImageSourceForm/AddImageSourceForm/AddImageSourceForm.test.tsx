import { setupServer } from "msw/node";

import AddImageSourceForm from "./AddImageSourceForm";

import { imageSourceResolvers } from "@/testing/resolvers/imageSources";
import { render, screen, userEvent } from "@/utils/test-utils";

const mockServer = setupServer(
  // Since edit and add are in the same form, creating a new image
  // source still makes a GET call, should separate the forms
  imageSourceResolvers.getImageSource.handler(),
  imageSourceResolvers.createImageSource.handler(),
);

beforeAll(() => {
  mockServer.listen();
});
afterEach(() => {
  mockServer.resetHandlers();
});
afterAll(() => {
  mockServer.close();
});

it("requires the URL field when adding an image source", () => {
  render(<AddImageSourceForm />);

  expect(screen.getByRole("textbox", { name: "URL" })).toBeRequired();
});

it("checks 'Automatically sync images' by defualt", () => {
  render(<AddImageSourceForm />);

  expect(screen.getByRole("checkbox", { name: "Automatically sync images" })).toBeChecked();
});

it("enables the submit button once a valid URL is entered", async () => {
  render(<AddImageSourceForm />);

  expect(screen.getByRole("button", { name: "Add image source" })).toBeAriaDisabled();

  await userEvent.type(screen.getByRole("textbox", { name: "URL" }), "http://example.com");
  await userEvent.tab();

  expect(screen.getByRole("button", { name: "Add image source" })).not.toBeAriaDisabled();
});

it("does not show a caution message for the URL", () => {
  render(<AddImageSourceForm />);

  expect(
    screen.queryByText(
      "Changing to an image server with different images might remove some images from MAAS Site Manager and MAAS.",
    ),
  ).not.toBeInTheDocument();
});

it.todo("shows an error message when submission fails");
