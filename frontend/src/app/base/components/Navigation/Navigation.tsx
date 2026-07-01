import type { ReactElement } from "react";

import { Navigation, NavigationBar } from "@canonical/maas-react-components";
import { Button, ButtonAppearance, Icon } from "@canonical/react-components";
import useLocalStorageState from "use-local-storage-state";

import NavigationBanner from "./NavigationBanner";
import NavigationItem from "./NavigationItem";
import NavigationList from "./NavigationList";
import type { ExternalNavLink, LocalNavLink } from "./types";

import { useCurrentUser } from "@/app/api/query/users";
import BREAKPOINTS from "@/app/base/breakpoints";
import useDarkMode from "@/app/base/hooks/useDarkMode";
import { useGlobalKeyShortcut } from "@/app/base/hooks/useGlobalKeyShortcut";
import type { RoutePath } from "@/app/base/routes";
import { useAuthContext } from "@/app/context";
import { useLocation, useNavigate } from "@/utils/router";

export const navItems: LocalNavLink[] = [
  {
    label: "Sites",
    url: "/sites",
    icon: "machines",
  },
  {
    label: "Images",
    url: "/images",
    icon: "applications",
  },
];

export const settingsNavItems: LocalNavLink[] = [
  {
    label: "Settings",
    url: "/settings",
    icon: "settings",
  },
];

export const navItemsBottom: ExternalNavLink[] = [
  { external: true, icon: "information", label: "Documentation", url: "https://maas.io/docs" },
  { external: true, icon: "comments", label: "Community", url: "https://discourse.maas.io/" },
  {
    external: true,
    icon: "submit-bug",
    label: "Report a bug",
    url: "https://bugs.launchpad.net/maas-site-manager/+filebug",
  },
];

type NavProps = {
  isLoggedIn: boolean;
};

const AccountNavigationList = ({ handleNavlinkClick, path }: { handleNavlinkClick: () => void; path: RoutePath }) => {
  const { data } = useCurrentUser();
  const { logout } = useAuthContext();
  const navigate = useNavigate();

  return (
    <Navigation.List>
      <NavigationItem
        navLink={{ label: data?.username || "User", url: "/account" }}
        onClick={handleNavlinkClick}
        path={path}
      />
      <NavigationItem
        navLink={{ label: "Log out", url: "/logout" }}
        onClick={() => logout().then(() => navigate("/login"))}
        path={path}
      />
    </Navigation.List>
  );
};

const DarkModeToggle = (): ReactElement => {
  const [isDarkMode, toggleDarkMode] = useDarkMode();

  return (
    <Button
      appearance={ButtonAppearance.BASE}
      aria-label={isDarkMode ? "Light mode" : "Dark mode"}
      className="dark-mode-toggle"
      hasIcon
      onClick={(event: React.MouseEvent<HTMLElement>) => {
        toggleDarkMode();
        // Remove focus so the side navigation can collapse on mouseleave.
        event.currentTarget.blur();
      }}
    >
      <Icon light name={isDarkMode ? "highlight-on" : "highlight-off"} />
    </Button>
  );
};

const AppNavigation = ({ isLoggedIn }: NavProps): ReactElement => {
  const [isCollapsed, setIsCollapsed] = useLocalStorageState<boolean>("appSideNavIsCollapsed", { defaultValue: true });
  const location = useLocation();
  const path = location.pathname;

  useEffect(() => {
    if (!isLoggedIn) {
      setIsCollapsed(true);
    }
  }, [isLoggedIn, setIsCollapsed]);

  const handleNavlinkClick = () => {
    if (window.screen.width <= BREAKPOINTS.small) {
      setIsCollapsed(true);
    }
  };

  useGlobalKeyShortcut("[", () => {
    setIsCollapsed(!isCollapsed);
  });

  return (
    <>
      <NavigationBar className="l-navigation-bar">
        <Navigation.Header>
          <NavigationBanner />
          <Navigation.Controls>
            <NavigationBar.MenuButton
              onClick={() => {
                setIsCollapsed(!isCollapsed);
              }}
            >
              Menu
            </NavigationBar.MenuButton>
          </Navigation.Controls>
        </Navigation.Header>
      </NavigationBar>
      <Navigation isCollapsed={isCollapsed}>
        <Navigation.Drawer>
          <Navigation.Header>
            <NavigationBanner>
              <Navigation.Controls>
                <Navigation.CollapseToggle isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
                <NavigationBar.MenuButton
                  onClick={() => {
                    setIsCollapsed(!isCollapsed);
                  }}
                >
                  Close menu
                </NavigationBar.MenuButton>
              </Navigation.Controls>
            </NavigationBanner>
          </Navigation.Header>
          <Navigation.Content>
            {isLoggedIn && (
              <>
                <NavigationList items={navItems} onClick={handleNavlinkClick} path={path} />
                <NavigationList items={settingsNavItems} onClick={handleNavlinkClick} path={path} />
                <AccountNavigationList handleNavlinkClick={handleNavlinkClick} path={path} />
              </>
            )}
          </Navigation.Content>
          <Navigation.Footer>
            <Navigation.Content>
              <NavigationList hideDivider items={navItemsBottom} onClick={handleNavlinkClick} path={path} />
            </Navigation.Content>
          </Navigation.Footer>
          <DarkModeToggle />
        </Navigation.Drawer>
      </Navigation>
    </>
  );
};

export default AppNavigation;
