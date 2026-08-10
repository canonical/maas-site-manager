import Navigation from "@/app/base/components/Navigation";
import SecondaryNavigation from "@/app/base/components/SecondaryNavigation";
import type { RoutePath } from "@/app/base/routes";
import { routesConfig } from "@/app/base/routes";
import { useAuthContext } from "@/app/context";
import { matchPath, Outlet, useLocation } from "@/utils/router";
import Layout from "@/app/base/components/Layout";

const getPageTitle = (pathname: RoutePath) => {
  const title = Object.values(routesConfig).find(({ path }) => path === pathname)?.title;
  return title ? `${title} | MAAS Site Manager` : "MAAS Site Manager";
};

const AppLayout = () => {
  const { pathname } = useLocation();
  const { status } = useAuthContext();
  const isLoggedIn = status === "authenticated";
  const isSideNavVisible = matchPath("/settings/*", pathname) || matchPath("/account/*", pathname);
  const isTableView = pathname.endsWith("/list") || (pathname.startsWith("/settings/") && pathname !== "/settings/map");

  const pageTitle = getPageTitle(pathname as RoutePath);

  return (
    <Layout
      isSecondaryNavVisible={!!isSideNavVisible}
      navigation={<Navigation isLoggedIn={isLoggedIn} />}
      className="is-maas-site-manager"
      pageTitle={pageTitle}
      secondaryNavigation={<SecondaryNavigation isOpen={!!isSideNavVisible} />}
      view={isTableView ? "table" : "settings"}
    >
      <Outlet />
    </Layout>
  );
};

export default AppLayout;
