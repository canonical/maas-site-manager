import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import TokensList from "./TokensList";

import { tokenFactory } from "@/mocks/factories";
import { tokensResolvers } from "@/testing/resolvers/tokens";
import { apiUrls } from "@/utils/test-urls";
import { waitFor, screen, renderWithMemoryRouter, within, userEvent } from "@/utils/test-utils";

const tokens = tokenFactory.buildList(2);
const mockServer = setupServer(
  tokensResolvers.listTokens.handler(tokens),
  tokensResolvers.exportTokens.handler(),
  tokensResolvers.deleteTokens.handler(),
);

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("TokensList", () => {
  describe("display", () => {
    it("displays table with tokens", async () => {
      renderWithMemoryRouter(<TokensList />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getAllByRole("rowgroup")).toHaveLength(2);
      });

      const tableBody = screen.getAllByRole("rowgroup")[1];

      expect(within(tableBody).getAllByRole("row")).toHaveLength(tokens.length);
      within(tableBody)
        .getAllByRole("row")
        .forEach((row, idx) => {
          expect(row).toHaveTextContent(new RegExp(tokens[idx].value, "i"));
        });
    });

    it("displays a token count description", async () => {
      renderWithMemoryRouter(<TokensList />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      expect(screen.getByText(/showing 2 out of 2 tokens/i)).toBeInTheDocument();
    });
  });

  describe("actions", () => {
    it("disables the Delete button if no rows are selected", async () => {
      renderWithMemoryRouter(<TokensList />);

      expect(screen.getByRole("button", { name: "Delete" })).toBeAriaDisabled();

      await userEvent.click(screen.getAllByRole("checkbox")[0]);

      expect(screen.getByRole("button", { name: "Delete" })).not.toBeAriaDisabled();
    });

    it("keeps the Export button enabled and updates the export count after row selection", async () => {
      renderWithMemoryRouter(<TokensList />);

      expect(screen.getByRole("button", { name: /Export all tokens/i })).not.toBeAriaDisabled();

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });
      await userEvent.click(screen.getAllByRole("checkbox")[1]);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Export 1 token/i })).not.toBeAriaDisabled();
      });
    });

    it("displays a notification after a successful single deletion", async () => {
      renderWithMemoryRouter(<TokensList />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      await userEvent.click(screen.getAllByRole("checkbox")[1]);
      await userEvent.click(screen.getByRole("button", { name: /delete/i }));

      expect(
        screen.getByRole("heading", {
          name: /deleted/i,
        }),
      ).toBeInTheDocument();
      expect(screen.getByText(/an enrollment token was deleted\./i)).toBeInTheDocument();
    });

    it("displays a different notification for multiple deletions", async () => {
      renderWithMemoryRouter(<TokensList />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      const checkboxes = screen.getAllByRole("checkbox");
      await userEvent.click(checkboxes[1]);
      await userEvent.click(checkboxes[2]);
      await userEvent.click(screen.getByRole("button", { name: /delete/i }));

      await waitFor(() => {
        expect(screen.getByText(/2 enrollment tokens were deleted\./i)).toBeInTheDocument();
      });
    });

    it("displays an error notification after failed deletion", async () => {
      mockServer.use(
        tokensResolvers.listTokens.handler(tokens),
        http.delete(apiUrls.tokens, () => new HttpResponse(null, { status: 400, statusText: "BAD REQUEST" })),
      );
      renderWithMemoryRouter(<TokensList />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      await userEvent.click(screen.getAllByRole("checkbox")[1]);
      await userEvent.click(screen.getByRole("button", { name: /delete/i }));

      await waitFor(() => {
        expect(
          screen.getByRole("heading", {
            name: /error/i,
          }),
        ).toBeInTheDocument();
      });
    });
  });
});
