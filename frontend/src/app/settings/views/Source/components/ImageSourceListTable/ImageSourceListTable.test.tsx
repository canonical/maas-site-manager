import ImageSourceListTable from "./ImageSourceListTable";

import type { BootSource } from "@/app/apiclient";
import { imageSourceFactory } from "@/mocks/factories";
import { renderWithMemoryRouter, screen, within } from "@/utils/test-utils";

const mockImageSources = imageSourceFactory.buildList(4);

it("renders an empty image source table", () => {
  renderWithMemoryRouter(<ImageSourceListTable data={[]} error={null} isPending={false} />);

  expect(screen.getByRole("table", { name: "Image source list" })).toBeInTheDocument();
  expect(screen.getAllByRole("row")).toHaveLength(1); // Only header row should be there
});

it("shows a spinner while loading", () => {
  renderWithMemoryRouter(<ImageSourceListTable data={[]} error={null} isPending={true} />);

  expect(screen.getByText(/Loading/i)).toBeInTheDocument();
});

it("shows errors if present", () => {
  const errorMessage = "There has been an error!";
  renderWithMemoryRouter(<ImageSourceListTable data={[]} error={new Error(errorMessage)} isPending={false} />);

  expect(screen.getByText(errorMessage)).toBeInTheDocument();
});

it("renders rows with details for each image source", () => {
  renderWithMemoryRouter(<ImageSourceListTable data={mockImageSources} error={null} isPending={false} />);

  expect(screen.getByRole("table", { name: "Image source list" })).toBeInTheDocument();

  const tableBody = screen.getAllByRole("rowgroup")[1];
  expect(within(tableBody).getAllByRole("row")).toHaveLength(mockImageSources.length);

  // Remove "custom" row - we test this later
  const rows = within(tableBody).getAllByRole("row").slice(1);
  rows.forEach((row, index) => {
    const cells = within(row).getAllByRole("cell");
    expect(cells[0]).toHaveTextContent(mockImageSources[index + 1].name);
    expect(cells[1]).toHaveTextContent(mockImageSources[index + 1].url);
    expect(
      within(cells[2]).getByText(
        mockImageSources[index + 1].sync_interval > 0 ? "Source is syncing" : "Source is not syncing",
      ),
    ).toBeInTheDocument();
    expect(
      within(cells[3]).getByText(
        !mockImageSources[index + 1].keyring ? "Not signed with GPG key" : "Signed with GPG key",
      ),
    ).toBeInTheDocument();
    expect(cells[4]).toHaveTextContent(mockImageSources[index + 1].priority.toString());
    expect(within(cells[5]).getByRole("button", { name: "Edit image source" })).toBeInTheDocument();
    expect(within(cells[5]).getByRole("button", { name: "Delete image source" })).toBeInTheDocument();
  });
});

it("doesn't show status, syncing, signature or delete button for custom image source", () => {
  renderWithMemoryRouter(
    <ImageSourceListTable
      data={[
        {
          id: 0,
          url: "custom",
          keyring: "",
          name: "Ubuntu",
          sync_interval: 0,
          priority: 1,
          last_sync: "",
        },
      ]}
      error={null}
      isPending={false}
    />,
  );

  const tableBody = screen.getAllByRole("rowgroup")[1];
  const customRow = within(tableBody).getAllByRole("row")[0];
  const cells = within(customRow).getAllByRole("cell");
  expect(cells[0]).toHaveTextContent("Ubuntu");
  expect(cells[1]).toHaveTextContent("Custom images");
  expect(cells[2]).toHaveTextContent("");
  expect(cells[3]).toHaveTextContent("");
  expect(cells[4]).toHaveTextContent(mockImageSources[0].priority.toString());
  expect(within(cells[5]).getByRole("button", { name: "Edit image source" })).toBeInTheDocument();
  expect(within(cells[5]).queryByRole("button", { name: "Delete image source" })).not.toBeInTheDocument();
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
