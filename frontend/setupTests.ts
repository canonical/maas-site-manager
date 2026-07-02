import "@/testing/customMatchers";
import { fetch, Request, Response } from "@remix-run/web-fetch";
import * as matchers from "@testing-library/jest-dom/matchers";
import { cleanup } from "@testing-library/react";
import { AbortController as NodeAbortController, AbortSignal as NodeAbortSignal } from "abort-controller";
import { config } from "dotenv";
import { configMocks, mockResizeObserver } from "jsdom-testing-mocks";
import { TextDecoder as NodeTextDecoder, TextEncoder as NodeTextEncoder } from "util";
import { afterEach, expect } from "vitest";
import "vitest-canvas-mock";
import "vitest-webgl-canvas-mock";
//import "@testing-library/jest-dom";

config();
configMocks({ beforeEach, afterEach, afterAll });

// extends Vitest's expect method with methods from react-testing-library
expect.extend(matchers);

// use the Web Fetch API in tests which is used by Remix
// @ts-expect-error because Web Fetch API types differ from jsdom implementation
// https://github.com/remix-run/react-router/blob/b154367/packages/router/__tests__/setup.ts

if (globalThis.fetch !== fetch) {
  // @ts-expect-error built-in lib.dom.d.ts expects `fetch(Request | string, ...)` but the web
  // fetch API allows a URL so @remix-run/web-fetch defines
  // `fetch(string | URL | Request, ...)`
  globalThis.fetch = fetch;
  // @ts-expect-error same as above, lib.dom.d.ts doesn't allow a URL to the Request constructor
  globalThis.Request = Request;
  // @ts-expect-error web-std/fetch Response does not currently implement Response.error()
  globalThis.Response = Response;
}

if (!globalThis.AbortController) {
  // @ts-expect-error because NodeAbortController is not a global in jsdom
  globalThis.AbortController = NodeAbortController;
}

if (!globalThis.AbortSignal) {
  // @ts-expect-error because NodeAbortSignal is not a global in jsdom
  globalThis.AbortSignal = NodeAbortSignal;
}

if (!globalThis.TextEncoder || !globalThis.TextDecoder) {
  globalThis.TextEncoder = NodeTextEncoder;
  globalThis.TextDecoder = NodeTextDecoder;
}

if (!globalThis.URL.createObjectURL) {
  window.URL.createObjectURL = vi.fn();
}

Object.defineProperty(window, "scrollTo", { value: vi.fn(), writable: true });

// jsdom does not implement the Web Animations API, which is used by some
// @canonical/react-components components (e.g. toast notifications).
if (!Element.prototype.animate) {
  Element.prototype.animate = vi.fn(() => ({
    cancel: vi.fn(),
    finish: vi.fn(),
    onfinish: null,
  })) as unknown as Element["animate"];
}

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
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query === "(prefers-reduced-motion)",
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
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
