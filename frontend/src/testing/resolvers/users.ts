import { http, HttpResponse } from "msw";

import type { SortDirection, UserSortKey } from "@/app/api/handlers";
import type {
  DeleteV1UsersIdDeleteError,
  GetV1UsersGetError,
  PatchV1UsersIdPatchError,
  PostV1UsersPostError,
  User,
  UsersPostRequest,
} from "@/app/apiclient";
import { ExceptionCode } from "@/app/apiclient";
import { userFactory } from "@/mocks/factories";
import { apiUrls } from "@/utils/test-urls";

const mockUsers = [
  userFactory.build({
    email: "admin@example.com",
    full_name: "MAAS Admin",
    id: 1,
    is_admin: true,
    username: "maas-admin",
  }),
  userFactory.build({
    email: "user1@example.com",
    full_name: "User One",
    id: 2,
    is_admin: false,
    username: "user1",
  }),
  userFactory.build({
    email: "user2@example.com",
    full_name: "",
    id: 3,
    is_admin: false,
    username: "user2",
  }),
];

const mockListGetUsersError: GetV1UsersGetError = {
  error: {
    code: ExceptionCode.NOT_AUTHENTICATED,
    message: "internal server error",
  },
};

const mockPatchUsersError: PatchV1UsersIdPatchError = {
  error: {
    code: ExceptionCode.MISSING_PERMISSIONS,
    message: "You do not have permission to update this user",
  },
};

const mockPostUsersError: PostV1UsersPostError = {
  error: {
    code: ExceptionCode.INVALID_PARAMETERS,
    message: "Invalid parameters",
  },
};

const mockDeleteUserError: DeleteV1UsersIdDeleteError = {
  error: {
    code: ExceptionCode.MISSING_PERMISSIONS,
    message: "You do not have permission to delete this user",
  },
};

const usersResolvers = {
  listUsers: {
    resolved: false,
    handler: (data: User[] = mockUsers) => {
      return http.get(apiUrls.users, ({ request }) => {
        const searchParams = new URL(request.url).searchParams;
        const page = Number(searchParams.get("page"));
        const size = Number(searchParams.get("size"));

        // sort items
        const items = [...data];
        const sortBy = searchParams.get("sortBy");
        if (sortBy) {
          const [field, order] = sortBy.split("-") as [UserSortKey, SortDirection];
          items.sort((a, b) => {
            if (order === "asc") {
              return a[field] > b[field] ? 1 : -1;
            }
            return a[field] < b[field] ? 1 : -1;
          });
        }

        const itemsPage = items.slice((page - 1) * size, page * size);

        const response = {
          items: itemsPage,
          page,
          total: data.length,
        };
        usersResolvers.listUsers.resolved = true;
        return HttpResponse.json(response);
      });
    },
    error: (error: GetV1UsersGetError = mockListGetUsersError) => {
      return http.get(apiUrls.users, () => {
        usersResolvers.listUsers.resolved = true;
        return HttpResponse.json(error, { status: 401 });
      });
    },
  },
  getUser: {
    resolved: false,
    handler: (data: User[] = mockUsers) => {
      return http.get(`${apiUrls.users}/:id`, ({ params }) => {
        usersResolvers.getUser.resolved = true;
        const id = params.id;
        if (id === "me") {
          const user = userFactory.build(
            data ? data[0] : { username: "admin", full_name: "MAAS Admin", email: "admin@example.com" },
          );
          return HttpResponse.json(user);
        }
        const user = data.find((user) => user.id === Number(id));
        return user ? HttpResponse.json(user) : HttpResponse.error();
      });
    },
    error: (error: GetV1UsersGetError = mockListGetUsersError) => {
      return http.get(`${apiUrls.users}/:id`, ({ params }) => {
        usersResolvers.getUser.resolved = true;
        const id = params.id;
        if (id === "me") {
          return HttpResponse.json(error, { status: 401 });
        }
        return HttpResponse.json(error, { status: 404 });
      });
    },
  },
  getCurrentUser: {
    resolved: false,
    handler: (data: User = mockUsers[0]) => {
      return http.get(apiUrls.currentUser, () => {
        const user = userFactory.build(
          data ? data : { username: "admin", full_name: "MAAS Admin", email: "admin@example.com" },
        );
        usersResolvers.getCurrentUser.resolved = true;
        return HttpResponse.json(user);
      });
    },
    error: (error: GetV1UsersGetError = mockListGetUsersError) => {
      usersResolvers.getCurrentUser.resolved = true;
      return http.get(apiUrls.currentUser, () => {
        return HttpResponse.json(error, { status: 401 });
      });
    },
  },
  updateUser: {
    resolved: false,
    handler: () => {
      return http.patch(`${apiUrls.users}/:id`, async ({ request, params }) => {
        const { full_name, username, email, is_admin } = (await request.json()) as UsersPostRequest;
        const id = params.id;
        const user = { id: Number(id), full_name, username, email, is_admin };
        usersResolvers.updateUser.resolved = true;
        return HttpResponse.json(user);
      });
    },
    error: (error: PatchV1UsersIdPatchError = mockPatchUsersError) => {
      return http.patch(`${apiUrls.users}/:id`, () => {
        usersResolvers.updateUser.resolved = true;
        return HttpResponse.json(error, { status: 403 });
      });
    },
  },
  updateCurrentUser: {
    resolved: false,
    handler: () => {
      return http.patch(apiUrls.currentUser, async () => {
        usersResolvers.updateCurrentUser.resolved = true;
        return new HttpResponse(null, { status: 200 });
      });
    },
    error: (error: PatchV1UsersIdPatchError = mockPatchUsersError) => {
      return http.patch(apiUrls.currentUser, () => {
        usersResolvers.updateCurrentUser.resolved = true;
        return HttpResponse.json(error, { status: 403 });
      });
    },
  },
  updateCurrentUserPassword: {
    resolved: false,
    handler: () => {
      return http.patch(`${apiUrls.currentUser}/password`, async () => {
        usersResolvers.updateCurrentUserPassword.resolved = true;
        return new HttpResponse(null, { status: 200 });
      });
    },
    error: (error: PatchV1UsersIdPatchError = mockPatchUsersError) => {
      return http.patch(`${apiUrls.currentUser}/password`, () => {
        usersResolvers.updateCurrentUserPassword.resolved = true;
        return HttpResponse.json(error, { status: 403 });
      });
    },
  },
  createUser: {
    resolved: false,
    handler: () => {
      return http.post(apiUrls.users, async ({ request }) => {
        const { username, full_name, email, is_admin } = (await request.json()) as UsersPostRequest;
        const newUser = userFactory.build({ username, full_name, email, is_admin });
        usersResolvers.createUser.resolved = true;
        return new HttpResponse(JSON.stringify(newUser), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        });
      });
    },
    error: (error: PostV1UsersPostError = mockPostUsersError) => {
      return http.post(apiUrls.users, () => {
        usersResolvers.createUser.resolved = true;
        return HttpResponse.json(error, { status: 400 });
      });
    },
  },
  deleteUser: {
    resolved: false,
    handler: () => {
      return http.delete(`${apiUrls.users}/:id`, async () => {
        usersResolvers.deleteUser.resolved = true;
        return new HttpResponse(null, { status: 204 });
      });
    },
    error: (error: DeleteV1UsersIdDeleteError = mockDeleteUserError) => {
      return http.delete(`${apiUrls.users}/:id`, () => {
        usersResolvers.deleteUser.resolved = true;
        return HttpResponse.json(error, { status: 403 });
      });
    },
  },
};
export { usersResolvers, mockUsers };
