import { LONG_TIMEOUT } from "../../constants";

context("Requests", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/settings/requests");
    cy.findByRole("treegrid").should("exist");
    cy.get("tbody .p-generic-table__skeleton-row", { timeout: LONG_TIMEOUT }).should("have.length", 0);
  });

  it("goes to the sites page if the user clicks on the sites link", () => {
    cy.findByRole("heading", { name: /enrollment requests/i }).should("exist");
    cy.findByText("Showing 0 out of 0 open enrollment requests").should("not.exist");
    cy.findByRole("checkbox", { name: "select all" }).click({ force: true });
    cy.findByRole("button", { name: /Accept/i }).click();
    cy.findByRole("alert", { timeout: LONG_TIMEOUT })
      .invoke("text")
      .should("match", /Accepted enrollment request for [0-9]+ MAAS sites/i);
    cy.findByRole("button", { name: /Go to Sites/i }).click();
    cy.url().should("include", "/sites/list");
  });
});
