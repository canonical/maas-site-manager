import ImagesList from "@/app/images/views/ImagesList/ImagesList";
import { selectedImageFactory } from "@/mocks/factories";
import { imageResolvers } from "@/testing/resolvers/images";
import { sitesResolvers } from "@/testing/resolvers/sites";
import { renderWithMemoryRouter, screen, setupServer, userEvent, waitFor } from "@/utils/test-utils";

const images = selectedImageFactory.buildList(2);
const mockServer = setupServer(
  imageResolvers.selectedImages.handler(images),
  imageResolvers.selectableImages.handler(),
  imageResolvers.addImageToSelection.handler(),
  sitesResolvers.listSites.handler(),
);

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
  localStorage.clear();
});

afterAll(() => {
  mockServer.close();
});

describe("ImagesList", () => {
  it("renders add selection form", async () => {
    renderWithMemoryRouter(<ImagesList />, { withMainLayout: true });
    await userEvent.click(screen.getByRole("button", { name: "Add to available images" }));
    expect(await screen.findByRole("complementary", { name: "Add to available images" })).toBeInTheDocument();
  });

  it("renders upload form", async () => {
    renderWithMemoryRouter(<ImagesList />, { withMainLayout: true });
    await userEvent.click(screen.getByRole("button", { name: "Upload custom image" }));
    expect(await screen.findByRole("complementary", { name: "Upload custom image" })).toBeInTheDocument();
  });

  it("renders delete form", async () => {
    renderWithMemoryRouter(<ImagesList />, { withMainLayout: true });
    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Delete" }).length).toBeGreaterThan(0);
    });
    await userEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);
    expect(await screen.findByRole("complementary", { name: "Remove available images" })).toBeInTheDocument();
  });

  it("closes side panel form when canceled", async () => {
    renderWithMemoryRouter(<ImagesList />, { withMainLayout: true });
    await userEvent.click(screen.getByRole("button", { name: "Add to available images" }));
    expect(await screen.findByRole("complementary", { name: "Add to available images" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("complementary", { name: "Add to available images" })).not.toBeInTheDocument();
  });
});
