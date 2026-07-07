import { lazy as lazyComponent, Suspense } from "react";
import type { ComponentType } from "react";

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

type SidePanelDefinition = {
  component: ComponentType;
  title: string;
};

/**
 * Lazily loads a panel component wrapped in its own Suspense boundary.
 *
 * The `<SidePanel />` component from `@canonical/maas-react-components` renders
 * the panel component directly. If a panel were a bare `React.lazy` component,
 * opening it for the first time (before its chunk is cached) would suspend the
 * whole `<SidePanel />`, swapping in the outer Suspense fallback and
 * unmounting/remounting `<SidePanel />`. On remount its internal "close on
 * navigation" effect runs and immediately closes the panel that was just
 * opened. Containing each panel's suspension here keeps `<SidePanel />` mounted
 * (and open) while the chunk loads, and shows the spinner inside the panel.
 */
const lazy = (loader: () => Promise<{ default: ComponentType }>): ComponentType => {
  const LazyPanel = lazyComponent(loader);
  const PanelWithSuspense = (props: Record<string, unknown>) => (
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
  return PanelWithSuspense;
};

/**
 * Central registry of the application's side panels. Each entry maps to a
 * lazily-loaded panel component and the title used for the panel's heading and
 * accessible name. Pass an entry to `openSidePanel` from the
 * `@canonical/maas-react-components` `useSidePanel` hook to open it.
 */
export const sidePanels = {
  addUser: {
    component: lazy(() => import("@/app/settings/views/Users/components/UserForm/UserAddForm")),
    title: "Add user",
  },
  editUser: {
    component: lazy(() => import("@/app/settings/views/Users/components/UserForm/UserEditForm")),
    title: "Edit user",
  },
  deleteUser: {
    component: lazy(() => import("@/app/settings/views/Users/components/DeleteUser")),
    title: "Delete user",
  },
  createToken: {
    component: lazy(() => import("@/app/settings/views/TokensList/components/TokensCreate")),
    title: "Generate tokens",
  },
  siteDetails: {
    component: lazy(() => import("@/app/sites/components/SiteDetails")),
    title: "Site details",
  },
  editSite: {
    component: lazy(() => import("@/app/sites/components/EditSite")),
    title: "Edit site",
  },
  removeSites: {
    component: lazy(() => import("@/app/sites/components/RemoveSites")),
    title: "Remove sites",
  },
  sitesMissingData: {
    component: lazy(() => import("@/app/sites/components/SitesMissingData")),
    title: "Sites with missing data",
  },
  uploadCustomImage: {
    component: lazy(() => import("@/app/images/components/UploadCustomImage")),
    title: "Upload custom image",
  },
  addToAvailableImages: {
    component: lazy(() => import("@/app/images/components/AddToAvailableImages")),
    title: "Add to available images",
  },
  removeAvailableImages: {
    component: lazy(() => import("@/app/images/components/RemoveAvailableImages")),
    title: "Remove available images",
  },
  addBootSource: {
    component: lazy(() => import("@/app/settings/views/Source/components/ImageSourceForm/AddImageSourceForm")),
    title: "Add image source",
  },
  editBootSource: {
    component: lazy(() => import("@/app/settings/views/Source/components/ImageSourceForm/EditImageSourceForm")),
    title: "Edit image source",
  },
  editCustomImagesSource: {
    component: lazy(() => import("@/app/settings/views/Source/components/ImageSourceForm/EditCustomImagesSourceForm")),
    title: "Edit custom images",
  },
  deleteBootSource: {
    component: lazy(() => import("@/app/settings/views/Source/components/DeleteImageSource")),
    title: "Delete image source",
  },
} satisfies Record<string, SidePanelDefinition>;

export type SidePanelKey = keyof typeof sidePanels;
