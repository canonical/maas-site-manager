import { publicPages } from "../../../src/app/base/routes";
import { checkPageA11y } from "../../support/a11y";

context("public routes accessibility", () => {
  publicPages.forEach((page) => {
    (["light", "dark"] as const).forEach((colorScheme) => {
      it(`${page.title} page does not have any automatically detectable accessibility issues in ${colorScheme} mode`, () => {
        checkPageA11y(colorScheme)(page);
      });
    });
  });
});
