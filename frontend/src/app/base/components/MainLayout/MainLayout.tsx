import { Suspense } from "react";

import { ContentSection } from "@canonical/maas-react-components";
import { Application, AppMain, Spinner } from "@canonical/react-components";
import classNames from "classnames";

import { Aside } from "./components/Aside";

import DocumentTitle from "@/app/base/components/MainLayout/components/DocumentTitle/DocumentTitle";
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

const MainLayout: React.FC = () => {
  const { pathname } = useLocation();
  const { status } = useAuthContext();
  const isLoggedIn = status === "authenticated";
  const isSideNavVisible = matchPath("/settings/*", pathname) || matchPath("/account/*", pathname);

  return (
    <Application>
      <Navigation isLoggedIn={isLoggedIn} />
      <AppMain className="is-maas-site-manager">
        <h1 className="u-visually-hidden">{getPageTitle(pathname as RoutePath)}</h1>
        <div className={classNames("l-main__nav", { "is-open": isSideNavVisible })}>
          <SecondaryNavigation isOpen={!!isSideNavVisible} />
        </div>
        <div className="l-main__content">
          <div className="row">
            <div className="col-12">
              <Suspense
                fallback={
                  <ContentSection>
                    <Spinner text="Loading..." />
                  </ContentSection>
                }
              >
                <Outlet />
              </Suspense>
            </div>
          </div>
        </div>
      </AppMain>
      <Aside />
      <StatusBar />
    </Application>
  );
};

const Layout = () => {
  const { pathname } = useLocation();
  return (
    <>
      <DocumentTitle>{getPageTitle(pathname as RoutePath)}</DocumentTitle>
      <MainLayout />
    </>
  );
};

export default Layout;
