import * as Sentry from "@sentry/browser";
import type { SortingState } from "@tanstack/react-table";
import { formatDistanceToNowStrict, parseISO } from "date-fns";
import { getTimezoneOffset, format, utcToZonedTime } from "date-fns-tz";
import * as countries from "i18n-iso-countries";
import { getName } from "i18n-iso-countries";
import en from "i18n-iso-countries/langs/en.json";
import pick from "lodash/fp/pick";

import type { SiteCoordinates, TimeZone } from "@/api/client";
import type { SiteMarkerType } from "@/components/Map/types";

if (typeof window !== "undefined") {
  countries.registerLocale(en);
}

export const getCountryName = (countryCode: string) => {
  return getName(countryCode, "en", { select: "official" });
};

export const parseSearchTextToQueryParams = (text: string) => {
  // if text:result => text=result
  if (!text) return "";
  const parsedText = text
    .split(" ")
    .map((item) => (item.includes(":") ? item.replaceAll(":", "=") : ""))
    .join("&");
  if (parsedText.at(-1) === "&") {
    return parsedText.substring(0, parsedText.length - 1);
  }
  return parsedText;
};

/**
 * Parses a search string into URL parameters for free text search, e.g:
 * "Bob Smith" would become "bob+smith"
 * @param text The text to be parsed
 */
export const parseSearchTextToUrlFreeTextSearch = (text: string) => {
  return text.replaceAll(" ", "+");
};

export const formatDistanceToNow = (dateString: string) =>
  formatDistanceToNowStrict(parseISO(dateString), {
    addSuffix: true,
  });

export const getTimezoneUTCString = (timezone: TimeZone, date?: Date | number) => {
  const offset = getTimezoneOffset(timezone, date);
  const sign = offset < 0 ? "-" : "+";
  const absOffset = Math.abs(offset);
  const minutes = Math.floor(absOffset / 60000) % 60;
  const hours = Math.floor(absOffset / 60000 / 60);
  if (absOffset > 0) {
    return `${sign}${hours}` + (minutes > 0 ? `:${minutes}` : "");
  } else {
    return "";
  }
};

export const formatSiteMarker = (site: SiteCoordinates): SiteMarkerType => ({
  id: site.id,
  position: site.coordinates as SiteMarkerType["position"],
});

export const getTimeInTimezone = (date: Date, timezone: TimeZone) => {
  const time = date.getTime() + getTimezoneOffset(timezone);
  const hours = `${new Date(time).getUTCHours()}`.padStart(2, "0");
  const minutes = `${new Date(time).getUTCMinutes()}`.padStart(2, "0");
  return hours + ":" + minutes;
};

export const formatUTCDateString = (dateString: string) =>
  format(utcToZonedTime(parseISO(dateString), "UTC"), "yyyy-MM-dd HH:mm", { timeZone: "UTC" });

export const unsecureCopyToClipboard = (text: string, callback?: (text: string) => void) => {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    // TODO: Investigate replacement for document.execCommand https://warthogs.atlassian.net/browse/MAASENG-3110
    document.execCommand("copy");
    callback && callback(text);
  } catch (error) {
    Sentry.captureException(new Error("unsecure copy to clipboard failed", { cause: error }));
  } finally {
    document.body.removeChild(textArea);
  }
};

export const copyToClipboard = (text: string, callback?: (text: string) => void) => {
  if (!navigator.clipboard) {
    unsecureCopyToClipboard(text, callback);
    return;
  }
  navigator.clipboard
    .writeText(text)
    .then(() => {
      callback && callback(text);
    })
    .catch((error) => {
      Sentry.captureException(new Error("copy to clipboard failed", { cause: error }));
    });
};

export const getSortBy = (sorting: SortingState) => {
  if (sorting.length !== 1) {
    return null;
  }
  const key = sorting[0].id;
  return `${key}-${sorting[0].desc ? "desc" : "asc"}`;
};

export const saveToFile = (data: BlobPart, filename: string, type: string): void => {
  const blob = new Blob([data], { type });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
};

export const computeMinZoom = ({
  screenWidth,
  screenHeight,
}: {
  screenWidth: number;
  screenHeight: number;
}): number => {
  return Math.ceil(Math.log2(Math.max(screenWidth, screenHeight) / 256));
};

export const createAccessor =
  <T, K extends keyof T>(keys: K[] | K) =>
  (obj: T) =>
    pick(keys, obj);
