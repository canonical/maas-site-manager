import { useEffect, useId } from "react";

import { useSidePanel } from "@canonical/maas-react-components";
import { Button, Icon, Input, Notification } from "@canonical/react-components";
import type { FormikHelpers } from "formik";
import { Field, Form, Formik } from "formik";
import pluralize from "pluralize";
import * as Yup from "yup";

import ErrorMessage from "../../../base/components/ErrorMessage";

import { useDeleteSites, useSite } from "@/app/api/query/sites";
import type { ReturnablePanelProps } from "@/app/base/sidePanel";
import { useRowSelection } from "@/app/context";

const initialValues = {
  confirmText: "",
};

type RemoveSitesFormValues = typeof initialValues;

const RemoveSitesFormSchema = Yup.object().shape({
  confirmText: Yup.string()
    .required()
    .when("$expectedConfirmTextValue", (type, schema) => {
      return schema.equals(type);
    }),
});

const createHandleValidate =
  ({ expectedConfirmTextValue }: { expectedConfirmTextValue: string }) =>
  async (values: RemoveSitesFormValues) => {
    let errors = {};
    await RemoveSitesFormSchema.validate(values, { context: { expectedConfirmTextValue } }).catch(() => {
      errors = { confirmText: `Confirmation string is not correct. Expected ${expectedConfirmTextValue}` };
    });
    return errors;
  };

const RemoveSites = ({ onClose }: ReturnablePanelProps) => {
  const { rowSelection, clearRowSelection } = useRowSelection("sites");
  const { closeSidePanel } = useSidePanel();
  const deleteSitesMutation = useDeleteSites();
  const sitesCount = rowSelection && Object.keys(rowSelection).length;
  const id = useId();
  const confirmTextId = `confirm-text-${id}`;
  const headingId = `heading-${id}`;
  const { data } = useSite({ path: { id: Number(Object.keys(rowSelection)?.[0]) } });
  const siteName = data?.name;
  const sitesCountText = sitesCount === 1 ? siteName : pluralize("sites", sitesCount || 0, !!sitesCount);
  const expectedConfirmTextValue = `remove ${sitesCountText}`;
  const handleSubmit = (_values: RemoveSitesFormValues, { setSubmitting }: FormikHelpers<RemoveSitesFormValues>) => {
    const selectedIds = Object.keys(rowSelection).map((id) => Number(id));
    deleteSitesMutation.mutate(
      { query: { ids: selectedIds } },
      {
        onSuccess() {
          setSubmitting(false);
          closeSidePanel();
          clearRowSelection();
        },
      },
    );
  };

  // close the sidebar when there are no sites selected
  useEffect(() => {
    if (!sitesCount) {
      closeSidePanel();
    }
  }, [sitesCount, closeSidePanel]);

  return (
    <Formik<RemoveSitesFormValues>
      initialValues={initialValues}
      onSubmit={handleSubmit}
      validate={createHandleValidate({ expectedConfirmTextValue })}
    >
      {({ isSubmitting, errors, touched, dirty, submitCount }) => (
        <Form aria-labelledby={headingId} className="tokens-create" noValidate>
          {deleteSitesMutation.isError && (
            <Notification severity="negative" title="Error while deleting sites">
              <ErrorMessage error={deleteSitesMutation.error} />
            </Notification>
          )}
          <div className="tokens-create">
            <h3 className="tokens-create__heading p-heading--4" id={headingId}>
              Remove <strong> {sitesCountText}</strong> from Site Manager
            </h3>
            <p>
              The deletion of data is irreversible. You can re-enroll the MAAS {pluralize("sites", sitesCount)} again
              through the enrollment process.
            </p>
            <p id={confirmTextId}>
              Type <strong>remove {sitesCountText}</strong> to confirm.
            </p>
            <Field
              aria-labelledby={confirmTextId}
              as={Input}
              error={submitCount > 0 && touched.confirmText && errors.confirmText}
              name="confirmText"
              placeholder={`remove ${sitesCountText}`}
              type="text"
            />
            <div className="u-flex u-flex--justify-end u-padding-top--medium">
              <Button
                appearance="base"
                onClick={() => {
                  if (onClose) {
                    onClose();
                  } else {
                    closeSidePanel();
                  }
                }}
                type="button"
              >
                Cancel
              </Button>
              <Button appearance="negative" disabled={!dirty || isSubmitting} type="submit">
                <Icon light name="delete" /> Remove
              </Button>
            </div>
          </div>
        </Form>
      )}
    </Formik>
  );
};

export default RemoveSites;
