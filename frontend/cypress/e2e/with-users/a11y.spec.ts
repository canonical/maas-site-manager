import { protectedPages } from "../../../src/app/base/routes";
import { checkPageA11y } from "../../support/a11y";

context("protected routes accessibility", () => {
  beforeEach(() => {
    cy.login();
  });

  protectedPages.forEach((page) => {
    (["light", "dark"] as const).forEach((colorScheme) => {
      it(`${page.title} page does not have any automatically detectable accessibility issues in ${colorScheme} mode`, () => {
        checkPageA11y(colorScheme)(page);
      });
    });
  });
});
