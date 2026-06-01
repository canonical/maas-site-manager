import { LONG_TIMEOUT } from "../../constants";

context("Users", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/settings/users");
  });

  it("can open and close the 'Add user' form", () => {
    cy.findByRole("button", { name: "Add user" }).click();
    cy.findByRole("form", { name: /Add user/i }).should("be.visible");
    cy.findByRole("button", { name: "Cancel" }).click();
    cy.findByRole("form", { name: /Add user/i }).should("not.exist");
  });

  it("can open and close the 'Edit user' form", () => {
    cy.findAllByRole("row", { timeout: LONG_TIMEOUT })
      .eq(2)
      .then(($row) => {
        const username = $row.find("td").eq(0).text();
        cy.findByRole("button", { name: `Edit ${username}` }).click();
        cy.findByRole("form", { name: `Edit ${username}` }).should("be.visible");
        cy.findByRole("button", { name: "Cancel" }).click();
        cy.findByRole("form", { name: `Edit ${username}` }).should("not.exist");
      });
  });

  it("can open and close the 'Delete user' form", () => {
    cy.findAllByRole("row", { timeout: LONG_TIMEOUT })
      .eq(2)
      .then(($row) => {
        const username = $row.find("td").eq(0).text();
        cy.findByRole("button", { name: `Delete ${username}` }).click();
        cy.findByRole("form", { name: `Delete ${username}` }).should("be.visible");
        cy.findByRole("button", { name: "Cancel" }).click();
        cy.findByRole("form", { name: `Delete ${username}` }).should("not.exist");
      });
  });

  it("can close forms using the escape key", () => {
    cy.findByRole("button", { name: "Add user" }).click();
    cy.findByRole("form", { name: /Add user/i }).should("be.visible");
    cy.press(Cypress.Keyboard.Keys.ESC);
    cy.findByRole("form", { name: /Add user/i }).should("not.exist");
  });

  it("closes the form after editing a user", () => {
    cy.findAllByRole("row", { timeout: LONG_TIMEOUT })
      .eq(2)
      .then(($row) => {
        const username = $row.find("td").eq(0).text();
        cy.findByRole("button", { name: `Edit ${username}` }).click();
        cy.findByRole("form", { name: `Edit ${username}` }).should("be.visible");
        cy.findByRole("textbox", { name: /Username/i }).type("12345");
        cy.findByRole("button", { name: "Save" }).click();
        cy.findByRole("form", { name: `Edit ${username}` }).should("not.exist");
      });
  });

  it("closes the form when navigating away", () => {
    cy.findByRole("button", { name: /Add user/i }).click();
    cy.findByRole("form", { name: /Add user/i }).should("be.visible");
    cy.findByRole("banner", { name: "main navigation" })
      .trigger("mouseover")
      .findByRole("link", { name: /Sites/ })
      .click({ force: true });
    cy.go("back");
    cy.get('form[aria-label="Add user"]').should("not.exist");
  });

  it("can delete a user", () => {
    const testUsername = "Watto89";
    cy.findByRole("button", { name: new RegExp(`Delete ${testUsername}`, "i"), timeout: LONG_TIMEOUT }).click();
    cy.findByPlaceholderText(testUsername).should("exist");
    cy.findByPlaceholderText(testUsername)
      .closest("form")
      .findByRole("button", { name: /delete/i })
      .should("have.attr", "aria-disabled", "true");
    cy.findByPlaceholderText(testUsername).type(testUsername);
    cy.findByPlaceholderText(testUsername)
      .closest("form")
      .findByRole("button", { name: /delete/i })
      .should("not.have.attr", "aria-disabled", "true")
      .click();
    cy.findByPlaceholderText(testUsername).should("not.exist");
  });
});
