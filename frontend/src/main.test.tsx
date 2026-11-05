import { act, waitFor, setupServer } from "@/utils/test-utils";

const mockServer = setupServer();

beforeAll(() => {
  mockServer.listen();

  const rootElement = document.createElement("div");
  rootElement.setAttribute("id", "root");
  document.body.appendChild(rootElement);
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(async () => {
  // Dynamic import: main.tsx mounts on load, so it must not run before beforeAll creates #root.
  // This resolves to the already-loaded module from the test.
  // Unmount inside act() so React flushes pending work while jsdom's `window` still exists.
  const { root } = await import("./main");
  act(() => {
    root.unmount();
  });
  mockServer.close();
});

it("renders the app in the root element", async () => {
  await act(() => import("./main"));
  const container = document.getElementById("root") as HTMLElement;
  await waitFor(() => {
    expect(container.querySelector(".l-application")).toBeInTheDocument();
  });
});
