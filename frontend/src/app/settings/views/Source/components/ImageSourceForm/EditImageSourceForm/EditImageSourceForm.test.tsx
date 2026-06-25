import { setupServer } from "msw/node";

import EditImageSourceForm from "./EditImageSourceForm";

import { BootSourceContext } from "@/app/context/BootSourceContext";
import { imageSourceResolvers, mockImageSources } from "@/testing/resolvers/imageSources";
import { render, screen, userEvent, waitFor } from "@/utils/test-utils";

const mockServer = setupServer(
  imageSourceResolvers.getImageSource.handler(),
  imageSourceResolvers.updateImageSource.handler(),
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

const renderEditForm = () => {
  return render(
    <BootSourceContext.Provider value={{ selected: mockImageSources[1].id, setSelected: jest.fn() }}>
      <EditImageSourceForm />
    </BootSourceContext.Provider>,
  );
};

it("shows the source's URL in the form title", async () => {
  renderEditForm();

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: `Edit ${mockImageSources[1].url}` })).toBeInTheDocument();
  });
});

it("pre-fills the form with the source's details", async () => {
  renderEditForm();

  await waitFor(() => {
    expect(screen.getByRole("textbox", { name: "GPG key" })).toHaveValue(mockImageSources[1].keyring);
  });
  expect(screen.getByRole("checkbox", { name: "Automatically sync images" })).toBeChecked(); // sync interval is > 0 on this boot source
  expect(screen.getByRole("textbox", { name: "Priority" })).toHaveValue(mockImageSources[1].priority.toString());
});

it("does not show the URL", async () => {
  renderEditForm();

  expect(screen.queryByRole("textbox", { name: "URL" })).not.toBeInTheDocument();
});

it("enables the submit button after a field has changed", async () => {
  renderEditForm();

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Save" })).toBeAriaDisabled();
  });

  await userEvent.click(screen.getByRole("checkbox", { name: "Automatically sync images" }));

  expect(screen.getByRole("button", { name: "Save" })).not.toBeAriaDisabled();
});

it.todo("shows an error message when submission fails");
