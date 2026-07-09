import { type ReactElement, Suspense, useEffect } from "react";

import { ContentSection, Placeholder } from "@canonical/maas-react-components";
import { Col, Row, useOnEscapePressed, usePrevious, AppAside } from "@canonical/react-components";

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
  addUser: lazy(() => import("@/app/settings/views/Users/components/UserForm/UserAddForm")),
  editSite: lazy(() => import("@/app/sites/components/EditSite")),
  editUser: lazy(() => import("@/app/settings/views/Users/components/UserForm/UserEditForm")),
  createToken: lazy(() => import("@/app/settings/views/Tokens/components/TokensCreate")),
  deleteUser: lazy(() => import("@/app/settings/views/Users/components/DeleteUser")),
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

const Aside = () => {
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
          <Suspense fallback={<AsideSkeleton />}>{sidebar && <SidebarComponents sidebar={sidebar} />}</Suspense>
        </Col>
      </Row>
    </AppAside>
  );
};

const AsideSkeleton = (): ReactElement => {
  return (
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
  );
};

Aside.Skeleton = AsideSkeleton;

export default Aside;
