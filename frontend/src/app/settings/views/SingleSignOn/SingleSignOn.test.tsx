import SingleSignOn from "./SingleSignOn";

import { oidcResolvers } from "@/testing/resolvers/oidc";
import { render, screen, setupServer, userEvent, waitFor } from "@/utils/test-utils";

// By default there is no active provider (404), so the form renders empty
const mockServer = setupServer(oidcResolvers.getActiveProvider.notFound(), oidcResolvers.createProvider.handler());

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

it("renders the single sign-on form", async () => {
  render(<SingleSignOn />);

  await waitFor(() => {
    expect(screen.getByRole("form", { name: "Single sign-on form" })).toBeInTheDocument();
  });
  expect(screen.getByRole("textbox", { name: /Name/ })).toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: /Client ID/ })).toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: /Issuer URL/ })).toBeInTheDocument();
  expect(screen.getByRole("combobox", { name: /Token type/ })).toBeInTheDocument();
});

it("shows an error notification when fetching the provider fails", async () => {
  mockServer.use(oidcResolvers.getActiveProvider.error());

  render(<SingleSignOn />);

  await waitFor(() => {
    expect(screen.getByText("Error while fetching OIDC provider")).toBeInTheDocument();
  });
});

it("shows validation errors for required fields", async () => {
  render(<SingleSignOn />);

  const nameField = await screen.findByRole("textbox", { name: /Name/ });
  await userEvent.click(nameField);
  await userEvent.tab();

  await waitFor(() => {
    expect(screen.getByText("Name is a required field.")).toBeInTheDocument();
  });
});

it("keeps the save button disabled until the form is valid and dirty", async () => {
  render(<SingleSignOn />);

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  await userEvent.type(screen.getByRole("textbox", { name: /Name/ }), "My provider");
  await userEvent.type(screen.getByRole("textbox", { name: /Client ID/ }), "client-id");
  await userEvent.type(screen.getByLabelText(/Client secret/), "client-secret");
  await userEvent.type(screen.getByRole("textbox", { name: /Issuer URL/ }), "https://issuer.example.com");

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
  });
});
