import { setupServer } from "msw/node";

import TokensCreate from "./TokensCreate";

import { tokensResolvers } from "@/testing/resolvers/tokens";
import { renderWithMemoryRouter, screen, userEvent } from "@/utils/test-utils";

const mockServer = setupServer(tokensResolvers.createTokens.handler());

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

it("renders the form", async () => {
  renderWithMemoryRouter(<TokensCreate />);
  expect(screen.getByRole("form", { name: /Generate new enrollment tokens/i })).toBeInTheDocument();
});

it("if not all required fields have been entered the submit button is disabled", async () => {
  renderWithMemoryRouter(<TokensCreate />);
  const amount = screen.getByLabelText(/Amount of tokens to generate/i);
  const expires = screen.getByLabelText(/Expiration time/i);
  expect(screen.getByRole("button", { name: /Generate 0 tokens/i })).toBeAriaDisabled();
  await userEvent.type(amount, "1");
  await userEvent.type(expires, "1 month");
  expect(screen.getByRole("button", { name: /Generate 1 token/i })).not.toBeAriaDisabled();
});

it("displays an error for invalid expiration value", async () => {
  renderWithMemoryRouter(<TokensCreate />);
  const expires = screen.getByLabelText(/Expiration time/i);
  await userEvent.type(expires, "2");
  await userEvent.tab();
  expect(expires).toHaveAccessibleErrorMessage(
    /Time unit must be a `string` type with a value of weeks, days, hours, and\/or minutes./i,
  );
});

it("does not display error message on blur if the value has not chagned", async () => {
  renderWithMemoryRouter(<TokensCreate />);
  const amount = screen.getByLabelText(/Amount of tokens to generate/i);
  await userEvent.type(amount, "{tab}");
  expect(amount).not.toHaveAccessibleErrorMessage(/Please enter a valid number/i);
  // enter a value and then delete it
  await userEvent.type(amount, "1{backspace}");
  expect(amount).toHaveAccessibleErrorMessage(/Please enter a valid number/i);
});
