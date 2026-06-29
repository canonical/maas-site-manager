import { http, HttpResponse } from "msw";

import UserEditForm from "./UserEditForm";

import { UserSelectionContext } from "@/app/context/UserSelectionContext";
import { userFactory } from "@/mocks/factories";
import { usersResolvers } from "@/testing/resolvers/users";
import { apiUrls } from "@/utils/test-urls";
import { render, screen, setupServer, userEvent, waitFor, waitForLoadingToFinish } from "@/utils/test-utils";

const user = userFactory.build({ is_admin: true });
const mockServer = setupServer(usersResolvers.getUser.handler([user]));

const renderEditForm = () => {
  const setSelected = vi.fn();
  return render(
    <UserSelectionContext.Provider value={{ selected: user.id, setSelected }}>
      <UserEditForm />
    </UserSelectionContext.Provider>,
  );
};

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

it("enables the submit button only when values have been changed while editing", async () => {
  renderEditForm();

  await waitForLoadingToFinish();

  await userEvent.clear(screen.getByRole("textbox", { name: "Full name (optional)" }));

  expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
});

it("makes the confirm_password field required if the password field has been filled in while editing", async () => {
  renderEditForm();

  await waitForLoadingToFinish();

  await userEvent.type(screen.getByLabelText("Password"), "testpassword");

  expect(screen.getByLabelText("Password (again)")).toBeRequired();
});

it("shows an error message when submission fails", async () => {
  mockServer.use(
    http.patch(`${apiUrls.users}/${user.id}`, () => {
      return new HttpResponse(null, { status: 400 });
    }),
  );
  renderEditForm();
  await waitForLoadingToFinish();
  expect(screen.queryByText(/Error/i)).not.toBeInTheDocument();

  await userEvent.type(screen.getByLabelText("Password"), "testpassword2");
  await userEvent.type(screen.getByLabelText("Password (again)"), "testpassword2");

  expect(screen.getByRole("button", { name: "Save" })).toBeEnabled();
  await userEvent.click(screen.getByRole("button", { name: "Save" }));

  await waitFor(() => {
    expect(screen.getByText(/Error/i)).toBeInTheDocument();
  });
  expect(screen.getByText(/Request failed with status code 400/i)).toBeInTheDocument();
});
