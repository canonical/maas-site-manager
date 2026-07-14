import { http, HttpResponse } from "msw";

import SiteSummary from "./SiteSummary";

import { SiteMarkerSvg } from "@/app/sites/views/SitesMap/components/Map/SiteMarker/SiteMarker";
import { siteFactory, statsFactory } from "@/mocks/factories";
import { sitesResolvers } from "@/testing/resolvers/sites";
import { apiUrls } from "@/utils/test-urls";
import {
  fireEvent,
  mockSidePanel,
  renderWithMemoryRouter,
  screen,
  setupServer,
  userEvent,
  waitFor,
} from "@/utils/test-utils";

const { mockOpen } = await mockSidePanel();

const stats = statsFactory.build();
const site = siteFactory.build({ url: "https://example.com", stats });
const mockServer = setupServer(sitesResolvers.getSite.handler([site]));

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

it("displays data for a site", async () => {
  renderWithMemoryRouter(<SiteSummary id={site.id} />);

  await waitFor(() => {
    expect(screen.getByText(site.name)).toBeInTheDocument();
  });

  expect(screen.getByRole("link", { name: site.url })).toBeInTheDocument();
  expect(screen.getByText(new RegExp(site.connection_status, "i"))).toBeInTheDocument();
  expect(screen.getByText(stats.machines_total)).toBeInTheDocument();

  await userEvent.click(screen.getByTestId("popover-container"));

  expect(screen.getByTestId("deployed")).toHaveTextContent(stats.machines_deployed.toString());
  expect(screen.getByTestId("allocated")).toHaveTextContent(stats.machines_allocated.toString());
  expect(screen.getByTestId("ready")).toHaveTextContent(stats.machines_ready.toString());
  expect(screen.getByTestId("error")).toHaveTextContent(stats.machines_error.toString());
});

it("displays an error notification when site fetch fails", async () => {
  mockServer.use(
    http.get(`${apiUrls.sites}/:id`, () => {
      return new HttpResponse(null, { status: 500 });
    }),
  );

  renderWithMemoryRouter(<SiteSummary id={site.id} />);

  await waitFor(() => {
    expect(screen.getByText("Error while fetching site")).toBeInTheDocument();
  });
});

it("opens the edit site sidebar when the edit button is clicked", async () => {
  renderWithMemoryRouter(<SiteSummary id={site.id} />);

  await waitFor(() => {
    expect(screen.getByText(site.name)).toBeInTheDocument();
  });

  await userEvent.click(screen.getByRole("button", { name: "Edit" }));

  expect(mockOpen).toHaveBeenCalledWith(expect.objectContaining({ title: "Edit site" }));
});

it("keeps the increased marker size when hovering over the site summary", async () => {
  renderWithMemoryRouter(
    <>
      <SiteSummary id={site.id} />
      <SiteMarkerSvg id={site.id} />
    </>,
  );

  // fireEvent is needed here since userEvent.hover does not trigger onMouseOver
  // eslint-disable-next-line testing-library/prefer-user-event
  fireEvent.mouseOver(screen.getByRole("group", { name: "Site details" }));
  await waitFor(() => {
    expect(screen.getByLabelText("site location marker")).toHaveClass("site-marker--active");
  });
});

it("restores the original marker style on unmount", async () => {
  renderWithMemoryRouter(<SiteMarkerSvg id={site.id} />);

  const { unmount } = renderWithMemoryRouter(<SiteSummary id={site.id} />);

  // fireEvent is needed here since userEvent.hover does not trigger onMouseOver
  // eslint-disable-next-line testing-library/prefer-user-event
  fireEvent.mouseOver(screen.getByRole("group", { name: "Site details" }));
  await waitFor(() => {
    expect(screen.getByLabelText("site location marker")).toHaveClass("site-marker--active");
  });

  unmount();

  await waitFor(() => {
    expect(screen.getByLabelText("site location marker")).not.toHaveClass("site-marker--active");
  });
});
