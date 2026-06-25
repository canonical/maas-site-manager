import { Suspense, useEffect } from "react";

import { ContentSection } from "@canonical/maas-react-components";
import { Col, Row, Spinner, useOnEscapePressed, usePrevious, AppAside } from "@canonical/react-components";

import { useAppLayoutContext } from "@/app/context";
import type { Sidebar } from "@/app/context/AppLayoutContext";
import { useLocation } from "@/utils/router";

export const sidebarLabels: Record<NonNullable<Sidebar>, string> = {
  addUser: "Add user",
  editUser: "Edit user",
  removeSites: "Remove sites",
  createToken: "Generate tokens",
  deleteUser: "Delete user",
  siteDetails: "Site details",
  editSite: "Edit site",
  siteSelect: "Selected Sites",
  uploadCustomImage: "Upload custom image",
  addToAvailableImages: "Add to available images",
  removeAvailableImages: "Remove available images",
  sitesMissingData: "Sites with missing data",
  deleteBootSource: "Delete image source",
  addBootSource: "Add image source",
  editBootSource: "Edit image source",
  editCustomImagesSource: "Edit custom images",
};

export const sidebarComponent: Record<NonNullable<Sidebar>, React.FC> = {
  addUser: lazy(() => import("@/app/settings/views/UserList/components/UserForm/UserAddForm")),
  editSite: lazy(() => import("@/app/sites/components/EditSite")),
  editUser: lazy(() => import("@/app/settings/views/UserList/components/UserForm/UserEditForm")),
  createToken: lazy(() => import("@/app/settings/views/TokensList/components/TokensCreate")),
  deleteUser: lazy(() => import("@/app/settings/views/UserList/components/DeleteUser")),
  removeSites: lazy(() => import("@/app/sites/components/RemoveSites")),
  siteDetails: lazy(() => import("@/app/sites/components/SiteDetails")),
  siteSelect: () => null,
  uploadCustomImage: lazy(() => import("@/app/images/components/UploadCustomImage")),
  addToAvailableImages: lazy(() => import("@/app/images/components/AddToAvailableImages")),
  removeAvailableImages: lazy(() => import("@/app/images/components/RemoveAvailableImages")),
  sitesMissingData: lazy(() => import("@/app/sites/components/SitesMissingData")),
  deleteBootSource: lazy(() => import("@/app/settings/views/Source/components/DeleteImageSource")),
  addBootSource: lazy(() => import("@/app/settings/views/Source/components/ImageSourceForm/AddImageSourceForm")),
  editBootSource: lazy(() => import("@/app/settings/views/Source/components/ImageSourceForm/EditImageSourceForm")),
  editCustomImagesSource: lazy(
    () => import("@/app/settings/views/Source/components/ImageSourceForm/EditCustomImagesSourceForm"),
  ),
} as const;

export const SidebarComponents = ({ sidebar }: { sidebar: NonNullable<Sidebar> }) => {
  const ComponentToRender = sidebarComponent[sidebar] || null;

  return <ComponentToRender />;
};

export const Aside = () => {
  const { pathname } = useLocation();
  const previousPathname = usePrevious(pathname);
  const { sidebar, setSidebar } = useAppLayoutContext();

  // close any open panels on route change
  useEffect(() => {
    if (pathname !== previousPathname) {
      setSidebar(null);
    }
  }, [pathname, previousPathname, setSidebar]);

  useOnEscapePressed(() => {
    setSidebar(null);
  });

  return (
    <AppAside
      aria-hidden={!sidebar}
      aria-label={sidebar ? sidebarLabels[sidebar] : undefined}
      className="is-maas-site-manager"
      collapsed={!sidebar}
      id="aside-panel"
    >
      <Row>
        <Col size={12}>
          <Suspense
            fallback={
              <ContentSection>
                <Spinner text="Loading..." />
              </ContentSection>
            }
          >
            {sidebar && <SidebarComponents sidebar={sidebar} />}
          </Suspense>
        </Col>
      </Row>
    </AppAside>
  );
};
