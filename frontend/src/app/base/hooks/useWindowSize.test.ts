import useWindowSize from "./useWindowSize";

import { renderHook, act, waitFor } from "@/utils/test-utils";

vi.mock("global/window", () => ({
  innerWidth: 1024,
  innerHeight: 768,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
}));

afterAll(() => {
  vi.resetModules();
});

it("returns the expected initial width and height values", () => {
  const {
    result: { current },
  } = renderHook(() => useWindowSize());
  expect(current.screenHeight).toEqual(window.innerHeight);
  expect(current.screenWidth).toEqual(window.innerWidth);
});

it("updates the width and height when the window is resized", async () => {
  const { result, rerender } = renderHook(() => useWindowSize());
  const newWidth = 1000;
  const newHeight = 500;
  window.innerWidth = newWidth;
  window.innerHeight = newHeight;
  await waitFor(() => {
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
  });
  rerender();

  const { screenWidth, screenHeight } = result.current;
  expect(screenWidth).toEqual(newWidth);
  expect(screenHeight).toEqual(newHeight);
});

it("cleans up the event listener on unmount", () => {
  const addEventListenerSpy = vi.spyOn(window, "addEventListener");
  const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

  const { unmount } = renderHook(() => useWindowSize());
  unmount();

  expect(addEventListenerSpy).toHaveBeenCalledWith("resize", expect.any(Function));
  expect(removeEventListenerSpy).toHaveBeenCalledWith("resize", expect.any(Function));
});
