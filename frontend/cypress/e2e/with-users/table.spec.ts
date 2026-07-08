import { LONG_TIMEOUT } from "../../constants";

const pagesWithTable = [
  { title: "Tokens", path: "/settings/tokens" },
  { title: "Requests", path: "/settings/requests" },
  { title: "Sites", path: "/sites/list" },
];

pagesWithTable.forEach(({ title, path }) => {
  context(title, () => {
    beforeEach(() => {
      cy.login();
      cy.visit(path);
      cy.findByRole("treegrid").should("exist");
      cy.get("tbody .p-generic-table__skeleton-row", { timeout: LONG_TIMEOUT }).should("have.length", 0);
    });

    it("clicking unchecked 'select all' checkbox selects all items on the current page", () => {
      cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
      cy.get("tbody .p-checkbox__input:not(:checked)").should("not.exist");
      cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
      cy.get("tbody .p-checkbox__input:checked").should("not.exist");
    });

    it("clicking partially checked 'select all' checkbox selects all items on the current page", () => {
      cy.get("tbody .p-checkbox__input").first().click({ force: true });
      cy.findByRole("checkbox", { name: /select all/i }).should("have.prop", "indeterminate", true);
      cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
      cy.findByRole("checkbox", { name: /select all/i }).should("be.checked");
      cy.findByRole("checkbox", { name: /select all/i }).should("not.have.prop", "indeterminate", true);
      cy.get("tbody .p-checkbox__input:not(:checked)").should("not.exist");
    });

    it("clicking checked 'select all' checkbox deselects items", () => {
      cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
      cy.findByRole("checkbox", { name: /select all/i }).should("be.checked");
      cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
      cy.get("tbody .p-checkbox__input:checked").should("not.exist");
    });

    it("changing page deselects all items", () => {
      cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
      cy.findByRole("checkbox", { name: /select all/i }).should("be.checked");
      cy.get("tbody .p-checkbox__input:not(:checked)").should("not.exist");
      cy.findByRole("button", { name: /next page/i })
        .should("not.have.attr", "aria-disabled", "true")
        .click();
      cy.findByRole("checkbox", { name: /select all/i }).should("not.be.checked");
      cy.get("tbody .p-checkbox__input:checked").should("not.exist");
      cy.findByRole("button", { name: /previous page/i })
        .should("not.have.attr", "aria-disabled", "true")
        .click();
      cy.findByRole("checkbox", { name: /select all/i }).should("not.be.checked");
      cy.get("tbody .p-checkbox__input:checked").should("not.exist");
    });

    it("changing page size deselects all items", () => {
      cy.findByRole("checkbox", { name: /select all/i }).click({ force: true });
      cy.findByRole("checkbox", { name: /select all/i }).should("be.checked");
      cy.get("tbody .p-checkbox__input:not(:checked)").should("not.exist");
      cy.findByRole("combobox", { name: /items per page/i }).select("30/page");
      cy.findByRole("checkbox", { name: /select all/i }).should("not.be.checked");
      cy.get("tbody .p-checkbox__input:checked").should("not.exist");
    });
  });
});
