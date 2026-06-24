import AggregatedStats from "./AggregatedStatus";

import { statsFactory } from "@/mocks/factories";
import { render, screen, userEvent } from "@/utils/test-utils";

it("displays correct number of deployed machines", async () => {
  render(
    <AggregatedStats
      stats={statsFactory.build({
        machines_total: 1000,
        machines_deployed: 100,
        machines_allocated: 200,
        machines_ready: 300,
        machines_error: 400,
      })}
    />,
  );

  await userEvent.click(screen.getByRole("button", { name: /100 of 1000 deployed/i }));
  expect(screen.getByTestId("deployed")).toHaveTextContent("100");
  expect(screen.getByTestId("allocated")).toHaveTextContent("200");
  expect(screen.getByTestId("ready")).toHaveTextContent("300");
  expect(screen.getByTestId("error")).toHaveTextContent("400");
});
