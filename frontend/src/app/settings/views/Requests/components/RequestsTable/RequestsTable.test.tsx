import { setupServer } from "msw/node";

import RequestsTable from "./RequestsTable";

import { enrollmentRequestFactory } from "@/mocks/factories";
import { enrollmentRequestsResolvers } from "@/testing/resolvers/enrollmentRequests";
import { renderWithMemoryRouter, screen, waitFor } from "@/utils/test-utils";

const enrollmentRequest = enrollmentRequestFactory.build({ name: "new-maas-site" });
const enrollmentRequests = [enrollmentRequest, ...enrollmentRequestFactory.buildList(2)];

const mockServer = setupServer(
  enrollmentRequestsResolvers.listEnrollmentRequests.handler(enrollmentRequests),
  enrollmentRequestsResolvers.postEnrollmentRequests.handler(),
);

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("RequestsTable", () => {
  describe("display", () => {
    it("displays a loading component if requests are loading", async () => {
      renderWithMemoryRouter(<RequestsTable />);

      await waitFor(() => {
        expect(screen.getAllByRole("progressbar", { name: /loading/i }).length).toBeGreaterThan(0);
      });
    });

    it("displays a message when rendering an empty list", async () => {
      mockServer.use(enrollmentRequestsResolvers.listEnrollmentRequests.handler([]));

      renderWithMemoryRouter(<RequestsTable />);

      await waitFor(() => {
        expect(screen.getByText("No outstanding requests")).toBeInTheDocument();
      });
    });

    it("shows errors if present", async () => {
      mockServer.use(enrollmentRequestsResolvers.listEnrollmentRequests.error());

      renderWithMemoryRouter(<RequestsTable />);

      await waitFor(() => {
        expect(screen.getByText("Request failed with status code 401")).toBeInTheDocument();
      });
    });

    it("displays the columns correctly", async () => {
      renderWithMemoryRouter(<RequestsTable />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      ["Name", "URL", "Time of request (UTC)"].forEach((column) => {
        expect(
          screen.getByRole("columnheader", {
            name: column,
          }),
        ).toBeInTheDocument();
      });
    });
  });

  describe("actions", () => {
    it("clicking the link redirects to the correct URL", async () => {
      renderWithMemoryRouter(<RequestsTable />);

      await waitFor(() => {
        expect(screen.queryByRole("progressbar", { name: /loading/i })).not.toBeInTheDocument();
      });

      expect(screen.getByRole("link", { name: enrollmentRequest.url })).toHaveAttribute("href", enrollmentRequest.url);
    });
  });
});
