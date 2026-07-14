// TODO: Upstream the lazy loader and side panel to maas-react-components
import type { ComponentType } from "react";
import { lazy, Suspense } from "react";

import { ContentSection, Placeholder } from "@canonical/maas-react-components";

/**
 * Props shared by side panels that can be opened on top of another panel (e.g.
 * the edit/remove site panels opened from the site details panel). When an
 * `onClose` callback is provided, the panel calls it instead of closing the
 * side panel outright, allowing the caller to restore the previous panel.
 *
 * The intersection with `Record<string, unknown>` keeps the type compatible
 * with `openSidePanel`'s `TProps extends Record<string, unknown>` constraint.
 */
export type ReturnablePanelProps = Record<string, unknown> & {
  onClose?: () => void;
};

/**
 * Lazily loads a side panel component wrapped in its own Suspense boundary.
 * Define the panel at module scope in the file that opens it and pass it
 * straight to `openSidePanel`:
 *
 * @example
 * const AddUser = lazySidePanel(() => import("./UserAddForm"));
 * // ...
 * openSidePanel({ component: AddUser, title: "Add user" });
 *
 * The `<SidePanel />` component from `@canonical/maas-react-components` renders
 * the panel component directly, so a bare `React.lazy` panel would suspend the
 * whole `<SidePanel />` on first open. That remounts `<SidePanel />`, and on
 * remount its internal "close on navigation" effect runs and immediately closes
 * the panel that was just opened. Giving each panel its own Suspense boundary
 * keeps `<SidePanel />` mounted (and open) while the chunk loads, and shows the
 * spinner inside the panel.
 */
export const lazySidePanel = (loader: () => Promise<{ default: ComponentType }>): ComponentType => {
  const LazyPanel = lazy(loader);
  const SidePanelContent = (props: Record<string, unknown>) => (
    <Suspense
      fallback={
        <ContentSection aria-hidden="true" className="aside-skeleton">
          {/* Side panel title skeleton */}
          <ContentSection.Title>
            <Placeholder height="2rem" variant="block" width="16ch" />
          </ContentSection.Title>
          {/* Side panel form skeleton */}
          <ContentSection.Content className="aside-skeleton__form">
            <div className="layout-skeleton__form-description">
              <Placeholder height="1.5rem" variant="block" width="100%" />
              <Placeholder height="1.5rem" variant="block" width="70%" />
            </div>
            {Array.from({ length: 2 }).map((_, index) => (
              <div className="layout-skeleton__form-field" key={`aside-skeleton-field-${index}`}>
                <Placeholder height="1.5rem" variant="block" width="14ch" />
                <Placeholder height="2.5rem" variant="block" width="100%" />
              </div>
            ))}
          </ContentSection.Content>
          {/* Side panel footer skeleton */}
          <ContentSection.Footer className="aside-skeleton__footer">
            <Placeholder height="2rem" variant="block" width="8ch" />
            <Placeholder height="2rem" variant="block" width="10ch" />
          </ContentSection.Footer>
        </ContentSection>
      }
    >
      <LazyPanel {...props} />
    </Suspense>
  );
  return SidePanelContent;
};
