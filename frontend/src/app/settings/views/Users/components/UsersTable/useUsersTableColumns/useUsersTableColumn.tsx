import { Placeholder } from "@canonical/maas-react-components";
import { Button } from "@canonical/react-components";
import type { ColumnDef } from "@tanstack/react-table";

import { useCurrentUser } from "@/app/api/query/users";
import type { User } from "@/app/apiclient";
import SortIndicator from "@/app/base/components/SortIndicator";
import TableActions from "@/app/base/components/TableActions";
import { useAppLayoutContext, useUserSelectionContext } from "@/app/context";
import { createAccessor } from "@/utils";
import { useNavigate } from "@/utils/router";

type UserColumnDef = ColumnDef<User, Partial<User>>;

export const useUsersTableColumns = () => {
  const { setSidebar } = useAppLayoutContext();
  const { setSelected: setSelectedUserId } = useUserSelectionContext();
  const [isShowingFullName, setIsShowingFullName] = useState(false);
  const { data: currentUser } = useCurrentUser();
  const currentUsername = currentUser?.username;

  const navigate = useNavigate();

  return useMemo<UserColumnDef[]>(
    () => [
      {
        id: isShowingFullName ? "full-name" : "username",
        accessorKey: isShowingFullName ? "full_name" : "username",
        accessorFn: createAccessor(["full_name", "username"]),
        enableSorting: false,
        meta: { isInteractiveHeader: true },
        header: ({ header, column }) => (
          <div>
            <Button
              appearance="link"
              className="p-button--table-header"
              onClick={() => {
                if (isShowingFullName) {
                  setIsShowingFullName(false);
                } else {
                  column.toggleSorting();
                }
              }}
            >
              Username
              {!isShowingFullName && (
                <>
                  {" "}
                  <SortIndicator header={header} />
                </>
              )}
            </Button>{" "}
            |{" "}
            <Button
              appearance="link"
              className="p-button--table-header"
              onClick={() => {
                if (!isShowingFullName) {
                  setIsShowingFullName(true);
                } else {
                  column.toggleSorting();
                }
              }}
            >
              Full name {isShowingFullName && <SortIndicator header={header} />}
            </Button>
          </div>
        ),
        cell: ({ getValue }) => {
          if (isShowingFullName) {
            const { full_name } = getValue();
            return <div>{full_name ? full_name : <>&mdash;</>}</div>;
          } else {
            const { username } = getValue();
            return <div>{username}</div>;
          }
        },
      },
      {
        id: "email",
        accessorKey: "email",
        accessorFn: createAccessor("email"),
        enableSorting: true,
        header: "Email",
        cell: ({
          row: {
            original: { email },
          },
        }) => email,
      },
      {
        id: "role",
        accessorKey: "is_admin",
        accessorFn: createAccessor("is_admin"),
        enableSorting: false,
        header: "Role",
        cell: ({
          row: {
            original: { is_admin },
          },
        }) => (is_admin ? "Admin" : "User"),
      },
      {
        id: "actions",
        accessorKey: ["username", "id"],
        accessorFn: createAccessor(["username", "id"]),
        enableSorting: false,
        header: "Actions",
        meta: {
          skeleton: () => (
            <div>
              <Placeholder variant="block" width="1.5rem" />
              <Placeholder variant="block" width="1.5rem" />
            </div>
          ),
        },
        cell: ({
          row: {
            original: { id, username },
          },
        }) => {
          return (
            <TableActions
              className="u-align--right"
              deleteDisabled={currentUsername === username}
              deleteTooltip={currentUsername === username ? "You cannot delete your own user." : undefined}
              hasBorder
              onDelete={() => {
                setSelectedUserId(id);
                setSidebar("deleteUser");
              }}
              onEdit={() => {
                if (username !== currentUsername) {
                  setSelectedUserId(id);
                  setSidebar("editUser");
                } else {
                  navigate("/account/details");
                }
              }}
            />
          );
        },
      },
    ],
    [currentUsername, isShowingFullName, navigate, setSelectedUserId, setSidebar],
  );
};
