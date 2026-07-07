import { http, HttpResponse } from "msw";

import { RemoveAvailableImages } from "./RemoveAvailableImages";

import * as context from "@/app/context";
import { imageResolvers } from "@/testing/resolvers/images";
import { apiUrls } from "@/utils/test-urls";
import {
    getByTextContent,
    render,
    renderWithMemoryRouter,
    screen,
    setupServer,
    userEvent,
    waitFor,
} from "@/utils/test-utils";

const mockServer = setupServer(imageResolvers.removeImageFromSelection.handler(), imageResolvers.removeImage.handler());

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

const clearRowSelection = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  vi.spyOn(context, "useRowSelection").mockImplementation(() => ({
    rowSelection: { "1": true, "2": true },
    setRowSelection: vi.fn(),
    clearRowSelection,
  }));
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

describe("RemoveAvailableImages", () => {
  it("displays delete confirmation", () => {
    render(<RemoveAvailableImages />);
    expect(
      getByTextContent(new RegExp("Are you sure you want to remove 2 available images?", "s")),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Remove 2 available images" })).toBeInTheDocument();
  });

  it("closes sidebar when the cancel button is clicked and clears row selection", async () => {
    renderWithMemoryRouter(<RemoveAvailableImages />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: /Cancel/i }));
    expect(mockCloseSidePanel).toHaveBeenCalled();

    expect(clearRowSelection).toHaveBeenCalled();

    vi.restoreAllMocks();
  });

  it("calls remove image on save click and clears row selection", async () => {
    renderWithMemoryRouter(<RemoveAvailableImages />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Remove 2 available images/i })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Remove 2 available images/i })).toBeEnabled();
    });

    await userEvent.click(screen.getByRole("button", { name: /Remove 2 available images/i }));

    await waitFor(() => {
      expect(imageResolvers.removeImageFromSelection.resolved).toBeTruthy();
    });
  });

  it("displays error message when fetching available images fails", async () => {
    mockServer.use(
      http.post(apiUrls.removeImageFromSelection, () => {
        return new HttpResponse(null, {
          status: 500,
          statusText: "error",
        });
      }),
    );

    renderWithMemoryRouter(<RemoveAvailableImages />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Remove 2 available images/i })).toBeEnabled();
    });

    await userEvent.click(screen.getByRole("button", { name: /Remove 2 available images/i }));

    await waitFor(() => {
      expect(screen.getByText("Remove failed")).toBeInTheDocument();
    });
  });
});
