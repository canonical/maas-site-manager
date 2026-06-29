import UserList from "./UserList";

import { renderWithMemoryRouter, screen, userEvent } from "@/utils/test-utils";

const mockUseAppLayoutContext = vi.spyOn(await import("@/app/context"), "useAppLayoutContext");

const mockSetSidebar = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  mockUseAppLayoutContext.mockReturnValue({
    previousSidebar: null,
    setSidebar: mockSetSidebar,
    sidebar: null,
  });
});

describe("UserList", () => {
  describe("display", () => {
    it("displays the user list header, search box, add button, and table", () => {
      renderWithMemoryRouter(<UserList />);

      expect(screen.getByRole("heading", { name: "Users" })).toBeInTheDocument();
      expect(screen.getByRole("searchbox")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Add user" })).toBeInTheDocument();
      expect(screen.getByRole("treegrid", { name: "Users list" })).toBeInTheDocument();
    });
  });

  describe("actions", () => {
    it("opens the add user sidebar when Add user is clicked", async () => {
      renderWithMemoryRouter(<UserList />);

      await userEvent.click(screen.getByRole("button", { name: "Add user" }));

      expect(mockSetSidebar).toHaveBeenCalledWith("addUser");
    });
  });
});
