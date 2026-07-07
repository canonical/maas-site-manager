import { http, HttpResponse } from "msw";

import EnrollmentActions from "./EnrollmentActions";

import { enrollmentRequestsResolvers } from "@/testing/resolvers/enrollmentRequests";
import { apiUrls } from "@/utils/test-urls";
import { renderWithMemoryRouter, screen, setupServer, userEvent, waitFor, within } from "@/utils/test-utils";

const mockServer = setupServer(enrollmentRequestsResolvers.postEnrollmentRequests.handler());

vi.mock("@/app/context", async () => {
  const actual = await vi.importActual("@/app/context");
  return {
    ...actual!,
    useRowSelection: () => ({
      rowSelection: {
        "1": true,
        "2": true,
      },
    }),
  };
});

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

it("displays enrollment action buttons", () => {
  renderWithMemoryRouter(<EnrollmentActions />);

  expect(screen.getByRole("button", { name: /Deny/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Accept/i })).toBeInTheDocument();
});

it("can display an error message on request error", async () => {
  mockServer.use(
    http.post(apiUrls.enrollmentRequests, () => {
      return HttpResponse.json(null, { status: 400 });
    }),
  );
  renderWithMemoryRouter(<EnrollmentActions />);

  await userEvent.click(screen.getByRole("button", { name: /Accept/i }));

  await waitFor(() => {
    expect(
      within(screen.getByRole("alert")).getByText(/There was an error processing enrollment request/i),
    ).toBeInTheDocument();
  });
});
