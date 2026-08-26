export const protectedRoutes = {
  homepage: {
    path: "/",
    title: "Homepage",
  },
  sites: {
    path: "/sites",
    title: "Sites",
  },
  sitesList: {
    path: "/sites/list",
    title: "Sites List",
  },
  sitesMap: {
    path: "/sites/map",
    title: "Sites Map",
  },
  settings: {
    path: "/settings",
    title: "Settings",
  },
  requests: {
    path: "/settings/requests",
    title: "Requests",
  },
  tokens: {
    path: "/settings/tokens",
    title: "Tokens",
  },
  users: {
    path: "/settings/users",
    title: "Users",
  },
  mapSettings: {
    path: "/settings/map",
    title: "Map",
  },
  singleSignOn: {
    path: "/settings/single-sign-on",
    title: "OIDC/Single sign-on",
  },
  settingsImages: {
    path: "/settings/images",
    title: "",
  },
  settingsImagesSource: {
    path: "/settings/images/source",
    title: "Image sources",
  },
  account: {
    path: "/account",
    // title is dynamic and based on a user name
    title: "Account" as string,
  },
  personalDetails: {
    path: "/account/details",
    title: "Personal Details",
  },
  images: {
    path: "/images",
    title: "",
  },
  imagesList: {
    path: "/images/list",
    title: "Images list",
  },
  password: {
    path: "/account/password",
    title: "Password",
  },
  logout: {
    path: "/logout",
    title: "Log out",
  },
} as const;

export const publicRoutes = {
  index: { path: "/", title: "" },
  login: {
    path: "/login",
    title: "Login",
  },
  loginCallback: {
    path: "/login/oidc/callback",
    title: "Login",
  },
} as const;

export const routesConfig = { ...publicRoutes, ...protectedRoutes } as const;

const redirectRoutes = [
  routesConfig.index.path,
  routesConfig.sites.path,
  routesConfig.settings.path,
  routesConfig.settingsImages.path,
  routesConfig.account.path,
  routesConfig.images.path,
  routesConfig.logout.path,
];

// pages without redirect routes
export const protectedPages = Object.values(protectedRoutes).filter((route) => !redirectRoutes.includes(route?.path));
export const publicPages = Object.values(publicRoutes).filter((route) => !redirectRoutes.includes(route?.path));
export const pages = [...protectedPages, ...publicPages];

type RoutesConfig = typeof routesConfig;
export type RoutePath = RoutesConfig[keyof RoutesConfig]["path"];
export type RouteTitle = RoutesConfig[keyof RoutesConfig]["title"];
