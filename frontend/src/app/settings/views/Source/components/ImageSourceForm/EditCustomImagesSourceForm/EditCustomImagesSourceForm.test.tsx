import { setupServer } from "msw/node";

import EditCustomImagesSourceForm from "./EditCustomImagesSourceForm";

import { AppLayoutContext } from "@/app/context";
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

const renderForm = () => {
  return render(
    <BootSourceContext.Provider value={{ selected: mockImageSources[0].id, setSelected: jest.fn() }}>
      <EditCustomImagesSourceForm />
    </BootSourceContext.Provider>,
  );
};

it("pre-fills the priority field with the source's priority", async () => {
  renderForm();

  await waitFor(() => {
    expect(screen.getByRole("textbox", { name: "Priority" })).toHaveValue(mockImageSources[0].priority.toString());
  });
});

it("requires the priority field", async () => {
  renderForm();

  await waitFor(() => {
    expect(screen.getByRole("textbox", { name: "Priority" })).toBeRequired();
  });
});

it("enables the submit button when a valid priority is entered", async () => {
  renderForm();

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Save" })).toBeAriaDisabled();
  });

  const priorityInput = screen.getByRole("textbox", { name: "Priority" });
  await userEvent.clear(priorityInput);
  await userEvent.type(priorityInput, "100");

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Save" })).not.toBeAriaDisabled();
  });
});

it("closes the side panel and resets selected source when 'Cancel' is clicked", async () => {
  const setSelected = vi.fn();
  const setSidebar = vi.fn();

  render(
    <AppLayoutContext.Provider value={{ sidebar: null, setSidebar, previousSidebar: null }}>
      <BootSourceContext.Provider value={{ selected: mockImageSources[0].id, setSelected }}>
        <EditCustomImagesSourceForm />
      </BootSourceContext.Provider>
    </AppLayoutContext.Provider>,
  );

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });
  await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

  await waitFor(() => {
    expect(setSelected).toHaveBeenCalledWith(null);
  });
  await waitFor(() => {
    expect(setSidebar).toHaveBeenCalledWith(null);
  });
});

it.todo("shows an error message when submission fails");
