import { ContentSection } from "@canonical/maas-react-components";
import { ActionButton, Button, Input, Label, Notification, Spinner } from "@canonical/react-components";
import { Field, Formik } from "formik";
import * as Yup from "yup";

import type { MutationErrorResponse } from "@/app/api";
import { useImageSource, useUpdateImageSource } from "@/app/api/query/imageSources";
import type { PatchBootSourceV1BootassetSourcesIdPatchData } from "@/app/apiclient";
import ErrorMessage from "@/app/base/components/ErrorMessage";
import FormikFormContent from "@/app/base/components/FormikFormContent";
import { useAppLayoutContext } from "@/app/context";
import { useBootSourceContext } from "@/app/context/BootSourceContext";

const baseInitialValues = {
  priority: 1,
};

type CustomImagesSourceFormValues = typeof baseInitialValues;

const CustomImagesSourceSchema = Yup.object().shape({
  priority: Yup.number().required("Priority is required"),
});

const EditCustomImagesSourceForm = () => {
  const [initialValues, setInitialValues] = useState<CustomImagesSourceFormValues>(baseInitialValues);
  const { selected: selectedBootSourceId, setSelected } = useBootSourceContext();
  const { setSidebar } = useAppLayoutContext();

  const updateImageSource = useUpdateImageSource();
  const { data: imageSource, error, isPending } = useImageSource({ path: { id: selectedBootSourceId! } });

  const headingId = useId();
  const priorityFieldId = useId();

  const resetForm = () => {
    setInitialValues(baseInitialValues);
    setSelected(null);
    setSidebar(null);
  };

  useEffect(() => {
    if (imageSource) {
      setInitialValues({
        priority: imageSource.priority,
      });
    }
  }, [imageSource]);

  const handleSubmit = (values: CustomImagesSourceFormValues) => {
    const body: PatchBootSourceV1BootassetSourcesIdPatchData["body"] = {
      priority: values.priority,
    };
    updateImageSource.mutate(
      {
        path: { id: selectedBootSourceId! },
        body,
      } as PatchBootSourceV1BootassetSourcesIdPatchData,
      { onSuccess: resetForm },
    );
  };

  return (
    <ContentSection>
      <ContentSection.Title id={headingId}>Edit Custom images</ContentSection.Title>
      <ContentSection.Content>
        {error ? (
          <Notification severity="negative" title="Error while fetching image source">
            <ErrorMessage error={error} />
          </Notification>
        ) : null}
        {updateImageSource.isError && (
          <Notification severity="negative" title="Error while editing image source">
            <ErrorMessage error={updateImageSource.error} />
          </Notification>
        )}
        {isPending || !imageSource ? (
          <Spinner text="Loading..." />
        ) : (
          <Formik
            enableReinitialize={true}
            initialValues={initialValues}
            onSubmit={handleSubmit}
            validationSchema={CustomImagesSourceSchema}
          >
            {({ errors, isSubmitting, touched, dirty, isValid }) => (
              <FormikFormContent
                aria-labelledby={headingId}
                errors={[{ body: updateImageSource.error?.response?.data }] as MutationErrorResponse[]}
              >
                <Label className="is-required" htmlFor={priorityFieldId}>
                  Priority
                </Label>
                <Field
                  as={Input}
                  error={touched.priority && errors.priority}
                  help="If the same image is available from several sources, the image from the source with the higher priority takes precedence. 1 is the highest priority."
                  id={priorityFieldId}
                  name="priority"
                  required
                  type="text"
                />
                <hr />
                <div className="u-flex u-flex--justify-end u-padding-top--medium">
                  <Button appearance="base" onClick={resetForm} type="button">
                    Cancel
                  </Button>
                  <ActionButton
                    appearance="positive"
                    disabled={!dirty || !isValid || isSubmitting}
                    loading={isSubmitting}
                    type="submit"
                  >
                    Save
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

export default EditCustomImagesSourceForm;
