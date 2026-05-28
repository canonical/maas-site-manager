import { LONG_TIMEOUT } from "../../constants";

context("Map", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/sites/map");
    cy.findByRole("region", { name: /sites map/i, timeout: LONG_TIMEOUT }).should("be.visible");
    cy.findAllByRole("button", { name: /site location marker/i, timeout: LONG_TIMEOUT }).should(
      "have.length.greaterThan",
      0,
    );
  });

  it("displays site markers", () => {
    cy.findByRole("complementary", { name: /Site details/i }).should("not.exist");
    cy.findAllByRole("button", { name: /site location marker/i })
      .first()
      .click();
    cy.findByRole("complementary", { name: /Site details/i }).should("be.visible");
  });

  it("returns to previous side panel if it exists", () => {
    cy.findAllByRole("button", { name: /site location marker/i })
      .first()
      .click();
    cy.findByRole("complementary", { name: /Site details/i })
      .findByRole("button", { name: "Edit" })
      .click();
    cy.findByRole("complementary", { name: /Edit site/i }).should("be.visible");
    cy.findByRole("button", { name: /Cancel/i }).click();
    cy.findByRole("complementary", { name: /Site details/i }).should("be.visible");
  });
});
