import { Button, Input, Notification, Spinner } from "@canonical/react-components";
import { Field, Form, Formik } from "formik";
import * as Yup from "yup";

import { useDeleteUser, useUser } from "@/app/api/query/users";
import ErrorMessage from "@/app/base/components/ErrorMessage";
import RemoveButton from "@/app/base/components/RemoveButton";
import { useAppLayoutContext, useUserSelectionContext } from "@/app/context";
import type { UserSelectionContextValue } from "@/app/context/UserSelectionContext";

type DeleteUserFormValues = { confirmUsername: string };
const createValidationSchema = (username: string) => {
  return Yup.object().shape({
    confirmUsername: Yup.string()
      .required("This field is required.")
      .test("exact-match", `Confirmation username is not correct. Expected ${username}`, (value) => value === username),
  });
};

const DeleteUserContent = ({
  selectedUserId,
  setSelectedUserId,
}: {
  selectedUserId: NonNullable<UserSelectionContextValue["selected"]>;
  setSelectedUserId: NonNullable<UserSelectionContextValue["setSelected"]>;
}) => {
  const id = useId();
  const { setSidebar } = useAppLayoutContext();
  const {
    data: user,
    error,
    isError,
    isPending,
    isSuccess: getUserSuccess,
  } = useUser({ path: { id: selectedUserId } });

  const deleteUserMutation = useDeleteUser();
  const headingId = `heading-${id}`;
  const confirmInputId = `confirm-${id}`;
  const initialValues = {
    confirmUsername: "",
  };

  const handleSubmit = () => {
    if (getUserSuccess) {
      deleteUserMutation.mutate(
        { path: { id: user.id } },
        {
          onSuccess() {
            setSidebar(null);
            setSelectedUserId(null);
          },
        },
      );
    }
  };

  const username = getUserSuccess ? user.username : "";
  return (
    <>
      {isError && (
        <Notification severity="negative" title="Error while fetching user">
          <ErrorMessage error={error} />
        </Notification>
      )}
      {isPending ? (
        <Spinner text="Loading..." />
      ) : (
        <Formik<DeleteUserFormValues>
          initialValues={initialValues}
          onSubmit={handleSubmit}
          validationSchema={createValidationSchema(username)}
        >
          {({ isSubmitting, errors, touched, dirty, isValid }) => (
            <Form aria-labelledby={headingId} noValidate>
              <div>
                <h3 className="p-heading--4" id={headingId}>
                  Delete <strong>{username}</strong>
                </h3>
                {deleteUserMutation.isError && (
                  <Notification severity="negative" title="Delete Failed">
                    {deleteUserMutation.error instanceof Error
                      ? deleteUserMutation.error.message
                      : "An unknown error occured."}
                  </Notification>
                )}
                <p>
                  Are you sure you want to delete user "{username}"? This action is permanent and can not be undone.
                </p>
                <p id={confirmInputId}>
                  Type <strong>{username}</strong> to confirm
                </p>
                <Field
                  aria-labelledby={confirmInputId}
                  as={Input}
                  error={touched.confirmUsername && errors.confirmUsername}
                  name="confirmUsername"
                  placeholder={username}
                  type="text"
                />
                <hr className="is-muted" />
                <div className="u-padding-top--medium u-flex u-flex--justify-end">
                  <Button
                    appearance="base"
                    onClick={() => {
                      setSidebar(null);
                    }}
                    type="button"
                  >
                    Cancel
                  </Button>
                  <RemoveButton
                    disabled={!dirty || isSubmitting || !isValid}
                    label="Delete"
                    showDeleteIcon
                    type="submit"
                  />
                </div>
              </div>
            </Form>
          )}
        </Formik>
      )}
    </>
  );
};

const DeleteUser = () => {
  const { selected: selectedUserId, setSelected: setSelectedUserId } = useUserSelectionContext();

  return selectedUserId ? (
    <DeleteUserContent selectedUserId={selectedUserId} setSelectedUserId={setSelectedUserId} />
  ) : null;
};

export default DeleteUser;
