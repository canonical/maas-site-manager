import NoSites from "./NoSites";

import { enrollmentRequestFactory } from "@/mocks/factories";
import { enrollmentRequestsResolvers } from "@/testing/resolvers/enrollmentRequests";
import { getByTextContent, renderWithMemoryRouter, screen, setupServer, waitFor } from "@/utils/test-utils";

const renderComponent = () => renderWithMemoryRouter(<NoSites />);

const enrollmentRequests = enrollmentRequestFactory.buildList(2);
const mockServer = setupServer(enrollmentRequestsResolvers.listEnrollmentRequests.handler(enrollmentRequests));

beforeAll(() => {
  mockServer.listen();
});
afterEach(() => {
  mockServer.resetHandlers();
});
afterAll(() => {
  mockServer.close();
});

it("should display 'no enrolled sites' text", () => {
  renderComponent();
  expect(screen.getByText(/no enrolled maas sites/i)).toBeInTheDocument();
});
it("should display link to enrollment docs", () => {
  renderComponent();

  expect(
    screen.getByRole("link", { name: /learn more about the enrollment process in the documentation\./i }),
  ).toBeInTheDocument();
});

it("should display a link to the request page if there are open requests", async () => {
  renderComponent();
  await waitFor(() => {
    expect(
      screen.getByRole("link", {
        name: /go to requests page/i,
      }),
    ).toBeInTheDocument();
  });
});

it("should display the amount of open enrollment requests", async () => {
  renderComponent();
  await waitFor(() => {
    expect(
      getByTextContent(new RegExp("You have 2 open enrollment requests, inspect them in the Requests page.", "i")),
    ).toBeInTheDocument();
  });
});

it("should display a link to the tokens page if no enrollment requests are open", async () => {
  mockServer.resetHandlers(enrollmentRequestsResolvers.listEnrollmentRequests.handler());
  renderComponent();
  await waitFor(() => {
    expect(
      screen.getByRole("link", {
        name: /go to tokens page/i,
      }),
    ).toBeInTheDocument();
  });
});
