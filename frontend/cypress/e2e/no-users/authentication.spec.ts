import { routesConfig } from "../../../src/app/base/routes";
import { scenarios } from "../../../src/mocks/scenarios";

const login = () => {
  cy.findByRole("textbox", { name: /email/i, timeout: 30000 }).type(Cypress.env("email"));
  cy.findByLabelText(/password/i).type(Cypress.env("password"));
  cy.findByRole("button", { name: /login/i }).click();
};

context("Authentication", () => {
  it("redirects unauthenticated user to login page when attempting to visit sites list", () => {
    const protectedRoute = routesConfig.sitesList.path;

    cy.visit(protectedRoute);
    cy.url().should("include", `${routesConfig.login.path}?redirectTo=${encodeURIComponent(protectedRoute)}`);
  });

  it("redirects user to enrolled sites list after login", () => {
    cy.visit(routesConfig.login.path);
    login();

    cy.url().should("include", routesConfig.sitesList.path);
  });

  it("redirects user to the URL they wanted to visit", () => {
    cy.visit(routesConfig.requests.path);
    login();

    cy.url().should("include", routesConfig.requests.path);
  });

  it("maintains authentication state after page reload", () => {
    cy.visit(routesConfig.sitesList.path);
    login();
    cy.url().should("include", routesConfig.sitesList.path);

    cy.reload();
    cy.url().should("include", routesConfig.sitesList.path);
  });

  it("redirects to login page when API returns 401", () => {
    cy.visit(routesConfig.login.path);
    login();

    const protectedRoute = routesConfig.sitesList.path;
    cy.visit(`${protectedRoute}?scenario=${scenarios.sitesUnauthorized}`);
    cy.url().should("include", `${routesConfig.login.path}?redirectTo=${encodeURIComponent(protectedRoute)}`);
  });
});
