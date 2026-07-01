import { useEffect } from "react";

import useLocalStorageState from "use-local-storage-state";

/**
 * The localStorage key used to persist the user's dark mode preference.
 *
 * NOTE: this value is duplicated in the inline theme bootstrap script in
 * `index.html` (used to apply the theme before React hydrates and avoid a flash
 * of the wrong theme). Keep the two in sync.
 */
export const DARK_MODE_STORAGE_KEY = "darkMode";

/** The class Vanilla Framework uses to activate its dark theme. */
const DARK_MODE_CLASS = "is-dark";

/**
 * Whether the user's operating system requests a dark colour scheme.
 */
const prefersDarkMode = (): boolean =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-color-scheme: dark)").matches;

/**
 * Manage the application's dark mode theme.
 *
 * The preference is persisted to localStorage and defaults to the user's system
 * colour scheme when no preference has been stored. Toggling adds or removes the
 * Vanilla Framework `is-dark` class on the document body, which remaps the
 * `--vf-color-*` custom properties used throughout the app.
 *
 * @returns A tuple of the current dark mode state and a function to toggle it.
 */
const useDarkMode = (): [boolean, () => void] => {
  const [isDarkMode, setIsDarkMode] = useLocalStorageState<boolean>(DARK_MODE_STORAGE_KEY, {
    defaultValue: prefersDarkMode,
  });

  useEffect(() => {
    document.body.classList.toggle(DARK_MODE_CLASS, isDarkMode);
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode((previousIsDarkMode) => !previousIsDarkMode);
  };

  return [isDarkMode, toggleDarkMode];
};

export default useDarkMode;
