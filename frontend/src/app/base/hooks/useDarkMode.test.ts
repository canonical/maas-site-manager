import useDarkMode, { DARK_MODE_STORAGE_KEY } from "./useDarkMode";

import { act, renderHook } from "@/utils/test-utils";

afterEach(() => {
  localStorage.clear();
  document.body.classList.remove("is-dark");
});

it("defaults to the system colour scheme when no preference is stored", () => {
  // matchMedia is stubbed in the test setup to report no dark preference.
  const { result } = renderHook(() => useDarkMode());

  expect(result.current[0]).toBe(false);
  expect(document.body).not.toHaveClass("is-dark");
});

it("uses the preference stored in localStorage", () => {
  localStorage.setItem(DARK_MODE_STORAGE_KEY, "true");

  const { result } = renderHook(() => useDarkMode());

  expect(result.current[0]).toBe(true);
  expect(document.body).toHaveClass("is-dark");
});

it("toggles dark mode and persists the preference", () => {
  const { result } = renderHook(() => useDarkMode());

  expect(result.current[0]).toBe(false);

  act(() => {
    result.current[1]();
  });

  expect(result.current[0]).toBe(true);
  expect(document.body).toHaveClass("is-dark");
  expect(localStorage.getItem(DARK_MODE_STORAGE_KEY)).toBe("true");

  act(() => {
    result.current[1]();
  });

  expect(result.current[0]).toBe(false);
  expect(document.body).not.toHaveClass("is-dark");
  expect(localStorage.getItem(DARK_MODE_STORAGE_KEY)).toBe("false");
});
