import { setupServer } from "msw/node";

import ImageSourceForm from "./ImageSourceForm";

import { AppLayoutContext } from "@/app/context";
import { BootSourceContext } from "@/app/context/BootSourceContext";
import { imageSourceResolvers, mockImageSources } from "@/testing/resolvers/imageSources";
import { render, screen, userEvent, waitFor } from "@/utils/test-utils";

const mockServer = setupServer(
  imageSourceResolvers.getImageSource.handler(),
  imageSourceResolvers.createImageSource.handler(),
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

it("shows an error for invalid URLs", async () => {
  render(<ImageSourceForm type="add" />);

  const urlInput = screen.getByRole("textbox", { name: "URL" });

  await userEvent.type(urlInput, "not a valid URL");
  await userEvent.tab();

  expect(screen.getByText(/Not a valid URL/i)).toBeInTheDocument();
});

it("shows an error for invalid priority", async () => {
  render(<ImageSourceForm type="add" />);

  const priorityInput = screen.getByRole("textbox", { name: "Priority" });

  await userEvent.type(priorityInput, "not a number");
  await userEvent.tab();

  expect(screen.getByText(/priority must be a `number`/i)).toBeInTheDocument();

  await userEvent.clear(priorityInput);
  await userEvent.type(priorityInput, "1.5");
  await userEvent.tab();

  expect(screen.getByText(/priority must be a whole number/i)).toBeInTheDocument();
});

it("shows an error for invalid Sync interval", async () => {
  render(<ImageSourceForm type="add" />);

  const syncIntervalInput = screen.getByRole("textbox", { name: "Sync interval" });

  await userEvent.type(syncIntervalInput, "not a number");
  await userEvent.tab();

  expect(screen.getByText(/sync_interval must be a `number`/i)).toBeInTheDocument();

  await userEvent.clear(syncIntervalInput);
  await userEvent.type(syncIntervalInput, "1.5");
  await userEvent.tab();

  expect(screen.getByText(/sync interval must be a whole number/i)).toBeInTheDocument();
});

it("hides the sync interval field when 'Automatically sync images' is unchecked", async () => {
  render(<ImageSourceForm type="add" />);

  expect(screen.getByRole("textbox", { name: "Sync interval" })).toBeInTheDocument();

  await userEvent.click(screen.getByRole("checkbox", { name: "Automatically sync images" }));

  await waitFor(() => {
    expect(screen.queryByRole("textbox", { name: "Sync interval" })).not.toBeInTheDocument();
  });
});

it("closes the side panel and resets selected source when 'Cancel' is clicked", async () => {
  const setSelected = vi.fn();
  const setSidebar = vi.fn();

  render(
    <AppLayoutContext.Provider value={{ sidebar: null, setSidebar, previousSidebar: null }}>
      <BootSourceContext.Provider value={{ selected: mockImageSources[0].id, setSelected }}>
        <ImageSourceForm type="edit" />
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
