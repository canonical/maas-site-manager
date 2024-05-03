import type { SortingState } from "@tanstack/react-table";

import {
  getTimezoneUTCString,
  parseSearchTextToQueryParams,
  getTimeInTimezone,
  formatDistanceToNow,
  getSortBy,
  computeMinZoom,
  unsecureCopyToClipboard,
} from "./utils";

import { TimeZone } from "@/api/client";

beforeEach(() => {
  const date = new Date("Fri Apr 21 2023 12:00:00 GMT+0100 (GMT)");
  vi.setSystemTime(date);
});

afterEach(() => {
  vi.useRealTimers();
});

it('should modify search params from "label:value" to "label=value"', () => {
  const searchText = "country:cuba";
  const queryParams = parseSearchTextToQueryParams(searchText);
  expect(queryParams.includes(":")).toBe(false);
  expect(queryParams.includes("=")).toBe(true);
  expect(queryParams).toBe("country=cuba");
});

it("should modify multiple search params", () => {
  const searchText = "country:cuba city:paris";
  const queryParams = parseSearchTextToQueryParams(searchText);
  const expectedResponse = "country=cuba&city=paris";
  expect(queryParams).toBe(expectedResponse);
});

[
  [TimeZone.CANADA_NEWFOUNDLAND, "-2:30"],
  [TimeZone.UTC, ""],
  [TimeZone.EUROPE_LONDON, "+1"],
].forEach(([timezone, expected]) => {
  it(`returns ${expected} for ${timezone}`, () => {
    const result = getTimezoneUTCString(timezone as TimeZone);
    expect(result).toBe(expected);
  });
});

[
  [TimeZone.CANADA_NEWFOUNDLAND, "09:30"],
  [TimeZone.UTC, "12:00"],
  [TimeZone.EUROPE_WARSAW, "14:00"],
  [TimeZone.EUROPE_LONDON, "13:00"],
].forEach(([timezone, expected]) => {
  it(`returns ${expected} for ${timezone}`, () => {
    const result = getTimeInTimezone(new Date("2000-01-01T12:00:00Z"), timezone as TimeZone);
    expect(result).toBe(expected);
  });
});

[
  ["2023-04-21T10:30:00.000Z", "30 minutes ago"],
  ["2023-04-21T11:15:00.000Z", "in 15 minutes"],
].forEach(([time, expected]) => {
  it(`returns ${expected} time distance for ${time}`, () => {
    const result = formatDistanceToNow(time);
    expect(result).toBe(expected);
  });
});

const sortingState: SortingState = [{ id: "name", desc: false }];

it("returns a sort key as a string", () => {
  const sortKey = getSortBy(sortingState);
  expect(sortKey).toStrictEqual("name-asc");
});

it("calculates the minimum zoom correctly for various screen sizes (computeMinZoom)", () => {
  // Desktop
  expect(computeMinZoom({ screenWidth: 1440, screenHeight: 1055 })).toEqual(3);
  // Tablet
  expect(computeMinZoom({ screenWidth: 829, screenHeight: 1180 })).toEqual(3);
  // Mobile
  expect(computeMinZoom({ screenWidth: 390, screenHeight: 844 })).toEqual(2);
});

it("copies a text string unsecurely", () => {
  const originalExecCommand = document.execCommand;
  document.execCommand = vi.fn(() => true);
  unsecureCopyToClipboard("test");
  expect(document.execCommand).toHaveBeenCalledWith("copy");
  document.execCommand = originalExecCommand;
});
