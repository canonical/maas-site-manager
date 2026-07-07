import UserList from "./UserList";

import { renderWithMemoryRouter, screen, userEvent } from "@/utils/test-utils";

const { mockOpenSidePanel, mockCloseSidePanel } = vi.hoisted(() => ({
  mockOpenSidePanel: vi.fn(),
  mockCloseSidePanel: vi.fn(),
}));

vi.mock("@canonical/maas-react-components", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    useSidePanel: () => ({
      openSidePanel: mockOpenSidePanel,
      closeSidePanel: mockCloseSidePanel,
      setSidePanelSize: vi.fn(),
      isOpen: false,
      title: "",
      size: "regular" as const,
      component: null,
      props: {},
    }),
  };
});

beforeEach(() => {
  vi.clearAllMocks();
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

      expect(mockOpenSidePanel).toHaveBeenCalledWith(expect.objectContaining({ title: "Add user" }));
    });
  });
});
