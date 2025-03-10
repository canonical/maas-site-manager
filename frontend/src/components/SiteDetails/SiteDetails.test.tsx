import type { ReactNode } from "react";

import { rest } from "msw";

import { SiteMarkerSvg } from "../Map/SiteMarker/SiteMarker";

import SiteDetails from "./SiteDetails";

import { SiteDetailsContext } from "@/context/SiteDetailsContext";
import { siteFactory, statsFactory } from "@/mocks/factories";
import { createMockSiteResolver } from "@/mocks/resolvers";
import { getCountryName, getTimeInTimezone, getTimezoneUTCString } from "@/utils";
import { apiUrls } from "@/utils/test-urls";
import { screen, renderWithMemoryRouter, setupServer, waitFor, getByTextContent } from "@/utils/test-utils";

const stats = statsFactory.build();
const site = siteFactory.build({ stats });
const mockServer = setupServer(rest.get(`${apiUrls.sites}/:id`, createMockSiteResolver([site])));

const renderForm = (children?: ReactNode) => {
  return renderWithMemoryRouter(
    <SiteDetailsContext.Provider value={{ selected: site.id, setSelected: vi.fn() }}>
      <SiteDetails />
      {children}
    </SiteDetailsContext.Provider>,
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

it("renders the correct details for a site", async () => {
  renderForm();

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: site.name })).toBeInTheDocument();
  });
  expect(screen.getByRole("link", { name: site.url })).toHaveAttribute("href", site.url);

  const country = getCountryName(site.country!) as string;

  expect(screen.getByText(new RegExp(site.connection_status, "i"))).toBeInTheDocument();
  expect(screen.getByText(country)).toBeInTheDocument();
  expect(screen.getByText(site.state!)).toBeInTheDocument();
  expect(screen.getByText(site.address!)).toBeInTheDocument();
  expect(screen.getByText(site.city!)).toBeInTheDocument();
  expect(screen.getByText(site.postal_code!)).toBeInTheDocument();
  expect(
    getByTextContent(`${getTimeInTimezone(new Date(), site.timezone!)} UTC${getTimezoneUTCString(site.timezone!)}`),
  ).toBeInTheDocument();
  expect(screen.getByText(stats.machines_total)).toBeInTheDocument();

  expect(screen.getByTestId("deployed-machines")).toHaveTextContent(stats.machines_deployed.toString());
  expect(screen.getByTestId("allocated-machines")).toHaveTextContent(stats.machines_allocated.toString());
  expect(screen.getByTestId("ready-machines")).toHaveTextContent(stats.machines_ready.toString());
  expect(screen.getByTestId("error-machines")).toHaveTextContent(stats.machines_error.toString());
});

it("keeps the increased map marker size when the side panel is open", async () => {
  renderWithMemoryRouter(<SiteMarkerSvg id={site.id} />);

  renderForm();

  await waitFor(() => {
    expect(screen.getByLabelText("site location marker")).toHaveClass("site-marker--active");
  });
});

it("restores the original marker style on unmount", async () => {
  renderWithMemoryRouter(<SiteMarkerSvg id={site.id} />);

  const { unmount } = renderForm();

  await waitFor(() => {
    expect(screen.getByLabelText("site location marker")).toHaveClass("site-marker--active");
  });

  unmount();

  await waitFor(() => {
    expect(screen.getByLabelText("site location marker")).not.toHaveClass("site-marker--active");
  });
});
