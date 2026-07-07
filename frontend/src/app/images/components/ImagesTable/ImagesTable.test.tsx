import ImagesTable from "@/app/images/components/ImagesTable/ImagesTable";
import { selectedImageFactory } from "@/mocks/factories";
import { imageResolvers } from "@/testing/resolvers/images";
import { renderWithMemoryRouter, screen, setupServer, userEvent, waitFor } from "@/utils/test-utils";

const images = selectedImageFactory.buildList(2, { os: "Hannah Montana Linux" });
const mockServer = setupServer(imageResolvers.selectedImages.handler(images));

const { mockOpenSidePanel, mockCloseSidePanel } = vi.hoisted(() => ({
  mockOpenSidePanel: vi.fn(),
  mockCloseSidePanel: vi.fn(),
}));

vi.mock("@canonical/maas-react-components", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    useSidePanel: () => ({
      openSidePanel: mockOpenSidePanel,
      closeSidePanel: mockCloseSidePanel,
      setSidePanelSize: vi.fn(),
      isOpen: false,
      title: "",
      size: "regular" as const,
      component: null,
      props: {},
    }),
  };
});

beforeEach(() => {
  vi.clearAllMocks();
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
        expect(mockOpenSidePanel).toHaveBeenCalledWith(expect.objectContaining({ title: "Remove available images" }));
      });
    });
  });
});
