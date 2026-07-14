import ImageSourceList from "./ImageSourceList";

import type { useImageSources } from "@/app/api/query/imageSources";
import { imageSourceFactory } from "@/mocks/factories";
import { mockSidePanel, renderWithMemoryRouter, screen, userEvent } from "@/utils/test-utils";

type UseImageSourcesResult = ReturnType<typeof useImageSources>;

const imageSources = [imageSourceFactory.build({ id: 101, name: "Daily mirror", url: "https://images.example.com" })];

const { mockOpen } = await mockSidePanel();

const mockUseBootSourceContext = vi.spyOn(await import("@/app/context/BootSourceContext"), "useBootSourceContext");
const mockUseImageSources = vi.spyOn(await import("@/app/api/query/imageSources"), "useImageSources");

const mockSetSelected = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  mockUseBootSourceContext.mockReturnValue({
    selected: null,
    setSelected: mockSetSelected,
  });
  mockUseImageSources.mockReturnValue({
    data: { items: imageSources },
    error: null,
    isPending: false,
  } as UseImageSourcesResult);
});

describe("ImageSourceList", () => {
  it("renders the image source list", () => {
    renderWithMemoryRouter(<ImageSourceList />);

    expect(screen.getByRole("heading", { name: /Source/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Add image source/i })).toBeInTheDocument();
    expect(screen.getByRole("treegrid", { name: /Image source list/i })).toBeInTheDocument();
  });

  it("opens the 'Add image source' side panel when 'Add image source' is clicked", async () => {
    renderWithMemoryRouter(<ImageSourceList />);

    await userEvent.click(screen.getByRole("button", { name: /Add image source/i }));

    expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Add image source" }));
  });

  it("opens the 'Edit image source' side panel when 'Edit image source' is clicked", async () => {
    renderWithMemoryRouter(<ImageSourceList />);

    await userEvent.click(screen.getByRole("button", { name: "Edit image source" }));

    expect(mockSetSelected).toHaveBeenCalledWith(imageSources[0].id);
    expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Edit image source" }));
  });

  it("opens the 'Delete image source' modal when 'Delete image source' is clicked", async () => {
    renderWithMemoryRouter(<ImageSourceList />);

    await userEvent.click(screen.getByRole("button", { name: "Delete image source" }));

    expect(mockSetSelected).toHaveBeenCalledWith(imageSources[0].id);
    expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Delete image source" }));
  });
});
