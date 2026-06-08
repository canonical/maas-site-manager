import { LONG_TIMEOUT } from "../../constants";

context("Sites", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/sites/list");
  });

  it("can hide table columns", () => {
    cy.get("th", { timeout: LONG_TIMEOUT }).should("have.length", 8);
    cy.findByRole("button", { name: "Columns" }).click();
    cy.get('[aria-label="columns menu"]')
      .findByRole("checkbox", { name: /connection/i })
      .click({ force: true });
    cy.get("th").should("have.length", 7);
    cy.get("th")
      .contains(/connection/i)
      .should("not.exist");
    cy.reload();
    cy.get("th", { timeout: LONG_TIMEOUT }).should("have.length", 7);
    cy.get("th")
      .contains(/connection/i)
      .should("not.exist");
  });

  it("opens remove sites panel if remove button is pressed", () => {
    cy.get("tbody .p-checkbox__input", { timeout: LONG_TIMEOUT }).should("have.length.greaterThan", 0);
    cy.findByRole("complementary", { name: /Remove sites/i }).should("not.exist");
    cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
    cy.findByRole("button", { name: /Remove/i }).click();
    cy.findByRole("complementary", { name: /Remove sites/i }).should("be.visible");
  });

  it("can close remove site panel using Escape key", () => {
    cy.get("tbody .p-checkbox__input", { timeout: LONG_TIMEOUT }).should("have.length.greaterThan", 0);
    cy.findByRole("complementary", { name: /Remove sites/i }).should("not.exist");
    cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
    cy.findByRole("button", { name: /Remove/i }).click();
    cy.findByRole("complementary", { name: /Remove sites/i }).should("be.visible");
    cy.press(Cypress.Keyboard.Keys.ESC);
    cy.findByRole("complementary", { name: /Remove sites/i }).should("not.exist");
  });

  it("hides columns dropdown in the map view", () => {
    cy.findByRole("searchbox", { name: /Search and filter/i, timeout: LONG_TIMEOUT }).should("be.visible");
    cy.findByRole("button", { name: /Columns/i }).should("be.visible");
    cy.findByRole("heading", { level: 1, name: /MAAS sites/i }).should("be.visible");
    cy.visit("/sites/map");
    cy.findByRole("heading", { level: 1, name: /MAAS sites/i }).should("be.visible");
    cy.findByRole("button", { name: /Columns/i }).should("not.exist");
  });

  it("search text persists when switching pages", () => {
    const searchText = "test";
    cy.findByRole("searchbox", { name: /Search and filter/i, timeout: LONG_TIMEOUT }).type(searchText);
    cy.url().should("include", `/sites/list?q=${searchText}`);
    cy.findByRole("tab", { name: /map/i }).click();
    cy.url().should("include", `/sites/map?q=${searchText}`);
    cy.findByRole("tab", { name: /table/i }).should("have.attr", "href", `/sites/list?q=${searchText}`);
    cy.findByRole("tab", { name: /table/i }).click();
    cy.findByRole("searchbox", { name: /Search and filter/i, timeout: LONG_TIMEOUT }).should("have.value", searchText);
  });
});
