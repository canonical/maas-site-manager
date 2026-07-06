import { humanIntervalToISODuration } from "./utils";

it("returns a valid ISO duration string for weeks, days, hours and seconds", () => {
  expect(humanIntervalToISODuration("5 weeks 7 days 3 hours 30 seconds")).toEqual("P42DT3H0M30S");
});
it("returns a valid ISO duration string for weeks", () => {
  expect(humanIntervalToISODuration("2 weeks")).toEqual("P14DT0H0M0S");
});
it("returns a valid ISO duration string for hours and seconds", () => {
  expect(humanIntervalToISODuration("1 hours 10 seconds")).toEqual("P0DT1H0M10S");
});
