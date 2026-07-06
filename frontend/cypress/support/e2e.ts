/// <reference types="cypress" />

import "@testing-library/cypress";
import "cypress-axe";
import "./commands";

declare global {
  namespace Cypress {
    interface Chainable {
      login(options?: { email?: string; password?: string }): void;
    }
  }
}
