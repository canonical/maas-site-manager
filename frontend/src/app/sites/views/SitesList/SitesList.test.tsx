import SitesList from "./SitesList";

import { siteFactory } from "@/mocks/factories";
import { sitesResolvers } from "@/testing/resolvers/sites";
import { renderWithMemoryRouter, screen, setupServer, userEvent, waitFor, within } from "@/utils/test-utils";

const searchSiteName = "SearchTestSite";
const sites = siteFactory.buildList(3);
sites[1].name = searchSiteName;

const mockServer = setupServer(sitesResolvers.listSites.handler(sites));

beforeAll(() => {
  mockServer.listen();
});

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("SitesList", () => {
  describe("display", () => {
    it("displays a loading component while sites are loading", async () => {
      renderWithMemoryRouter(<SitesList />);

      await waitFor(() => {
        expect(screen.getAllByRole("progressbar", { name: /loading/i }).length).toBeGreaterThan(0);
      });
    });

    it("displays a populated sites table", async () => {
      renderWithMemoryRouter(<SitesList />);

      expect(screen.getByRole("treegrid", { name: /sites/i })).toBeInTheDocument();

      await waitFor(() => {
        const tableBody = screen.getAllByRole("rowgroup")[1];
        expect(within(tableBody).getAllByRole("row")).toHaveLength(sites.length);
      });

      const tableBody = screen.getAllByRole("rowgroup")[1];
      within(tableBody)
        .getAllByRole("row")
        .forEach((row, i) => {
          expect(row).toHaveTextContent(new RegExp(sites[i].name, "i"));
        });
    });

    it("disables the remove button if no rows are selected", () => {
      renderWithMemoryRouter(<SitesList />);

      expect(screen.getByRole("button", { name: /Remove/i })).toBeAriaDisabled();
    });

    it("can hide and unhide columns", async () => {
      renderWithMemoryRouter(<SitesList />);

      await waitFor(() => {
        expect(screen.getByRole("columnheader", { name: /Connection/i })).toBeInTheDocument();
      });

      await userEvent.click(screen.getByRole("button", { name: "Columns" }));

      [/Connection/i, /Address/i, /Time/i, /Machines/i, /Status/i].forEach((name) => {
        expect(screen.getByRole("checkbox", { name })).toBeInTheDocument();
      });

      await userEvent.click(screen.getByRole("checkbox", { name: /Connection/i }));

      expect(screen.getByRole("checkbox", { name: "4 out of 5 selected" })).toBeInTheDocument();
      expect(screen.queryByRole("columnheader", { name: /Connection/i })).not.toBeInTheDocument();

      await userEvent.click(screen.getByRole("checkbox", { name: /Connection/i }));

      expect(screen.getByRole("checkbox", { name: "5 out of 5 selected" })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: /Connection/i })).toBeInTheDocument();
    });

    it("can hide and unhide all columns", async () => {
      renderWithMemoryRouter(<SitesList />);

      await waitFor(() => {
        expect(screen.getByRole("columnheader", { name: /Connection/i })).toBeInTheDocument();
      });
      expect(screen.getByRole("columnheader", { name: /Country/i })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: /Local time/i })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: /Machines/i })).toBeInTheDocument();

      await userEvent.click(screen.getByRole("button", { name: "Columns" }));
      await userEvent.click(screen.getByRole("checkbox", { name: "5 out of 5 selected" }));

      expect(screen.getByRole("checkbox", { name: "0 out of 5 selected" })).toBeInTheDocument();
      expect(screen.queryByRole("columnheader", { name: /Connection/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("columnheader", { name: /Country/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("columnheader", { name: /Local time/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("columnheader", { name: /Machines/i })).not.toBeInTheDocument();

      await userEvent.click(screen.getByRole("checkbox", { name: "0 out of 5 selected" }));

      expect(screen.getByRole("columnheader", { name: /Connection/i })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: /Country/i })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: /Local time/i })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: /Machines/i })).toBeInTheDocument();
    });
  });

  describe("actions", () => {
    it("enables the remove button if some rows are selected", async () => {
      renderWithMemoryRouter(<SitesList />);

      await waitFor(() => {
        expect(screen.getByRole("checkbox", { name: /select all/i })).not.toBeDisabled();
      });

      await userEvent.click(screen.getByRole("checkbox", { name: /select all/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Remove/i })).not.toBeAriaDisabled();
      });
    });

    it("toggles the select all checkbox on click", async () => {
      renderWithMemoryRouter(<SitesList />);

      await waitFor(() => {
        expect(screen.getByRole("checkbox", { name: /select all/i })).not.toBeDisabled();
      });

      const checkbox = screen.getByRole("checkbox", { name: /select all/i });
      expect(checkbox).not.toBeChecked();

      await userEvent.click(checkbox);

      expect(checkbox).toBeChecked();
    });

    it("adds search text to navigation url and narrows down search results", async () => {
      const searchText = "SearchTestSite";

      renderWithMemoryRouter(<SitesList />);

      await waitFor(() => {
        const tableBody = screen.getAllByRole("rowgroup")[1];
        expect(within(tableBody).getAllByRole("row")).toHaveLength(sites.length);
      });

      const searchBox = screen.getByRole("searchbox", {
        name: /search and filter/i,
      });

      await userEvent.type(searchBox, searchText);

      await waitFor(() => {
        expect(
          screen.getByRole("tab", {
            name: /map/i,
          }),
        ).toHaveAttribute("href", `/sites/map?q=${searchText}`);
      });

      expect(
        screen.getByRole("tab", {
          name: /table/i,
        }),
      ).toHaveAttribute("href", `/sites/list?q=${searchText}`);

      await waitFor(() => {
        const tableBody = screen.getAllByRole("rowgroup")[1];
        expect(within(tableBody).getAllByRole("row")).toHaveLength(1);
        expect(within(tableBody).getAllByRole("row")[0]).toHaveTextContent(searchSiteName);
      });
    });
  });
});
