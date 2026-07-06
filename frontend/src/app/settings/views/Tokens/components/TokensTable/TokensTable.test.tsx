import TokensTable from "./TokensTable";

import type { Token } from "@/app/apiclient";
import { tokenFactory } from "@/mocks/factories";
import { render, screen, within } from "@/utils/test-utils";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

it("displays the tokens table", () => {
  render(<TokensTable data={{ items: [], total: 0, page: 1, size: 0 }} error={null} isPending={false} />);

  expect(screen.getByRole("table", { name: /tokens/i })).toBeInTheDocument();
});

it("displays rows for each token", () => {
  const items = tokenFactory.buildList(1);
  render(<TokensTable data={{ items, total: 0, page: 1, size: 0 }} error={null} isPending={false} />);

  const tableBody = screen.getAllByRole("rowgroup")[1];
  expect(within(tableBody).getAllByRole("row")).toHaveLength(items.length);
  within(tableBody)
    .getAllByRole("row")
    .forEach((row, idx) => {
      expect(row).toHaveTextContent(new RegExp(items[idx].value, "i"));
    });
});

it("displays a copy button in each row", () => {
  const items = tokenFactory.buildList(1);
  render(<TokensTable data={{ items, total: 0, page: 1, size: 0 }} error={null} isPending={false} />);

  const tableBody = screen.getAllByRole("rowgroup")[1];
  within(tableBody)
    .getAllByRole("button", { name: /copy/i })
    .forEach((btn) => {
      expect(btn).toBeInTheDocument();
    });
});

it("should display a no-tokens caption if there are no tokens", () => {
  const items: Token[] = [];
  render(<TokensTable data={{ items, total: 0, page: 1, size: 0 }} error={null} isPending={false} />);

  expect(screen.getByText(/No tokens available/i)).toBeInTheDocument();
});

it("displays created date in UTC", () => {
  const date = new Date("Fri Apr 21 2023 14:00:00 GMT+0200 (GMT)");
  vi.setSystemTime(date);
  const items = [tokenFactory.build({ created: "2023-04-21T11:30:00.000Z" })];

  render(<TokensTable data={{ items, total: 0, page: 1, size: 0 }} error={null} isPending={false} />);

  expect(screen.getByText(/2023-04-21 11:30/i)).toBeInTheDocument();
});

it("displays time until expiration in UTC", () => {
  const date = new Date("Fri Apr 21 2023 14:00:00 GMT+0200 (GMT)");
  vi.setSystemTime(date);
  const items = [tokenFactory.build({ expired: "2023-04-21T14:00:00.000Z" })];

  render(<TokensTable data={{ items, total: 0, page: 1, size: 0 }} error={null} isPending={false} />);

  expect(screen.getByText(/in 2 hours/i)).toBeInTheDocument();
});
