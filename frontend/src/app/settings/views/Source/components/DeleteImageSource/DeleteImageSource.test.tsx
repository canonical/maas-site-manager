import { setupServer } from "msw/node";

import DeleteImageSource from "./DeleteImageSource";

import { BootSourceContext } from "@/app/context/BootSourceContext";
import { imageSourceResolvers, mockImageSources } from "@/testing/resolvers/imageSources";
import { render, screen, waitFor } from "@/utils/test-utils";

const mockServer = setupServer(
  imageSourceResolvers.getImageSource.handler(),
  imageSourceResolvers.deleteImageSource.handler(),
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

const renderForm = async (id: number) => {
  const view = render(
    <BootSourceContext.Provider value={{ selected: id, setSelected: vi.fn() }}>
      <DeleteImageSource />
    </BootSourceContext.Provider>,
  );
  return view;
};

it("shows the name of the site in the title and description", async () => {
  // Use a specific image source from the mock data
  const testImageSource = mockImageSources[0]; // Using the second item just like in the original test

  renderForm(testImageSource.id);

  // Wait for the component to finish loading
  await waitFor(() => {
    expect(screen.getByRole("heading", { name: `Remove ${testImageSource.url}?` })).toBeInTheDocument();
  });

  expect(
    screen.getByText(`Are you sure you want to remove ${testImageSource.url} as an image source in MAAS Site Manager?`),
  ).toBeInTheDocument();
});
