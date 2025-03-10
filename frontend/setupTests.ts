import { config } from "dotenv";
import { expect, afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import matchers from "@testing-library/jest-dom/matchers";
import { fetch, Request, Response } from "@remix-run/web-fetch";
import { TextEncoder as NodeTextEncoder, TextDecoder as NodeTextDecoder } from "util";
import { AbortSignal as NodeAbortSignal, AbortController as NodeAbortController } from "abort-controller";
import "vitest-canvas-mock";
import "vitest-webgl-canvas-mock";
import { mockResizeObserver, configMocks } from "jsdom-testing-mocks";
import "@/testing/customMatchers";

config();
configMocks({ beforeEach, afterEach, afterAll });

// extends Vitest's expect method with methods from react-testing-library
expect.extend(matchers);

// use the Web Fetch API in tests which is used by Remix
// expect errors, Web Fetch API types differ from jsdom implementation
// https://github.com/remix-run/react-router/blob/b154367/packages/router/__tests__/setup.ts
// @ts-expect-error
if (globalThis.fetch !== fetch) {
  // Built-in lib.dom.d.ts expects `fetch(Request | string, ...)` but the web
  // fetch API allows a URL so @remix-run/web-fetch defines
  // `fetch(string | URL | Request, ...)`
  // @ts-expect-error
  globalThis.fetch = fetch;
  // Same as above, lib.dom.d.ts doesn't allow a URL to the Request constructor
  // @ts-expect-error
  globalThis.Request = Request;
  // web-std/fetch Response does not currently implement Response.error()
  // @ts-expect-error
  globalThis.Response = Response;
}

if (!globalThis.AbortController) {
  // @ts-expect-error
  globalThis.AbortController = NodeAbortController;
}

if (!globalThis.AbortSignal) {
  // @ts-expect-error
  globalThis.AbortSignal = NodeAbortSignal;
}

if (!globalThis.TextEncoder || !globalThis.TextDecoder) {
  globalThis.TextEncoder = NodeTextEncoder;
  // @ts-expect-error
  globalThis.TextDecoder = NodeTextDecoder;
}

if (!globalThis.URL.createObjectURL) {
  window.URL.createObjectURL = vi.fn();
}

Object.defineProperty(window, "scrollTo", { value: vi.fn(), writable: true });

const originalObserver = window.ResizeObserver;

globalThis.__ROOT_PATH__ = "";

beforeAll(() => {
  // fail a test whenver console.error is called
  // enabled on CI only as it's noisy and not helpful during development
  if (process.env.CI) {
    vi.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
      throw new Error(args.join(" "));
    });
  }

  // simulate reduced motion enabled
  vi.stubGlobal("matchMedia", (query: string) =>
    query === "(prefers-reduced-motion)" ? { matches: true } : { matches: false },
  );
  vi.stubGlobal("AbortController", NodeAbortController);
});

beforeEach(() => {
  mockResizeObserver();
});

afterEach(() => {
  window.ResizeObserver = originalObserver;
  // runs a cleanup after each test case (e.g. clearing jsdom)
  cleanup();
});

afterAll(() => {
  vi.unstubAllGlobals();
});
