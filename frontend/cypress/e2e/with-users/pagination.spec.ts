import { LONG_TIMEOUT } from "../../constants";

const pagesWithPagination = [
  { title: "Tokens", path: "/settings/tokens" },
  { title: "Requests", path: "/settings/requests" },
];

pagesWithPagination.forEach(({ title, path }) => {
  context("navigates to the correct page on user input", () => {
    beforeEach(() => {
      cy.login();
      cy.visit(path);
    });

    it(`${title} page`, () => {
      cy.findByRole("spinbutton", { name: /page number/i, timeout: LONG_TIMEOUT }).should("have.value", "1");
      cy.findByRole("button", { name: /next page/i })
        .should("not.have.attr", "aria-disabled", "true")
        .click();
      cy.findByRole("spinbutton", { name: /page number/i }).should("have.value", "2");
      cy.findByRole("button", { name: /next page/i })
        .should("not.have.attr", "aria-disabled", "true")
        .click();
      cy.findByRole("spinbutton", { name: /page number/i }).should("have.value", "3");
      cy.findByRole("button", { name: /previous page/i })
        .should("not.have.attr", "aria-disabled", "true")
        .click();
      cy.findByRole("spinbutton", { name: /page number/i }).should("have.value", "2");
      cy.findByRole("spinbutton", { name: /page number/i }).type("{selectall}1");
      cy.findByRole("spinbutton", { name: /page number/i }).should("have.value", "1");
    });
  });
});
