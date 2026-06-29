import { http, HttpResponse } from "msw";

import UserAddForm from "./UserAddForm";

import { userFactory } from "@/mocks/factories";
import { usersResolvers } from "@/testing/resolvers/users";
import { apiUrls } from "@/utils/test-urls";
import { render, screen, setupServer, userEvent, waitFor } from "@/utils/test-utils";

const user = userFactory.build({ is_admin: true });
const mockServer = setupServer(usersResolvers.getUser.handler([user]));

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

it("requires the password fields when adding a user", () => {
  render(<UserAddForm />);

  expect(screen.getByLabelText("Password")).toBeRequired();
  expect(screen.getByLabelText("Password (again)")).toBeRequired();
});

it("enables the submit button when all required fields are filled in and valid when editing a user", async () => {
  render(<UserAddForm />);

  expect(screen.getByRole("button", { name: "Add user" })).toBeDisabled();

  await userEvent.type(screen.getByRole("textbox", { name: "Username" }), "user1");
  await userEvent.type(screen.getByRole("textbox", { name: "Email address" }), "user1@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "testpassword");

  // Ensure form is still disabled
  expect(screen.getByRole("button", { name: "Add user" })).toBeDisabled();

  await userEvent.type(screen.getByLabelText("Password (again)"), "testpassword");

  expect(screen.getByRole("button", { name: "Add user" })).toBeEnabled();
});

it("displays an error if a username with invalid characters is entered", async () => {
  render(<UserAddForm />);

  await userEvent.type(screen.getByRole("textbox", { name: "Username" }), "not a valid username");
  await userEvent.tab();

  expect(screen.getByText(/Usernames must contain letters, digits and @\/.\/\+\/-\/_ only/i)).toBeInTheDocument();
});

it("displays an error if a username over 150 characters in length is entered", async () => {
  render(<UserAddForm />);

  // 151 characters long, max is 150
  const tooLong = "A".repeat(151);

  await userEvent.type(screen.getByRole("textbox", { name: "Username" }), tooLong);
  await userEvent.tab();

  await waitFor(() => {
    expect(screen.getByText(/Username must be 150 characters or less/i)).toBeInTheDocument();
  });
});

it("displays an error if no username is entered", async () => {
  render(<UserAddForm />);

  await userEvent.click(screen.getByRole("textbox", { name: "Username" }));
  await userEvent.tab();

  expect(screen.getByText(/Username is required/i)).toBeInTheDocument();
});

it("displays an error if an invalid email address is entered", async () => {
  render(<UserAddForm />);

  await userEvent.type(screen.getByRole("textbox", { name: "Email address" }), "not a valid email address");
  await userEvent.tab();

  expect(screen.getByText(/Must be a valid email address/i)).toBeInTheDocument();
});

it("displays an error if a password less than 8 characters in length is entered", async () => {
  render(<UserAddForm />);

  // 151 characters long, max is 150
  const tooShort = "AAAA";

  await userEvent.type(screen.getByLabelText("Password"), tooShort);
  await userEvent.tab();

  expect(screen.getByText(/Password must be at least 8 characters/i)).toBeInTheDocument();
});

it("displays an error if a password over 100 characters in length is entered", async () => {
  render(<UserAddForm />);

  // 101 characters long, max is 100
  const tooLong = "A".repeat(101);

  await userEvent.type(screen.getByLabelText("Password"), tooLong);
  await userEvent.tab();

  await waitFor(() => {
    expect(screen.getByText(/Password must be 100 characters or less/i)).toBeInTheDocument();
  });
});

it("displays an error if the password confirmation field does not match the given password", async () => {
  render(<UserAddForm />);
  await userEvent.type(screen.getByLabelText("Password"), "aValidPassword");
  await userEvent.type(screen.getByLabelText("Password (again)"), "notTheSamePassword");
  await userEvent.tab();

  expect(
    screen.getByText(/New passwords do not match. Please ensure the new passwords are the same./i),
  ).toBeInTheDocument();
});

it("shows an error message when submission fails", async () => {
  mockServer.use(
    http.post(apiUrls.users, () => {
      return new HttpResponse(null, { status: 400 });
    }),
  );
  render(<UserAddForm />);

  expect(screen.queryByText(/Error/i)).not.toBeInTheDocument();

  await userEvent.type(screen.getByRole("textbox", { name: "Username" }), "user1");
  await userEvent.type(screen.getByRole("textbox", { name: "Email address" }), "user1@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "testpassword");
  await userEvent.type(screen.getByLabelText("Password (again)"), "testpassword");

  // Simulate form submission
  await userEvent.click(screen.getByRole("button", { name: "Add user" }));

  await waitFor(() => {
    expect(screen.getByText(/Error/i)).toBeInTheDocument();
  });
  expect(screen.getByText(/Request failed with status code 400/i)).toBeInTheDocument();
});
