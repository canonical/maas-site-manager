import classNames from "classnames";

import useSecondaryNavContext from "@/app/base/hooks/useSecondaryNavContext";
import type { RoutePath, RouteTitle } from "@/app/base/routes";
import type { Location } from "@/utils/router";
import { Link, matchPath, useLocation } from "@/utils/router";

export type NavItem =
  | {
      label: RouteTitle;
      path: RoutePath;
      items?: never;
    }
  | {
      label: string;
      path?: never;
      items: {
        label: RouteTitle;
        path: RoutePath;
      }[];
    };

type ItemProps = { item: NavItem };

const SideNavigationLink = ({ item }: ItemProps) => {
  const location = useLocation();
  const isActive = getIsActive({ item, location });
  if (!item.path) {
    return null;
  }
  return (
    <Link
      aria-current={isActive ? "page" : undefined}
      className={classNames("p-side-navigation__link", {
        "is-active": isActive,
      })}
      to={item.path}
    >
      {item.label}
    </Link>
  );
};
const SubNavItem = ({ item }: ItemProps) => {
  return (
    <li className="p-side-navigation__item" key={item.path}>
      <SideNavigationLink item={item} />
    </li>
  );
};

const SubNavigation = ({ items }: { items: NavItem["items"] }) => {
  if (!items || !items.length) return null;

  return (
    <ul className="p-side-navigation__list">
      {items.map((item) => (
        <SubNavItem item={item} key={item.path} />
      ))}
    </ul>
  );
};

const getIsActive = ({ item, location }: ItemProps & { location: Location }) => {
  const path = item.path;

  if (!path) {
    return false;
  }

  if (!item.items) {
    return location.pathname.startsWith(path);
  }

  return matchPath(path, location.pathname);
};

const SideNavigationItem = ({ item }: ItemProps) => {
  const location = useLocation();
  const isActive = getIsActive({ item, location });
  const itemClassName = classNames("p-side-navigation__item--title", {
    "is-active": isActive,
  });

  return (
    <li className={itemClassName} key={item.path || item.label}>
      {item.path ? (
        <SideNavigationLink item={item} />
      ) : (
        <span className="p-side-navigation__text p-side-navigation__item">{item.label}</span>
      )}
      {item.items ? <SubNavigation items={item.items} /> : null}
    </li>
  );
};

export type SecondaryNavContext = "account" | "settings";

export type SecondaryNavInfoType = Record<
  SecondaryNavContext,
  {
    title: RouteTitle;
    navItems: NavItem[];
  }
>;

type SecondaryNavigationProps = {
  isOpen?: boolean;
};

const secondaryNavInfo: SecondaryNavInfoType = {
  settings: {
    title: "Settings",
    navItems: [
      {
        label: "Enrollment",
        items: [
          { path: "/settings/tokens", label: "Tokens" },
          {
            path: "/settings/requests",
            label: "Requests",
          },
        ],
      },
      {
        label: "Users",
        path: "/settings/users",
      },
      {
        label: "Map",
        path: "/settings/map",
      },
      {
        label: "Single sign-on",
        path: "/settings/single-sign-on",
      },
      {
        label: "Images",
        items: [{ path: "/settings/images/source", label: "Source" }],
      },
    ],
  },
  account: {
    title: "Account",
    navItems: [
      {
        label: "",
        items: [
          { path: "/account/details", label: "Personal Details" },
          { path: "/account/password", label: "Password" },
        ],
      },
    ],
  },
};

export const SecondaryNavigation = ({ isOpen }: SecondaryNavigationProps) => {
  const context = useSecondaryNavContext();
  const { title, navItems } = secondaryNavInfo[context];
  return (
    <div className={classNames("p-side-navigation is-maas-site-manager is-dark", { "is-open": isOpen })}>
      <nav className="p-side-navigation__drawer u-padding-top--medium">
        <h2 className="p-side-navigation__title p-heading--4 p-panel__logo-name">{title}</h2>
        <ul className="p-side-navigation__list">
          {navItems.map((item) => (
            <SideNavigationItem item={item} key={item.label} />
          ))}
        </ul>
      </nav>
    </div>
  );
};

export default SecondaryNavigation;
