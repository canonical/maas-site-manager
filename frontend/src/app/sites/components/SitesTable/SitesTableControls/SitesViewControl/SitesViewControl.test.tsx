import SitesViewControl from "./SitesViewControl";

import { routesConfig } from "@/app/base/routes";
import { renderWithMemoryRouter, screen, waitFor } from "@/utils/test-utils";

describe("sites view control", () => {
  it("renders a sites view control tablist", () => {
    renderWithMemoryRouter(<SitesViewControl />);

    expect(
      screen.getByRole("tablist", {
        name: /sites view control/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /map/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /table/i })).toBeInTheDocument();
  });

  it("points to the appropriate route for each tab", async () => {
    renderWithMemoryRouter(<SitesViewControl />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /map/i })).toHaveAttribute("href", routesConfig.sitesMap.path);
    });
    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /table/i })).toHaveAttribute("href", routesConfig.sitesList.path);
    });
  });
});
