import ImageSourceListTable from "./ImageSourceListTable";

import type { BootSource } from "@/app/apiclient";
import { imageSourceFactory } from "@/mocks/factories";
import { mockImageSources } from "@/testing/resolvers/imageSources";
import { mockSidePanel, renderWithMemoryRouter, screen, userEvent, waitFor, within } from "@/utils/test-utils";

const { mockOpen } = await mockSidePanel();

const mockUseBootSourceContext = vi.spyOn(await import("@/app/context/BootSourceContext"), "useBootSourceContext");

const mockSetSelected = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  mockUseBootSourceContext.mockReturnValue({
    selected: null,
    setSelected: mockSetSelected,
  });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("ImageSourceListTable", () => {
  describe("display", () => {
    it("displays a loading component if image sources are loading", async () => {
      renderWithMemoryRouter(<ImageSourceListTable data={[]} error={null} isPending={true} />);

      await waitFor(() => {
        expect(screen.getAllByRole("progressbar", { name: /loading/i }).length).toBeGreaterThan(0);
      });
    });

    it("displays a message when rendering an empty list", async () => {
      renderWithMemoryRouter(<ImageSourceListTable data={[]} error={null} isPending={false} />);

      await waitFor(() => {
        expect(screen.getByText("No image sources configured.")).toBeInTheDocument();
      });
    });

    it("shows errors if present", async () => {
      const errorMessage = "There has been an error!";

      renderWithMemoryRouter(<ImageSourceListTable data={[]} error={new Error(errorMessage)} isPending={false} />);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it("displays the columns correctly", () => {
      renderWithMemoryRouter(<ImageSourceListTable data={[]} error={null} isPending={false} />);

      ["Name", "Source", "Syncing", "Signed with GPG key", "Priority", "Actions"].forEach((column) => {
        expect(
          screen.getByRole("columnheader", {
            name: new RegExp(`^${column}`, "i"),
          }),
        ).toBeInTheDocument();
      });
    });

    it("renders rows with details for each image source", () => {
      renderWithMemoryRouter(<ImageSourceListTable data={mockImageSources} error={null} isPending={false} />);

      expect(screen.getByRole("treegrid", { name: "Image source list" })).toBeInTheDocument();

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const rows = within(tableBody).getAllByRole("row");

      expect(rows).toHaveLength(mockImageSources.length);

      rows.forEach((row, index) => {
        const item = mockImageSources[index];
        expect(row).toHaveTextContent(item.name);
        expect(row).toHaveTextContent(item.url === "custom" ? "Custom images" : item.url);

        if (item.url === "custom") {
          expect(within(row).queryByText(/Source is syncing|Source is not syncing/i)).not.toBeInTheDocument();
          expect(within(row).queryByText(/Signed with GPG key|Not signed with GPG key/i)).not.toBeInTheDocument();
          expect(within(row).queryByRole("button", { name: "Delete image source" })).not.toBeInTheDocument();
        } else {
          expect(
            within(row).getByText(item.sync_interval > 0 ? "Source is syncing" : "Source is not syncing"),
          ).toBeInTheDocument();
          expect(
            within(row).getByText(!item.keyring ? "Not signed with GPG key" : "Signed with GPG key"),
          ).toBeInTheDocument();
          expect(within(row).getByRole("button", { name: "Delete image source" })).toBeInTheDocument();
        }

        expect(within(row).getByText(item.priority.toString())).toBeInTheDocument();
        expect(within(row).getByRole("button", { name: "Edit image source" })).toBeInTheDocument();
      });
    });

    // TODO: re-enable test once the status field is added to BootSource
    it.skip("shows a tick icon for syncing sources, and a cross for non-syncing sources", () => {
      const bootSources: { items: BootSource[] } = {
        items: [
          {
            id: 1,
            url: "images.example.com",
            keyring: "abcdefghijklmnopqrstuvwxyz",
            name: "Ubuntu",
            sync_interval: 150,
            priority: 1,
            last_sync: "",
          },
          {
            id: 1,
            url: "images.example2.com",
            keyring: "abcdefghijklmnopqrstuvwxyz",
            name: "Ubuntu",
            sync_interval: 0,
            priority: 1,
            last_sync: "",
          },
        ],
      };
      renderWithMemoryRouter(<ImageSourceListTable data={bootSources.items} error={null} isPending={false} />);

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const rows = within(tableBody).getAllByRole("row");

      // first child is the wrapper div, child of that div is the icon
      expect(within(rows[0]).getAllByRole("cell")[2].firstChild?.firstChild).toHaveClass("p-icon--task-outstanding");
      expect(within(rows[0]).getAllByRole("cell")[2]).toHaveAccessibleName("Source is syncing");

      expect(within(rows[1]).getAllByRole("cell")[2].firstChild?.firstChild).toHaveClass("p-icon--error-grey");
      expect(within(rows[1]).getAllByRole("cell")[2]).toHaveAccessibleName("Source is not syncing");
    });

    it("does not show syncing, signature or delete action for the custom image source row", () => {
      const customImageSource = {
        id: 0,
        keyring: "",
        last_sync: "",
        name: "Ubuntu",
        priority: 1,
        sync_interval: 0,
        url: "custom",
      };

      renderWithMemoryRouter(<ImageSourceListTable data={[customImageSource]} error={null} isPending={false} />);

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const customRow = within(tableBody).getByRole("row", { name: /Ubuntu/i });

      expect(customRow).toHaveTextContent("Ubuntu");
      expect(customRow).toHaveTextContent("Custom images");
      expect(customRow).toHaveTextContent(customImageSource.priority.toString());
      expect(within(customRow).queryByText(/Source is syncing|Source is not syncing/i)).not.toBeInTheDocument();
      expect(within(customRow).queryByText(/Signed with GPG key|Not signed with GPG key/i)).not.toBeInTheDocument();
      expect(within(customRow).getByRole("button", { name: "Edit image source" })).toBeInTheDocument();
      expect(within(customRow).queryByRole("button", { name: "Delete image source" })).not.toBeInTheDocument();
    });
  });

  describe("actions", () => {
    it("opens the edit boot source sidebar and selects the image source when edit is clicked", async () => {
      const item = imageSourceFactory.build({ id: 17, name: "Ubuntu archive", url: "https://images.example.com" });

      renderWithMemoryRouter(<ImageSourceListTable data={[item]} error={null} isPending={false} />);

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const row = within(tableBody).getByRole("row", { name: new RegExp(item.name, "i") });

      await userEvent.click(within(row).getByRole("button", { name: "Edit image source" }));

      expect(mockSetSelected).toHaveBeenCalledWith(item.id);
      expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Edit image source" }));
    });

    it("opens the custom image source sidebar when editing the custom row", async () => {
      const item = imageSourceFactory.build({ id: 23, name: "Custom upload", url: "custom" });

      renderWithMemoryRouter(<ImageSourceListTable data={[item]} error={null} isPending={false} />);

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const row = within(tableBody).getByRole("row", { name: /Custom upload/i });

      await userEvent.click(within(row).getByRole("button", { name: "Edit image source" }));

      expect(mockSetSelected).toHaveBeenCalledWith(item.id);
      expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Edit custom images" }));
    });

    it("opens the delete boot source sidebar when delete is clicked", async () => {
      const item = imageSourceFactory.build({ id: 42, name: "Daily mirror", url: "https://daily.example.com" });

      renderWithMemoryRouter(<ImageSourceListTable data={[item]} error={null} isPending={false} />);

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const row = within(tableBody).getByRole("row", { name: new RegExp(item.name, "i") });

      await userEvent.click(within(row).getByRole("button", { name: "Delete image source" }));

      expect(mockSetSelected).toHaveBeenCalledWith(item.id);
      expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Delete image source" }));
    });
  });
});
