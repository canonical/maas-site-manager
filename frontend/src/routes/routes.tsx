import RequireLogin from "./RequireLogin";

import Layout from "@/app/base/components/Layout";
import { lazyWithErrorBoundary } from "@/utils/hoc";
import { createRoutesFromElements, redirect, Route } from "@/utils/router";

const Logout = lazyWithErrorBoundary(() => import("@/routes/logout"));
const Login = lazyWithErrorBoundary(() => import("@/routes/login"));
const NotFound = lazyWithErrorBoundary(() => import("@/routes/404"));
const Sites = lazyWithErrorBoundary(() => import("@/routes/sites"));
const List = lazyWithErrorBoundary(() => import("@/routes/sites/list"));
const Map = lazyWithErrorBoundary(() => import("@/routes/sites/map"));
const ImagesList = lazyWithErrorBoundary(() => import("@/app/images/views/ImagesList"));
const Settings = lazyWithErrorBoundary(() => import("@/routes/settings"));
const Tokens = lazyWithErrorBoundary(() => import("@/routes/tokens/tokens"));
const Requests = lazyWithErrorBoundary(() => import("@/routes/requests"));
const Users = lazyWithErrorBoundary(() => import("@/routes/users"));
const MapSettings = lazyWithErrorBoundary(() => import("@/app/settings/views/MapSettings"));
const Account = lazyWithErrorBoundary(() => import("@/routes/account"));
const PersonalDetails = lazyWithErrorBoundary(() => import("@/routes/personalDetails"));
const Password = lazyWithErrorBoundary(() => import("@/routes/account/password"));
const ImageSources = lazyWithErrorBoundary(() => import("@/routes/settings/images/source"));

export const routes = createRoutesFromElements(
  <Route element={<Layout />} path="/">
    <Route element={<Logout />} path="logout" />
    <Route element={<Login />} path="login" />
    <Route element={<RequireLogin />}>
      <Route element={<NotFound />} path="*" />
      <Route index loader={() => redirect("/sites")} />
      <Route element={<Sites />} path="sites">
        <Route index loader={() => redirect("/sites/list")} />
        <Route element={<List />} index path="list" />
        <Route element={<Map />} index path="map" />
      </Route>
      <Route path="images">
        <Route index loader={() => redirect("/images/list")} />
        <Route element={<ImagesList />} index path="list" />
      </Route>
      <Route element={<Settings />} path="settings">
        <Route element={<RequireLogin />} index loader={() => redirect("/settings/tokens")} />
        <Route element={<Tokens />} path="tokens" />
        <Route element={<Requests />} path="requests" />
        <Route element={<Users />} path="users" />
        <Route element={<MapSettings />} path="map" />
        <Route path="images">
          <Route element={<RequireLogin />} index loader={() => redirect("/settings/images/source")} />
          <Route element={<ImageSources />} path="source" />
        </Route>
      </Route>
      <Route element={<Account />} path="account">
        <Route element={<RequireLogin />} index loader={() => redirect("/account/details")} />
        <Route element={<PersonalDetails />} path="details" />
        <Route element={<Password />} path="password" />
      </Route>
    </Route>
  </Route>,
);

export default routes;
