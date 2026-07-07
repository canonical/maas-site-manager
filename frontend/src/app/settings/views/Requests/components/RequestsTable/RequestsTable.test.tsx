import RequestsTable from "./RequestsTable";

import { enrollmentRequestFactory, enrollmentRequestQueryResultFactory } from "@/mocks/factories";
import { formatUTCDateString } from "@/utils";
import { renderWithMemoryRouter, screen, within } from "@/utils/test-utils";

it("displays a loading text", () => {
  const { rerender } = renderWithMemoryRouter(
    <RequestsTable
      currentPage={1}
      data={enrollmentRequestQueryResultFactory.build()}
      error={null}
      isPending={true}
      pageSize={50}
    />,
  );

  const table = screen.getByRole("table", { name: /enrollment requests/i });
  expect(table).toBeInTheDocument();
  expect(within(table).getByText(/Loading/i)).toBeInTheDocument();

  rerender(
    <RequestsTable
      currentPage={1}
      data={enrollmentRequestQueryResultFactory.build()}
      error={null}
      isPending={false}
      pageSize={50}
    />,
  );

  expect(within(table).queryByText(/Loading/i)).not.toBeInTheDocument();
});

it("should show a message if there are no open enrollment requests", () => {
  renderWithMemoryRouter(
    <RequestsTable
      currentPage={1}
      data={enrollmentRequestQueryResultFactory.build()}
      error={null}
      isPending={false}
      pageSize={50}
    />,
  );

  const table = screen.getByRole("table", { name: /enrollment requests/i });
  expect(table).toBeInTheDocument();
  expect(within(table).getByText(/No outstanding requests/i)).toBeInTheDocument();
});

it("displays enrollment request in each table row correctly", () => {
  const items = enrollmentRequestFactory.buildList(1);
  renderWithMemoryRouter(
    <RequestsTable
      currentPage={1}
      data={enrollmentRequestQueryResultFactory.build({ items })}
      error={null}
      isPending={false}
      pageSize={50}
    />,
  );

  const tableBody = screen.getAllByRole("rowgroup")[1];
  const tableRows = within(tableBody).getAllByRole("row");

  expect(tableRows).toHaveLength(items.length);

  tableRows.forEach((row, i) => {
    const checkbox = new RegExp(`select ${items[i].name}`, "i");
    const name = items[i].name;
    const url = new RegExp(items[i].url, "i");
    const timeOfRequest = new RegExp(formatUTCDateString(items[i].created), "i");
    const expectedCells = [checkbox, name, url, timeOfRequest];

    expect(within(row).getAllByRole("cell")).toHaveLength(expectedCells.length);
    expectedCells.forEach((cell) => {
      expect(within(row).getByRole("cell", { name: cell })).toBeInTheDocument();
    });
  });
});
