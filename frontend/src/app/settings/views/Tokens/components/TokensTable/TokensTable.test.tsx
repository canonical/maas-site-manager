import { setupServer } from "msw/node";

import TokensTable from "./TokensTable";

import { tokenFactory } from "@/mocks/factories";
import { tokensResolvers } from "@/testing/resolvers/tokens";
import { renderWithMemoryRouter, screen, userEvent, waitFor } from "@/utils/test-utils";

const tokens = tokenFactory.buildList(2);
const mockServer = setupServer(tokensResolvers.listTokens.handler(tokens));

beforeAll(() => {
  mockServer.listen();
});

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("TokensTable", () => {
  const props = {
    page: 1,
    debouncedPage: 1,
    size: 50,
    handlePageSizeChange: vi.fn(),
    setPage: vi.fn(),
    rowSelection: {},
    setRowSelection: vi.fn(),
  };

  describe("display", () => {
    it("displays a loading component if tokens are loading", async () => {
      renderWithMemoryRouter(<TokensTable {...props} />);

      await waitFor(() => {
        expect(screen.getAllByRole("progressbar", { name: /loading/i }).length).toBeGreaterThan(0);
      });
    });

    it("displays a message when rendering an empty list", async () => {
      mockServer.use(tokensResolvers.listTokens.handler([]));

      renderWithMemoryRouter(<TokensTable {...props} />);

      await waitFor(() => {
        expect(screen.getByText("No tokens available")).toBeInTheDocument();
      });
    });

    it("shows errors if present", async () => {
      mockServer.use(tokensResolvers.listTokens.error());

      renderWithMemoryRouter(<TokensTable {...props} />);

      await waitFor(() => {
        expect(screen.getByText("Request failed with status code 401")).toBeInTheDocument();
      });
    });

    it("displays the columns correctly", async () => {
      renderWithMemoryRouter(<TokensTable {...props} />);

      ["Token", "Time until expiration", "Created (UTC)"].forEach((column) => {
        expect(
          screen.getByRole("columnheader", {
            name: column,
          }),
        ).toBeInTheDocument();
      });
    });

    it("displays created date in UTC", async () => {
      const date = new Date("Fri Apr 21 2023 14:00:00 GMT+0200 (GMT)");
      vi.setSystemTime(date);
      const testTokens = [tokenFactory.build({ created: "2023-04-21T11:30:00.000Z" })];

      mockServer.use(tokensResolvers.listTokens.handler(testTokens));

      renderWithMemoryRouter(<TokensTable {...props} />);

      await waitFor(() => {
        expect(screen.getByText(/2023-04-21[\s\S]*11:30/i)).toBeInTheDocument();
      });
    });

    it("displays time until expiration in UTC", async () => {
      const date = new Date("Fri Apr 21 2023 14:00:00 GMT+0200 (GMT)");
      vi.setSystemTime(date);
      const testTokens = [tokenFactory.build({ expired: "2023-04-21T14:00:00.000Z" })];

      mockServer.use(tokensResolvers.listTokens.handler(testTokens));

      renderWithMemoryRouter(<TokensTable {...props} />);

      await waitFor(() => {
        expect(screen.getByText(/in[\s\S]*2 hours/i)).toBeInTheDocument();
      });
    });
  });

  describe("actions", () => {
    it("copies the token", async () => {
      const copyFn = vi.fn(() => Promise.resolve());
      const user = userEvent.setup();

      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: {
          writeText: copyFn,
        },
      });

      renderWithMemoryRouter(<TokensTable {...props} />);

      await waitFor(() => {
        expect(screen.queryAllByRole("progressbar", { name: /loading/i })).toHaveLength(0);
      });

      await user.click(screen.getByText(tokens[0].value));

      expect(copyFn).toHaveBeenCalledWith(tokens[0].value);
    });
  });
});
