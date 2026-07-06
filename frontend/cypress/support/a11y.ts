// NOTE: keep in sync with the "darkMode" localStorage key used by useDarkMode.ts
const DARK_MODE_STORAGE_KEY = "darkMode";

export const checkPageA11y =
  (colorScheme: "light" | "dark") =>
  ({ title, path }: { title: string; path: string }) => {
    cy.visit(path, {
      onBeforeLoad(win) {
        win.localStorage.setItem(DARK_MODE_STORAGE_KEY, JSON.stringify(colorScheme === "dark"));
      },
    });

    // verify the correct page has been displayed
    cy.title().should("match", new RegExp(title));

    cy.injectAxe();

    cy.checkA11y(
      // @canonical/react-components Accordion is known to have accessibility issues
      { exclude: [".p-accordion"] },
      // TODO: https://warthogs.atlassian.net/browse/MAASENG-2043
      { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] } },
    );
  };
