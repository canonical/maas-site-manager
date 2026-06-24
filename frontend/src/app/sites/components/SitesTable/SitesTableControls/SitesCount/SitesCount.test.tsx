import SitesCount from "./SitesCount";

import { render, screen } from "@/utils/test-utils";

it("displays plural sites count", () => {
  const total = 11;
  render(<SitesCount isPending={false} totalSites={total} />);

  expect(screen.getByText("11 MAAS sites")).toBeInTheDocument();
});

it("displays singular sites count", () => {
  const total = 1;
  render(<SitesCount isPending={false} totalSites={total} />);

  expect(screen.getByText("1 MAAS site")).toBeInTheDocument();
});
