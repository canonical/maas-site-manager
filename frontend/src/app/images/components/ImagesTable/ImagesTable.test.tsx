import ImagesTable from "@/app/images/components/ImagesTable/ImagesTable";
import { selectedImageFactory } from "@/mocks/factories";
import { imageResolvers } from "@/testing/resolvers/images";
import { renderWithMemoryRouter, screen, setupServer, userEvent, waitFor } from "@/utils/test-utils";

const images = selectedImageFactory.buildList(2, { os: "Hannah Montana Linux" });
const mockServer = setupServer(imageResolvers.selectedImages.handler(images));

const mockUseAppLayoutContext = vi.spyOn(await import("@/app/context/AppLayoutContext"), "useAppLayoutContext");

const mockSetSidebar = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  mockUseAppLayoutContext.mockReturnValue({
    previousSidebar: null,
    setSidebar: mockSetSidebar,
    sidebar: null,
  });
});

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("ImagesTable", () => {
  describe("display", () => {
    it("displays a loading component if images are loading", async () => {
      renderWithMemoryRouter(<ImagesTable />);

      await waitFor(() => {
        expect(screen.getAllByRole("progressbar", { name: /loading/i }).length).toBeGreaterThan(0);
      });
    });

    it("displays a message when rendering an empty list", async () => {
      mockServer.use(imageResolvers.selectedImages.handler([]));
      renderWithMemoryRouter(<ImagesTable />);

      await waitFor(() => {
        expect(screen.getByText("No images found.")).toBeInTheDocument();
      });
    });

    it("displays the columns correctly", () => {
      renderWithMemoryRouter(<ImagesTable />);

      ["Release", "Architecture", "Size", "Status", "Custom", "Source", "Action"].forEach((column) => {
        expect(
          screen.getByRole("columnheader", {
            name: new RegExp(`^${column}`, "i"),
          }),
        ).toBeInTheDocument();
      });
    });
  });

  describe("actions", () => {
    it("opens delete image side panel form", async () => {
      mockServer.use(imageResolvers.selectedImages.handler([selectedImageFactory.build()]));

      renderWithMemoryRouter(<ImagesTable />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
      });

      await userEvent.click(screen.getByRole("button", { name: "Delete" }));

      await waitFor(() => {
        expect(mockSetSidebar).toHaveBeenCalledWith("removeAvailableImages");
      });
    });
  });
});
