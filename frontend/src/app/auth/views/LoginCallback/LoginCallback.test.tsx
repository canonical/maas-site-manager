import LoginCallback, { Labels } from "./LoginCallback";

import { AuthContextProvider } from "@/app/context";
import { oidcResolvers } from "@/testing/resolvers/oidc";
import { RouterProvider, createMemoryRouter } from "@/utils/router";
import { Providers, render, screen, setupServer, waitFor } from "@/utils/test-utils";

const mockServer = setupServer(oidcResolvers.getCallback.handler());

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
  localStorage.clear();
});

afterAll(() => {
  mockServer.close();
});

const renderCallback = (initialEntries: string[]) => {
  const router = createMemoryRouter([{ path: "*", element: <LoginCallback /> }], { initialEntries });
  render(
    <Providers>
      <AuthContextProvider>
        <RouterProvider router={router} />
      </AuthContextProvider>
    </Providers>,
  );
  return { router };
};

it("shows an error if the code or state params are missing", () => {
  renderCallback(["/login/oidc/callback?code=abc123"]);
  expect(screen.getByRole("alert")).toHaveTextContent(Labels.MissingParams);
});

it("shows an error if callback fails due to a server error", async () => {
  mockServer.use(oidcResolvers.getCallback.error());
  renderCallback(["/login/oidc/callback?code=abc123&state=xyz789"]);
  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent(Labels.CallbackError);
  });
  expect(screen.getByRole("alert")).toHaveTextContent("Please try logging in again.");
});

it("shows an error if the callback URL contains an error parameter", async () => {
  renderCallback(["/login/oidc/callback?error=access_denied&error_description=User%20denied%20access"]);
  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent("Error: access_denied");
  });
  expect(screen.getByRole("alert")).toHaveTextContent("Please try logging in again.");
  expect(screen.getByRole("alert")).toHaveTextContent("User denied access");
  expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
});

it("shows a loading state while processing the callback", () => {
  renderCallback(["/login/oidc/callback?code=abc123&state=xyz789"]);
  expect(screen.getByText("Loading...")).toBeInTheDocument();
});

it("redirects to the sites page if already authenticated", async () => {
  localStorage.setItem("jwtToken", JSON.stringify("mock-token"));
  const { router } = renderCallback(["/login/oidc/callback?code=abc123&state=xyz789"]);
  await waitFor(() => {
    expect(screen.getByText(Labels.AlreadyAuthenticated)).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/sites");
  });
});
