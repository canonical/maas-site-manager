/* eslint-disable no-restricted-imports */
import type { ReactElement } from "react";
import * as React from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { RenderOptions, RenderResult } from "@testing-library/react";
import { screen, render, waitForElementToBeRemoved } from "@testing-library/react";

import Layout from "@/app/base/components/Layout";
import { AppLayoutContextProvider, AuthContextProvider, RowSelectionContextProviders } from "@/app/context";
import type { MemoryRouterProps } from "@/utils/router";
import { MemoryRouter } from "@/utils/router";

export const Providers = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        // in tests any unsuccessful query should fail immediately without retrying
        retry: false,
      },
    },
  });

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};

const makeProvidersWithMemoryRouter =
  ({ withMainLayout, ...memoryRouterProps }: MemoryRenderOptions) =>
  ({ children }: { children: React.ReactNode }) => {
    return (
      <Providers>
        <MemoryRouter {...memoryRouterProps}>
          <AppLayoutContextProvider>
            <AuthContextProvider>
              <RowSelectionContextProviders>
                {withMainLayout ? <Layout /> : null}
                {children}
              </RowSelectionContextProviders>
            </AuthContextProvider>
          </AppLayoutContextProvider>
        </MemoryRouter>
      </Providers>
    );
  };

const customRender: (ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) => RenderResult = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: Providers, ...options });

interface MemoryRenderOptions extends MemoryRouterProps, Omit<RenderOptions, "wrapper"> {
  withMainLayout?: boolean;
}
export const renderWithMemoryRouter = (ui: ReactElement, options?: MemoryRenderOptions) => {
  const { basename, initialEntries, initialIndex, withMainLayout } = options || {};
  const Providers = makeProvidersWithMemoryRouter({ basename, initialEntries, initialIndex, withMainLayout });
  return render(ui, { wrapper: Providers, ...options });
};

export const getByTextContent = (text: RegExp | string) => {
  return screen.getByText((_, element) => {
    const hasText = (element: Element | null) => {
      if (element) {
        if (text instanceof RegExp && element.textContent) {
          return text.test(element.textContent);
        } else {
          return element.textContent === text;
        }
      } else {
        return false;
      }
    };
    const elementHasText = hasText(element);
    const childrenDontHaveText = Array.from(element?.children || []).every((child) => !hasText(child));
    return elementHasText && childrenDontHaveText;
  });
};

export const waitForLoadingToFinish = () => waitForElementToBeRemoved(screen.queryByText(/loading/i));

export { screen, within, waitFor, act, renderHook, fireEvent } from "@testing-library/react";

export type { RenderResult } from "@testing-library/react";

export { customRender as render };
export { default as userEvent } from "@testing-library/user-event";
export { setupServer } from "msw/node";
