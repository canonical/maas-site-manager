import SitesTable from "./SitesTable";

import { TimeZone } from "@/app/apiclient";
import { enrollmentRequestFactory, siteFactory, sitesQueryResultFactory, statsFactory } from "@/mocks/factories";
import { enrollmentRequestsResolvers } from "@/testing/resolvers/enrollmentRequests";
import { renderWithMemoryRouter, screen, setupServer, within } from "@/utils/test-utils";

const enrollmentRequests = enrollmentRequestFactory.buildList(2);
const mockServer = setupServer(enrollmentRequestsResolvers.listEnrollmentRequests.handler(enrollmentRequests));

const paginationProps = {
  currentPage: 1,
  dataContext: "MAAS Sites",
  handlePageSizeChange: vi.fn(),
  isPending: false,
  itemsPerPage: 1,
  onNextClick: vi.fn(),
  onPreviousClick: vi.fn(),
  setCurrentPage: vi.fn(),
  totalItems: 1,
};
const commonProps = {
  error: null,
  isPending: false,
  sorting: [],
  setSorting: vi.fn(),
  paginationProps: {
    ...paginationProps,
  },
  setSearchText: vi.fn(),
  searchText: "",
};

beforeAll(() => {
  mockServer.listen();
});

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

it("displays an empty sites table", () => {
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build()}
      paginationProps={{
        ...paginationProps,
        totalItems: 0,
      }}
    />,
  );

  expect(screen.getByRole("treegrid", { name: /sites/i })).toBeInTheDocument();
});

it("displays rows with details for each site", () => {
  const items = siteFactory.buildList(1);
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items, total: 1, page: 1, size: 1 })}
      paginationProps={{
        ...paginationProps,
      }}
    />,
  );

  expect(screen.getByRole("treegrid", { name: /sites/i })).toBeInTheDocument();

  const tableBody = screen.getAllByRole("rowgroup")[1];
  expect(within(tableBody).getAllByRole("row")).toHaveLength(items.length);
  within(tableBody)
    .getAllByRole("row")
    .forEach((row, i) => {
      expect(row).toHaveTextContent(new RegExp(items[i].name, "i"));
    });
});

it("displays correctly paginated results", () => {
  const pageLength = 50;
  const items = siteFactory.buildList(pageLength);
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items, total: 100, page: 1, size: pageLength })}
      error={null}
      isPending={false}
      paginationProps={{
        ...paginationProps,
        itemsPerPage: pageLength,
        totalItems: 100,
      }}
      setSearchText={vi.fn()}
    />,
  );

  const tableBody = screen.getAllByRole("rowgroup")[1];
  expect(within(tableBody).getAllByRole("row")).toHaveLength(pageLength);
});

it("displays correct local time", () => {
  const date = new Date("Fri Apr 21 2023 12:00:00 GMT+0000 (GMT)");
  vi.setSystemTime(date);

  const item = siteFactory.build({ timezone: TimeZone.EUROPE_LONDON });
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items: [item], total: 1, page: 1, size: 1 })}
      error={null}
      isPending={false}
      paginationProps={{
        ...paginationProps,
      }}
      setSearchText={vi.fn()}
    />,
  );

  expect(screen.getByRole("treegrid", { name: /sites/i })).toBeInTheDocument();
  expect(screen.getByText(/13:00 UTC\+1/i)).toBeInTheDocument();
});

it("displays full name of the country", () => {
  const item = siteFactory.build({ country: "GB" });
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items: [item], total: 1, page: 1, size: 1 })}
      error={null}
      isPending={false}
      paginationProps={{
        ...paginationProps,
      }}
      setSearchText={vi.fn()}
    />,
  );

  expect(screen.getByText("United Kingdom")).toBeInTheDocument();
});

it("displays correct number of deployed machines", () => {
  const item = siteFactory.build({
    stats: statsFactory.build({
      machines_total: 1000,
      machines_deployed: 100,
      machines_allocated: 200,
      machines_ready: 300,
      machines_error: 400,
    }),
  });
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items: [item], total: 1, page: 1, size: 1 })}
      paginationProps={{
        ...paginationProps,
      }}
    />,
  );

  expect(screen.getByText("100 of 1000 deployed")).toBeInTheDocument();
});

it("if name is not unique a warning is displayed.", async () => {
  const itemUnique = siteFactory.build({
    name_unique: true,
  });
  const { rerender } = renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items: [itemUnique], total: 1, page: 1, size: 1 })}
      paginationProps={{
        ...paginationProps,
      }}
    />,
  );

  expect(screen.queryByRole("button", { name: /warning - name is not unique/i })).not.toBeInTheDocument();

  const itemNonUnique = siteFactory.build({
    name_unique: false,
  });
  rerender(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items: [itemNonUnique], total: 1, page: 1, size: 1 })}
      paginationProps={{
        ...paginationProps,
      }}
    />,
  );

  expect(screen.getByRole("button", { name: /warning - name is not unique/i })).toBeInTheDocument();
});

it("displays a pagination bar with the table", () => {
  const items = siteFactory.buildList(2);
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items, total: 2, page: 1, size: 10 })}
      paginationProps={{
        ...paginationProps,
        itemsPerPage: 10,
        totalItems: 2,
      }}
    />,
  );

  expect(screen.getByText(/Showing 2 out of 2 MAAS Sites/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /next page/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /previous page/i })).toBeInTheDocument();
});

it("displays sort direction label", async () => {
  const items = siteFactory.buildList(2);
  const { rerender } = renderWithMemoryRouter(
    <SitesTable {...commonProps} data={sitesQueryResultFactory.build({ items, total: 2, page: 1, size: 10 })} />,
  );
  const nameDescending = ["columnheader", { name: /Name descending/i }] as const;
  const nameAscending = ["columnheader", { name: /Name ascending/i }] as const;

  expect(screen.getByRole("columnheader", { name: /Name/i })).toBeInTheDocument();
  expect(screen.queryByRole(...nameDescending)).not.toBeInTheDocument();
  expect(screen.queryByRole(...nameAscending)).not.toBeInTheDocument();

  rerender(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items, total: 2, page: 1, size: 10 })}
      sorting={[{ id: "name", desc: true }]}
    />,
  );

  expect(screen.getByRole(...nameDescending)).toBeInTheDocument();

  rerender(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items, total: 2, page: 1, size: 10 })}
      sorting={[{ id: "name", desc: false }]}
    />,
  );

  expect(screen.getByRole(...nameAscending)).toBeInTheDocument();
});

it("displays action buttons on each row", () => {
  const items = siteFactory.buildList(1);
  renderWithMemoryRouter(
    <SitesTable
      {...commonProps}
      data={sitesQueryResultFactory.build({ items, total: 1, page: 1, size: 1 })}
      paginationProps={{
        ...paginationProps,
      }}
    />,
  );

  expect(screen.getByRole("treegrid", { name: /sites/i })).toBeInTheDocument();

  const tableBody = screen.getAllByRole("rowgroup")[1];
  within(tableBody)
    .getAllByRole("row")
    .forEach((_row) => {
      expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
    });
});
