import { http, HttpResponse } from "msw";

import AddToAvailableImages from "./AddToAvailableImages";

import type { SelectableImage } from "@/app/apiclient";
import { selectableImageFactory } from "@/mocks/factories";
import { imageResolvers } from "@/testing/resolvers/images";
import { apiUrls } from "@/utils/test-urls";
import { mockSidePanel, renderWithMemoryRouter, screen, setupServer, userEvent, waitFor } from "@/utils/test-utils";

const ubuntuImages = selectableImageFactory.buildList(5, { os: "Ubuntu" });
const centOsImages = selectableImageFactory.buildList(5, { os: "CentOS" });
const upstreamImages = [...ubuntuImages, ...centOsImages];

const mockServer = setupServer(
  imageResolvers.selectableImages.handler(upstreamImages),
  imageResolvers.addImageToSelection.handler(),
);

const { mockClose } = await mockSidePanel();

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

describe("AddToAvailableImages", () => {
  it("separates images by distro", async () => {
    renderWithMemoryRouter(<AddToAvailableImages />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Ubuntu/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: /CentOS/i })).toBeInTheDocument();
  });

  it("closes sidebar when the cancel button is clicked", async () => {
    renderWithMemoryRouter(<AddToAvailableImages />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Cancel/i })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: /Cancel/i }));
    expect(mockClose).toHaveBeenCalled();
  });

  it("enabled submission when form is edited and calls add image on save click", async () => {
    const images: SelectableImage[] = [];
    const arches = ["amd64", "arm64", "i386"];

    arches.forEach((architecture) => {
      images.push(selectableImageFactory.build({ os: "Ubuntu", release: "22.04 LTS", arch: architecture }));
    });

    const localHandlers = [
      imageResolvers.selectableImages.handler(images),
      imageResolvers.addImageToSelection.handler(),
    ];

    mockServer.use(...localHandlers);

    renderWithMemoryRouter(<AddToAvailableImages />);

    await waitFor(() => {
      expect(screen.getByRole("form", { name: /Add upstream images to available images/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();

    await userEvent.click(screen.getByRole("tab", { name: "Ubuntu" }));

    await waitFor(() => {
      expect(screen.getByRole("combobox", { name: "Select architectures" })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("combobox", { name: "Select architectures" }));

    arches.forEach(async (arch) => {
      await userEvent.click(screen.getByRole("checkbox", { name: arch }));
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
    });

    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(imageResolvers.addImageToSelection.resolved).toBeTruthy();
    });
  });

  it("displays error message when fetching available images fails", async () => {
    mockServer.use(
      http.get(apiUrls.selectableImages, () => {
        return new HttpResponse(null, {
          status: 500,
          statusText: "error",
        });
      }),
    );

    renderWithMemoryRouter(<AddToAvailableImages />);

    await waitFor(() => {
      expect(screen.getByText("Error while fetching upstream images")).toBeInTheDocument();
    });
  });
});
