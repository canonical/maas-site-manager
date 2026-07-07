import type { ComponentType } from "react";
import { lazy, Suspense } from "react";

import { ContentSection } from "@canonical/maas-react-components";
import { Spinner } from "@canonical/react-components";

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
        <ContentSection>
          <Spinner text="Loading..." />
        </ContentSection>
      }
    >
      <LazyPanel {...props} />
    </Suspense>
  );
  return SidePanelContent;
};
