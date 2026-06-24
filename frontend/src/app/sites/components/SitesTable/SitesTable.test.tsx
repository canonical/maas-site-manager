import type { ComponentProps } from "react";

import SitesTable from "./SitesTable";

import { TimeZone } from "@/app/apiclient";
import { enrollmentRequestFactory, siteFactory, sitesQueryResultFactory, statsFactory } from "@/mocks/factories";
import { enrollmentRequestsResolvers } from "@/testing/resolvers/enrollmentRequests";
import { renderWithMemoryRouter, screen, setupServer, userEvent, waitFor, within } from "@/utils/test-utils";

const enrollmentRequests = enrollmentRequestFactory.buildList(2);
const mockServer = setupServer(enrollmentRequestsResolvers.listEnrollmentRequests.handler(enrollmentRequests));

const mockUseAppLayoutContext = vi.spyOn(await import("@/app/context"), "useAppLayoutContext");
const mockUseAppLayoutContextDirect = vi.spyOn(await import("@/app/context/AppLayoutContext"), "useAppLayoutContext");
const mockUseSiteDetailsContext = vi.spyOn(await import("@/app/context/SiteDetailsContext"), "useSiteDetailsContext");

const mockSetSidebar = vi.fn();
const mockSetSiteId = vi.fn();

const paginationProps = {
  currentPage: 1,
  dataContext: "MAAS Sites",
  handlePageSizeChange: vi.fn(),
  isPending: false,
  itemsPerPage: 10,
  onNextClick: vi.fn(),
  onPreviousClick: vi.fn(),
  setCurrentPage: vi.fn(),
  totalItems: 1,
};

const buildProps = (overrides: Partial<ComponentProps<typeof SitesTable>> = {}): ComponentProps<typeof SitesTable> => ({
  data: sitesQueryResultFactory.build({
    items: [siteFactory.build()],
    page: 1,
    size: paginationProps.itemsPerPage,
    total: 1,
  }),
  error: null,
  isPending: false,
  paginationProps: {
    ...paginationProps,
  },
  searchText: "",
  setSearchText: vi.fn(),
  setSorting: vi.fn(),
  sorting: [],
  ...overrides,
});

const renderSitesTable = (overrides: Partial<ComponentProps<typeof SitesTable>> = {}) => {
  return renderWithMemoryRouter(<SitesTable {...buildProps(overrides)} />);
};

beforeAll(() => {
  mockServer.listen();
});

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();

  const appLayoutContextValue = {
    previousSidebar: null,
    setSidebar: mockSetSidebar,
    sidebar: null,
  };

  mockUseAppLayoutContext.mockReturnValue(appLayoutContextValue);
  mockUseAppLayoutContextDirect.mockReturnValue(appLayoutContextValue);
  mockUseSiteDetailsContext.mockReturnValue({
    selected: null,
    setSelected: mockSetSiteId,
  });
});

afterEach(() => {
  vi.useRealTimers();
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("SitesTable", () => {
  describe("display", () => {
    it("displays a loading component if sites are loading", async () => {
      renderSitesTable({ isPending: true });

      await waitFor(() => {
        expect(screen.getAllByRole("progressbar", { name: /loading/i }).length).toBeGreaterThan(0);
      });
    });

    it("displays a message when rendering an empty list", async () => {
      mockServer.use(enrollmentRequestsResolvers.listEnrollmentRequests.handler([]));

      renderSitesTable({
        data: sitesQueryResultFactory.build({ items: [], page: 1, size: 10, total: 0 }),
        paginationProps: {
          ...paginationProps,
          totalItems: 0,
        },
      });

      await waitFor(() => {
        expect(screen.getByText("No enrolled MAAS sites")).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Go to Tokens page/i })).toBeInTheDocument();
      });
    });

    it("displays the columns correctly", () => {
      renderSitesTable();

      ["Name", "Connection", "Country", "Local time", "Machines", "Aggregated status"].forEach((column) => {
        expect(
          screen.getByRole("columnheader", {
            name: new RegExp(`^${column}`, "i"),
          }),
        ).toBeInTheDocument();
      });

      expect(screen.getByRole("button", { name: /Columns/i })).toBeInTheDocument();
    });

    it("displays site details including the country, local time, and aggregated status", () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date("2023-04-21T12:00:00.000Z"));

      const item = siteFactory.build({
        country: "GB",
        stats: statsFactory.build({
          machines_allocated: 200,
          machines_deployed: 100,
          machines_error: 400,
          machines_ready: 300,
          machines_total: 1000,
        }),
        timezone: TimeZone.EUROPE_LONDON,
        url: "https://example.com",
      });

      renderSitesTable({
        data: sitesQueryResultFactory.build({ items: [item], page: 1, size: 1, total: 1 }),
        paginationProps: {
          ...paginationProps,
          itemsPerPage: 1,
        },
      });

      expect(screen.getByRole("link", { name: item.url })).toBeInTheDocument();
      expect(screen.getByText("United Kingdom")).toBeInTheDocument();
      expect(screen.getByText(/13:00 UTC\+1/i)).toBeInTheDocument();
      expect(screen.getByText("100 of 1000 deployed")).toBeInTheDocument();
    });

    it("displays the non-unique name warning when a site name is duplicated", () => {
      const uniqueSite = siteFactory.build({ name_unique: true });
      const { rerender } = renderSitesTable({
        data: sitesQueryResultFactory.build({ items: [uniqueSite], page: 1, size: 1, total: 1 }),
        paginationProps: {
          ...paginationProps,
          itemsPerPage: 1,
        },
      });

      expect(screen.queryByRole("button", { name: /warning - name is not unique/i })).not.toBeInTheDocument();

      const nonUniqueSite = siteFactory.build({ name_unique: false });

      rerender(
        <SitesTable
          {...buildProps({
            data: sitesQueryResultFactory.build({ items: [nonUniqueSite], page: 1, size: 1, total: 1 }),
            paginationProps: {
              ...paginationProps,
              itemsPerPage: 1,
            },
          })}
        />,
      );

      expect(screen.getByRole("button", { name: /warning - name is not unique/i })).toBeInTheDocument();
    });

    it("calls the sorting handler when the name header is clicked", async () => {
      const items = siteFactory.buildList(2);
      const setSorting = vi.fn();

      renderSitesTable({
        data: sitesQueryResultFactory.build({ items, page: 1, size: 10, total: 2 }),
        paginationProps: {
          ...paginationProps,
          totalItems: 2,
        },
        setSorting,
      });

      await userEvent.click(screen.getByRole("button", { name: "Name" }));

      expect(setSorting).toHaveBeenCalled();
    });
  });

  describe("actions", () => {
    it("opens the edit site sidebar and selects the site when edit is clicked", async () => {
      const item = siteFactory.build({ name: "alpha-site" });

      renderSitesTable({
        data: sitesQueryResultFactory.build({ items: [item], page: 1, size: 1, total: 1 }),
        paginationProps: {
          ...paginationProps,
          itemsPerPage: 1,
        },
      });

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const row = within(tableBody).getByRole("row", { name: new RegExp(item.name, "i") });

      await userEvent.click(within(row).getByRole("button", { name: "Edit" }));

      expect(mockSetSiteId).toHaveBeenCalledWith(item.id);
      expect(mockSetSidebar).toHaveBeenCalledWith("editSite");
    });

    it("opens the remove sites sidebar when delete is clicked", async () => {
      const item = siteFactory.build({ name: "beta-site" });

      renderSitesTable({
        data: sitesQueryResultFactory.build({ items: [item], page: 1, size: 1, total: 1 }),
        paginationProps: {
          ...paginationProps,
          itemsPerPage: 1,
        },
      });

      const tableBody = screen.getAllByRole("rowgroup")[1];
      const row = within(tableBody).getByRole("row", { name: new RegExp(item.name, "i") });

      await userEvent.click(within(row).getByRole("button", { name: "Delete" }));

      expect(mockSetSidebar).toHaveBeenCalledWith("removeSites");
    });

    it("enables bulk remove when a row is selected and opens the remove sidebar", async () => {
      const item = siteFactory.build({ name: "gamma-site" });

      renderSitesTable({
        data: sitesQueryResultFactory.build({ items: [item], page: 1, size: 1, total: 1 }),
        paginationProps: {
          ...paginationProps,
          itemsPerPage: 1,
        },
      });

      const removeButton = screen.getByRole("button", { name: /Remove/i });
      expect(removeButton).toBeAriaDisabled();

      await userEvent.click(screen.getByRole("checkbox", { name: `select ${item.name}` }));

      await waitFor(() => {
        expect(removeButton).not.toBeAriaDisabled();
      });

      await userEvent.click(removeButton);

      expect(mockSetSidebar).toHaveBeenCalledWith("removeSites");
    });
  });
});
