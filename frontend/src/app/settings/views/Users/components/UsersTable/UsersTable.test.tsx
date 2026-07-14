import UsersTable from "./UsersTable";

import { mockUsers, usersResolvers } from "@/testing/resolvers/users";
import {
  mockSidePanel,
  renderWithMemoryRouter,
  screen,
  setupServer,
  userEvent,
  waitFor,
  within,
} from "@/utils/test-utils";

const mockServer = setupServer(usersResolvers.listUsers.handler(), usersResolvers.getCurrentUser.handler(mockUsers[0]));

const { mockOpen } = await mockSidePanel();

const mockUseUserSelectionContext = vi.spyOn(await import("@/app/context"), "useUserSelectionContext");
const mockUseNavigate = vi.spyOn(await import("@/utils/router"), "useNavigate");

const mockSetSelectedUserId = vi.fn();
const mockNavigate = vi.fn();

beforeAll(() => {
  mockServer.listen();
});

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();

  mockUseUserSelectionContext.mockReturnValue({
    selected: null,
    setSelected: mockSetSelectedUserId,
  });
  mockUseNavigate.mockReturnValue(mockNavigate);
});

afterEach(() => {
  vi.useRealTimers();
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("UsersTable", () => {
  describe("display", () => {
    it("displays a loading component if users are loading", async () => {
      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.getAllByRole("progressbar", { name: /loading/i }).length).toBeGreaterThan(0);
      });
    });

    it("displays a message when rendering an empty list", async () => {
      mockServer.use(usersResolvers.listUsers.handler([]));

      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.getByText("No users found.")).toBeInTheDocument();
      });
    });

    it("shows errors if present", async () => {
      mockServer.use(usersResolvers.listUsers.error());

      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.getByText("Request failed with status code 401")).toBeInTheDocument();
      });
    });

    it("displays the columns correctly", async () => {
      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Username/i })).toBeInTheDocument();
      });
      expect(screen.getByRole("button", { name: /Full name/i })).toBeInTheDocument();

      ["Email", "Role", "Actions"].forEach((column) => {
        expect(
          screen.getByRole("columnheader", {
            name: new RegExp(`^${column}`, "i"),
          }),
        ).toBeInTheDocument();
      });
    });

    it("can switch between username and full name display", async () => {
      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      let tableBody = screen.getAllByRole("rowgroup")[1];
      within(tableBody)
        .getAllByRole("row")
        .forEach((row, index) => {
          expect(within(row).getAllByRole("gridcell")[0]).toHaveTextContent(mockUsers[index].username);
        });

      await userEvent.click(screen.getByRole("button", { name: "Full name" }));

      tableBody = screen.getAllByRole("rowgroup")[1];
      within(tableBody)
        .getAllByRole("row")
        .forEach((row, index) => {
          const fullName = mockUsers[index].full_name as string;
          expect(within(row).getAllByRole("gridcell")[0]).toHaveTextContent(fullName || "—");
        });
    });
  });

  describe("actions", () => {
    it("opens the edit user sidebar and selects the user when edit is clicked", async () => {
      const editableUser = mockUsers[1];
      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      const row = within(screen.getAllByRole("rowgroup")[1]).getByRole("row", {
        name: new RegExp(editableUser.username, "i"),
      });

      await userEvent.click(within(row).getByRole("button", { name: /Edit/ }));

      expect(mockSetSelectedUserId).toHaveBeenCalledWith(editableUser.id);
      expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Edit user" }));
    });

    it("redirects to personal details if a user tries to edit themselves", async () => {
      const currentUser = mockUsers[0];
      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      const row = within(screen.getAllByRole("rowgroup")[1]).getByRole("row", {
        name: new RegExp(currentUser.username, "i"),
      });

      await userEvent.click(within(row).getByRole("button", { name: /Edit/ }));

      expect(mockNavigate).toHaveBeenCalledWith("/account/details");
      expect(mockSetSelectedUserId).not.toHaveBeenCalled();
      expect(mockOpen).not.toHaveBeenCalled();
    });

    it("disables delete and shows a tooltip if a user tries to delete themselves", async () => {
      const currentUser = mockUsers[0];
      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      const row = within(screen.getAllByRole("rowgroup")[1]).getByRole("row", {
        name: new RegExp(currentUser.username, "i"),
      });
      const deleteButton = within(row).getByRole("button", { name: /Delete/ });

      expect(deleteButton).toBeAriaDisabled();

      await userEvent.hover(deleteButton);

      await waitFor(() => {
        expect(screen.getByRole("tooltip", { name: "You cannot delete your own user." })).toBeInTheDocument();
      });
    });

    it("opens the delete user sidebar and selects a different user when delete is clicked", async () => {
      const editableUser = mockUsers[1];
      renderWithMemoryRouter(<UsersTable debounceSearchText="" />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      const row = within(screen.getAllByRole("rowgroup")[1]).getByRole("row", {
        name: new RegExp(editableUser.username, "i"),
      });

      await userEvent.click(within(row).getByRole("button", { name: /Delete/ }));

      expect(mockSetSelectedUserId).toHaveBeenCalledWith(editableUser.id);
      expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Delete user" }));
    });
  });
});
