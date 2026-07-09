import type { ReactElement } from "react";
import { Suspense } from "react";

import { ContentSection, GenericTable, Placeholder } from "@canonical/maas-react-components";
import { Application, AppMain } from "@canonical/react-components";
import classNames from "classnames";

import Aside from "@/app/base/components/Layout/components/Aside";
import DocumentTitle from "@/app/base/components/Layout/components/DocumentTitle/DocumentTitle";
import Navigation from "@/app/base/components/Navigation";
import SecondaryNavigation from "@/app/base/components/SecondaryNavigation";
import StatusBar from "@/app/base/components/StatusBar";
import type { RoutePath } from "@/app/base/routes";
import { routesConfig } from "@/app/base/routes";
import { useAuthContext } from "@/app/context";
import { matchPath, Outlet, useLocation } from "@/utils/router";

const getPageTitle = (pathname: RoutePath) => {
  const title = Object.values(routesConfig).find(({ path }) => path === pathname)?.title;
  return title ? `${title} | MAAS Site Manager` : "MAAS Site Manager";
};

const Layout = (): ReactElement => {
  const { pathname } = useLocation();
  const { status } = useAuthContext();
  const isLoggedIn = status === "authenticated";
  const isSideNavVisible = matchPath("/settings/*", pathname) || matchPath("/account/*", pathname);
  const isTableView = pathname.endsWith("/list") || (pathname.startsWith("/settings/") && pathname !== "/settings/map");

  const pageTitle = getPageTitle(pathname as RoutePath);

  return (
    <>
      <DocumentTitle>{pageTitle}</DocumentTitle>
      <Application>
        <Navigation isLoggedIn={isLoggedIn} />
        <AppMain className="is-maas-site-manager">
          <h1 className="u-visually-hidden">{pageTitle}</h1>
          <div className={classNames("l-main__nav", { "is-open": isSideNavVisible })}>
            <SecondaryNavigation isOpen={!!isSideNavVisible} />
          </div>
          <div className="l-main__content">
            <div className="row">
              <div className="col-12">
                <Suspense fallback={<LayoutSkeleton view={isTableView ? "table" : "settings"} />}>
                  <Outlet />
                </Suspense>
              </div>
            </div>
          </div>
        </AppMain>
        <Aside />
        <StatusBar />
      </Application>
    </>
  );
};

const LayoutSkeleton = ({ view }: { view: "settings" | "table" }): ReactElement => {
  if (view === "settings") {
    return (
      <ContentSection aria-hidden="true" className="layout-skeleton" variant="narrow">
        {/* Setting page title skeleton */}
        <ContentSection.Title>
          <Placeholder height="2rem" variant="block" width="16ch" />
        </ContentSection.Title>
        {/* Settings form field skeleton */}
        <div className="layout-skeleton__form">
          {Array.from({ length: 3 }).map((_, index) => (
            <div className="layout-skeleton__form-field" key={`layout-skeleton-field-${index}`}>
              <Placeholder height="1.5rem" variant="block" width="14ch" />
              <Placeholder height="2.5rem" variant="block" width="100%" />
            </div>
          ))}
        </div>
        {/* Footer skeleton */}
        <ContentSection.Footer>
          <Placeholder height="2rem" variant="block" width="8ch" />
        </ContentSection.Footer>
      </ContentSection>
    );
  }

  return (
    <ContentSection aria-hidden="true" className="layout-skeleton">
      <ContentSection.Header>
        {/* Page title, searchbar and toolbar buttons skeleton */}
        <div className="layout-skeleton__header">
          <Placeholder height="2rem" variant="block" width="24ch" />
          <Placeholder height="2rem" variant="block" width="100%" />
          <Placeholder height="2rem" variant="block" width="18ch" />
          <Placeholder height="2rem" variant="block" width="18ch" />
        </div>
      </ContentSection.Header>
      <ContentSection.Content>
        {/* Pagination skeleton */}
        <div className="layout-skeleton__pagination">
          <Placeholder height="2rem" variant="block" width="24ch" />
          <div className="layout-skeleton__pagination-controls">
            <Placeholder height="2rem" variant="block" width="16ch" />
            <Placeholder height="2rem" variant="block" width="16ch" />
          </div>
        </div>
        {/* Table skeleton */}
        <GenericTable
          className="layout-skeleton__table"
          columns={[
            {
              accessorKey: "name",
              header: () => <Placeholder variant="block" width="8ch" />,
              meta: {
                skeleton: () => (
                  <div>
                    <Placeholder variant="block" width="18ch" />
                    <Placeholder variant="block" width="24ch" />
                  </div>
                ),
              },
            },
            {
              accessorKey: "details",
              header: () => <Placeholder variant="block" width="12ch" />,
              meta: {
                skeleton: () => (
                  <div>
                    <Placeholder variant="block" width="18ch" />
                    <Placeholder variant="block" width="14ch" />
                  </div>
                ),
              },
            },
            {
              accessorKey: "status",
              header: () => <Placeholder variant="block" width="10ch" />,
              meta: {
                skeleton: () => <Placeholder variant="block" width="12ch" />,
              },
            },
            {
              accessorKey: "updated",
              header: () => <Placeholder variant="block" width="16ch" />,
              meta: {
                skeleton: () => <Placeholder variant="block" width="10ch" />,
              },
            },
            {
              accessorKey: "actions",
              header: () => <Placeholder variant="block" width="10ch" />,
              meta: {
                skeleton: () => (
                  <div>
                    <Placeholder variant="block" width="2ch" />
                    <Placeholder variant="block" width="2ch" />
                  </div>
                ),
              },
            },
          ]}
          data={[]}
          isLoading
          loadingVariant="skeleton"
        />
      </ContentSection.Content>
    </ContentSection>
  );
};

Layout.Skeleton = LayoutSkeleton;

export default Layout;
