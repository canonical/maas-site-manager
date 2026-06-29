import { ContentSection } from "@canonical/maas-react-components";
import { ActionButton, Button, Input, Label, Notification, Spinner } from "@canonical/react-components";
import { Field, Formik } from "formik";
import isEqual from "lodash/isEqual";
import * as Yup from "yup";

import type { MutationErrorResponse } from "@/app/api";
import { useAddUser, useEditUser, useUser } from "@/app/api/query/users";
import ErrorMessage from "@/app/base/components/ErrorMessage/ErrorMessage";
import FormikFormContent from "@/app/base/components/FormikFormContent";
import { useAppLayoutContext } from "@/app/context";
import { useUserSelectionContext } from "@/app/context/UserSelectionContext";

const baseInitialValues = {
  username: "",
  full_name: "",
  email: "",
  is_admin: false,
  password: "",
  confirm_password: "",
};

type UserFormValues = typeof baseInitialValues;

const baseSchemaFields = {
  email: Yup.string().email("Must be a valid email address").required("Email is required"),
  full_name: Yup.string(),
  is_admin: Yup.boolean(),
  username: Yup.string()
    .max(150, "Username must be 150 characters or less")
    .matches(/^[a-zA-Z0-9@.+-_]*$/, "Usernames must contain letters, digits and @/./+/-/_ only")
    .required("Username is required"),
};

const fullSchemaFields = {
  ...baseSchemaFields,
  password: Yup.string()
    .min(8, "Password must be at least 8 characters.")
    .max(100, "Password must be 100 characters or less"),
  confirm_password: Yup.string().oneOf(
    [Yup.ref("password")],
    "New passwords do not match. Please ensure the new passwords are the same.",
  ),
};

const NoPasswordUserSchema = Yup.object().shape(baseSchemaFields);

const EditUserSchema = Yup.object().shape(fullSchemaFields);

const AddUserSchema = Yup.object().shape({
  ...fullSchemaFields,
  password: fullSchemaFields.password.required("Password is required"),
  confirm_password: fullSchemaFields.confirm_password.required("Password is required"),
});

const UserForm = ({ type }: { type: "add" | "edit" }) => {
  const headingId = useId();
  const usernameId = useId();
  const fullNameId = useId();
  const emailId = useId();
  const passwordId = useId();
  const confirmPasswordId = useId();

  const [initialValues, setInitialValues] = useState<UserFormValues>(baseInitialValues);

  const { selected: selectedUserId, setSelected: setSelectedUserId } = useUserSelectionContext();
  const { setSidebar } = useAppLayoutContext();
  const { data: user, error, isPending } = useUser({ path: { id: selectedUserId! } }, type === "edit");

  const resetForm = () => {
    setSidebar(null);
    setSelectedUserId(null);
    setInitialValues(baseInitialValues);
  };

  const updateUser = useEditUser();
  const addUser = useAddUser();

  const isMutationPending = addUser.isPending || updateUser.isPending;

  useEffect(() => {
    if (type === "edit" && user) {
      setInitialValues({
        username: user.username,
        full_name: user.full_name ? user.full_name : "",
        email: user.email,
        is_admin: user.is_admin,
        password: "",
        confirm_password: "",
      });
    }
  }, [type, user]);

  const handleSubmit = async (values: UserFormValues) => {
    const userData = {
      email: values.email,
      username: values.username,
      is_admin: values.is_admin,
      full_name: values.full_name,
    };
    if (type === "edit") {
      if (!values.password) {
        await NoPasswordUserSchema.validate(values);
        updateUser.mutate({ path: { id: user!.id }, body: { ...userData } }, { onSuccess: resetForm });
      } else {
        await AddUserSchema.validate(values);
        updateUser.mutate(
          {
            path: { id: user!.id },
            body: { ...userData, password: values.password, confirm_password: values.confirm_password },
          },
          { onSuccess: resetForm },
        );
      }
    } else {
      addUser.mutate({ body: { ...values } }, { onSuccess: resetForm });
    }
  };

  return (
    <ContentSection>
      <ContentSection.Title id={headingId}>
        {type === "add" ? "Add user" : `Edit ${user ? user.username : ""}`}
      </ContentSection.Title>
      <ContentSection.Content>
        {error ? (
          <Notification severity="negative" title="Error while fetching user">
            <ErrorMessage error={error} />
          </Notification>
        ) : null}
        {updateUser.isError && (
          <Notification severity="negative" title="Error while editing user">
            <ErrorMessage error={updateUser.error} />
          </Notification>
        )}
        {addUser.isError && (
          <Notification severity="negative" title="Error while adding user">
            <ErrorMessage error={addUser.error} />
          </Notification>
        )}
        {type === "edit" && (isEqual(initialValues, baseInitialValues) || isPending) ? (
          <Spinner text="Loading..." />
        ) : (
          <Formik
            initialValues={initialValues}
            onSubmit={handleSubmit}
            validationSchema={type === "add" ? AddUserSchema : EditUserSchema}
          >
            {({ isSubmitting, errors, touched, isValid, dirty, values }) => (
              <FormikFormContent
                aria-labelledby={headingId}
                errors={
                  [
                    { body: addUser.error?.response?.data },
                    { body: updateUser.error?.response?.data },
                  ] as MutationErrorResponse[]
                }
              >
                <h4 className="p-heading--5">Personal details</h4>
                <Label className="is-required" htmlFor={usernameId}>
                  Username
                </Label>
                <Field
                  as={Input}
                  error={touched.username && errors.username}
                  id={usernameId}
                  name="username"
                  required
                  type="text"
                />
                <Label htmlFor={fullNameId}>Full name (optional)</Label>
                <Field
                  as={Input}
                  error={touched.full_name && errors.full_name}
                  id={fullNameId}
                  name="full_name"
                  type="text"
                />
                <Label className="is-required" htmlFor={emailId}>
                  Email address
                </Label>
                <Field
                  as={Input}
                  error={touched.email && errors.email}
                  id={emailId}
                  name="email"
                  required
                  type="email"
                />
                <Field
                  as={Input}
                  error={touched.is_admin && errors.is_admin}
                  label="MAAS Site Manager administrator"
                  name="is_admin"
                  type="checkbox"
                />
                <hr />
                <h4 className="p-heading--5">{type === "edit" ? "Change " : null}Password</h4>
                <Label className={type === "add" ? "is-required" : null} htmlFor={passwordId}>
                  Password
                </Label>
                <Field
                  as={Input}
                  error={touched.password && errors.password}
                  id={passwordId}
                  name="password"
                  required={type === "add"}
                  type="password"
                />
                <Label className={type === "add" ? "is-required" : null} htmlFor={confirmPasswordId}>
                  Password (again)
                </Label>
                <Field
                  as={Input}
                  error={errors.confirm_password}
                  id={confirmPasswordId}
                  name="confirm_password"
                  required={type === "add" || values.password !== ""}
                  type="password"
                />
                <p className="u-text--muted">Enter the same password as before, for verification</p>

                <hr />
                <div className="u-flex u-flex--justify-end u-padding-top--medium">
                  <Button appearance="base" onClick={resetForm} type="button">
                    Cancel
                  </Button>
                  <ActionButton
                    appearance="positive"
                    disabled={!dirty || !isValid || isSubmitting || isMutationPending}
                    loading={isSubmitting || isMutationPending}
                    type="submit"
                  >
                    {type === "add" ? "Add user" : "Save"}
                  </ActionButton>
                </div>
              </FormikFormContent>
            )}
          </Formik>
        )}
      </ContentSection.Content>
    </ContentSection>
  );
};

export default UserForm;
