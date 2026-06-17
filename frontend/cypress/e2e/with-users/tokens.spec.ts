import * as path from "path";
import { LONG_TIMEOUT } from "../../constants";

context("Tokens", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/settings/tokens");
  });

  it("can open and close token generate form", () => {
    cy.findByRole("button", { name: /Generate tokens/i, timeout: LONG_TIMEOUT }).click();
    cy.findByRole("form", { name: /Generate new enrollment tokens/i }).should("be.visible");
    cy.findByRole("button", { name: /Cancel/i }).click();
    cy.findByRole("form", { name: /Generate new enrollment tokens/i }).should("not.exist");
  });

  it("can close token generate dialog using Escape key", () => {
    cy.findByRole("button", { name: /Generate tokens/i }).click();
    cy.findByRole("complementary", { name: /generate tokens/i }).should("be.visible");
    cy.press(Cypress.Keyboard.Keys.ESC);
    cy.findByRole("complementary", { name: /generate tokens/i }).should("not.exist");
  });

  it("closes the token create form when navigating away", () => {
    cy.findByRole("button", { name: /Generate tokens/i }).click();
    cy.findByRole("form", { name: /Generate new enrollment tokens/i }).should("be.visible");

    cy.findByRole("banner", { name: "main navigation" })
      .trigger("mouseover")
      .findByRole("link", { name: /Sites/ })
      .click({ force: true });

    cy.go("back");
    cy.get('form[aria-label="Generate tokens"]').should("not.exist");
  });

  it("closes and clears the form after creating the token", () => {
    cy.intercept("POST", "**/tokens").as("createTokens");
    cy.findByRole("button", { name: /Generate tokens/i }).click();
    cy.findByRole("textbox", { name: /Amount of tokens to generate/i }).type("1");
    cy.findByRole("textbox", { name: /Expiration time/i }).type("1 week");
    cy.findByRole("form", { name: /Generate new enrollment tokens/i })
      .findByRole("button", { name: /Generate 1 token/i })
      .click();
    cy.get('form[aria-label="Generate tokens"]').should("not.exist");
    // check that the form has been reset
    cy.findByRole("button", { name: /Generate tokens/i }).click();
    cy.findByRole("form", { name: /Generate new enrollment tokens/i })
      .findByRole("button", { name: /Generate 0 tokens/i })
      .should(($btn) => {
        expect($btn).to.have.attr("aria-disabled", "true");
      });
  });

  it("saves tokens to a file on export", () => {
    const downloadsFolder = Cypress.config("downloadsFolder");
    cy.findByText("Showing 0 out of 0 tokens").should("not.exist");
    // The export hook fetches a token count first, then fires paged requests.
    // isLoadingExportTokens is false until the page queries start (aria-disabled absent),
    // true while they load (aria-disabled="true"), then false when data is ready.
    // Waiting for the full cycle ensures exportTokensData is non-null before clicking.
    cy.findByRole("button", { name: /Export/i }).should("have.attr", "aria-disabled", "true");
    cy.findByRole("button", { name: /Export/i }).should("not.have.attr", "aria-disabled");
    cy.findByRole("button", { name: /Export/i }).click();
    cy.readFile(path.join(downloadsFolder, "site-manager-tokens.csv")).should("match", /id,value,expired,created/);
  });
});
