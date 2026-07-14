/* eslint-disable no-restricted-imports */
import type { ReactElement } from "react";
import * as React from "react";

import { SidePanelContextProvider } from "@canonical/maas-react-components";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { RenderOptions, RenderResult } from "@testing-library/react";
import { render, screen, waitForElementToBeRemoved } from "@testing-library/react";

import Layout from "@/app/base/components/Layout";
import { AuthContextProvider, RowSelectionContextProviders } from "@/app/context";
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

  return (
    <QueryClientProvider client={queryClient}>
      <SidePanelContextProvider>{children}</SidePanelContextProvider>
    </QueryClientProvider>
  );
};

const makeProvidersWithMemoryRouter =
  ({ withMainLayout, ...memoryRouterProps }: MemoryRenderOptions) =>
  ({ children }: { children: React.ReactNode }) => {
    return (
      <Providers>
        <MemoryRouter {...memoryRouterProps}>
          <AuthContextProvider>
            <RowSelectionContextProviders>
              {withMainLayout ? <Layout /> : null}
              {children}
            </RowSelectionContextProviders>
          </AuthContextProvider>
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

/**
 * Mocks the generic side panel context
 * @returns A mock functions for opening and closing the side panel
 */
export const mockSidePanel = async () => {
  const mockUseSidePanel = vi.spyOn(await import("@canonical/maas-react-components"), "useSidePanel");

  const mockOpen = vi.fn();
  const mockClose = vi.fn();

  let isOpen = false;

  beforeEach(() => {
    vi.clearAllMocks();
    isOpen = false;

    mockOpen.mockImplementation(() => {
      isOpen = true;
      mockUseSidePanel.mockReturnValue({
        isOpen: true,
        title: "",
        size: "regular",
        component: null,
        props: {},
        openSidePanel: mockOpen,
        closeSidePanel: mockClose,
        setSidePanelSize: vi.fn(),
      });
    });

    mockClose.mockImplementation(() => {
      isOpen = false;
      mockUseSidePanel.mockReturnValue({
        isOpen: false,
        title: "",
        size: "regular",
        component: null,
        props: {},
        openSidePanel: mockOpen,
        closeSidePanel: mockClose,
        setSidePanelSize: vi.fn(),
      });
    });

    mockUseSidePanel.mockReturnValue({
      isOpen,
      title: "",
      size: "regular",
      component: null,
      props: {},
      openSidePanel: mockOpen,
      closeSidePanel: mockClose,
      setSidePanelSize: vi.fn(),
    });
  });

  return { mockOpen, mockClose };
};

export const waitForLoadingToFinish = () => waitForElementToBeRemoved(screen.queryByText(/loading/i));

export { act, fireEvent, renderHook, screen, waitFor, within } from "@testing-library/react";

export type { RenderResult } from "@testing-library/react";

export { default as userEvent } from "@testing-library/user-event";
export { setupServer } from "msw/node";
export { customRender as render };
