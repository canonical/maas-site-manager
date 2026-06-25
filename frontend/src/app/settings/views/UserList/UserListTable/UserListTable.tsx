import type { Dispatch, SetStateAction } from "react";

import { Button, Icon, Tooltip } from "@canonical/react-components";
import { useReactTable, getCoreRowModel, flexRender } from "@tanstack/react-table";
import type { SortingState, Column, ColumnDef } from "@tanstack/react-table";
import classNames from "classnames";

import { useCurrentUser, type UseUsersResult } from "@/app/api/query/users";
import type { User } from "@/app/apiclient";
import DynamicTable from "@/app/base/components/DynamicTable/DynamicTable";
import SortIndicator from "@/app/base/components/SortIndicator";
import TableCaption from "@/app/base/components/TableCaption/TableCaption";
import { useAppLayoutContext } from "@/app/context";
import { useUserSelectionContext } from "@/app/context/UserSelectionContext";
import { createAccessor } from "@/utils";
import { useNavigate } from "@/utils/router";

export type UserColumnDef = ColumnDef<User, User>;
export type UserColumn = Column<User>;

type SortProps = {
  sorting: SortingState;
  setSorting: Dispatch<SetStateAction<SortingState>>;
};

const UserListTable = ({
  data,
  error,
  isPending,
  setSorting,
  sorting,
}: Pick<UseUsersResult, "data" | "error" | "isPending"> & SortProps) => {
  const [isShowingFullName, setIsShowingFullName] = useState(false);
  const { setSelected: setSelectedUserId } = useUserSelectionContext();
  const { setSidebar } = useAppLayoutContext();
  const { data: currentUser } = useCurrentUser();
  const currentUsername = currentUser?.username;
  const navigate = useNavigate();

  const columns = useMemo<UserColumnDef[]>(
    () => [
      {
        id: isShowingFullName ? "full_name" : "username",
        enableSorting: false,
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
        accessorKey: isShowingFullName ? "full_name" : "username",
        accessorFn: createAccessor(["full_name", "username"]),
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
        enableSorting: true,
        header: ({ header }) => (
          <div>
            Email <SortIndicator header={header} />
          </div>
        ),
        accessorFn: createAccessor("email"),
        cell: ({ getValue }) => {
          const { email } = getValue();
          return <div>{email}</div>;
        },
      },
      {
        id: "is_admin",
        accessorKey: "is_admin",
        enableSorting: false,
        header: () => <div>Role</div>,
        accessorFn: createAccessor("is_admin"),
        cell: ({ getValue }) => {
          const { is_admin } = getValue();
          return <div>{is_admin ? "Admin" : "User"}</div>;
        },
      },
      {
        id: "actions",
        accessorKey: ["username", "id"],
        accessorFn: createAccessor(["username", "id"]),
        enableSorting: false,
        header: () => <div>Actions</div>,
        cell: ({ getValue }) => {
          const { username, id } = getValue();
          const editLabel = `Edit ${username}`;
          const deleteLabel = `Delete ${username}`;
          return (
            <div>
              <Button
                appearance="base"
                aria-label={editLabel}
                className="is-dense u-table-cell-padding-overlap"
                onClick={() => {
                  if (username !== currentUsername) {
                    setSelectedUserId(id);
                    setSidebar("editUser");
                  } else {
                    navigate("/account/details");
                  }
                }}
              >
                <Icon name="edit" />
              </Button>
              <Tooltip message={currentUsername === username ? "You cannot delete your own user." : null}>
                <Button
                  appearance="base"
                  aria-label={deleteLabel}
                  className="is-dense u-table-cell-padding-overlap"
                  disabled={currentUsername === username}
                  onClick={() => {
                    setSelectedUserId(id);
                    setSidebar("deleteUser");
                  }}
                >
                  <Icon name="delete" />
                </Button>
              </Tooltip>
            </div>
          );
        },
      },
    ],
    [currentUsername, isShowingFullName, navigate, setSelectedUserId, setSidebar],
  );

  const noItems = useMemo<User[]>(() => [], []);
  const pageCount = data && "total" in data ? Math.ceil(data.total / data.size) : 0;
  const pageIndex = data && "page" in data ? data.page : 0;
  const pageSize = data && "size" in data ? data.size : 0;
  const userTable = useReactTable<User>({
    data: data?.items || noItems,
    columns,
    state: {
      pagination: {
        pageIndex,
        pageSize,
      },
      sorting,
    },
    onSortingChange: setSorting,
    manualPagination: true,
    pageCount,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    enableSorting: true,
  });

  return (
    <DynamicTable aria-label="users" className="user-list__table">
      <thead>
        {userTable.getHeaderGroups().map((headerGroup) => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <th
                className={classNames(header.column.id, { "p-button--table-header": header?.column?.getCanSort() })}
                colSpan={header.colSpan}
                key={header.id}
                onClick={header.column.getToggleSortingHandler()}
              >
                {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      {error ? (
        <TableCaption inTable>
          <TableCaption.Error error={{ body: error }} />
        </TableCaption>
      ) : isPending ? (
        <DynamicTable.Loading table={userTable} />
      ) : (
        <DynamicTable.Body>
          {userTable.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => {
                return <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>;
              })}
            </tr>
          ))}
        </DynamicTable.Body>
      )}
    </DynamicTable>
  );
};

export default UserListTable;
