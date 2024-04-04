import { ContentSection, FileUpload } from "@canonical/maas-react-components";
import type { SelectProps } from "@canonical/react-components";
import { ActionButton, Button, Input, Label, Select } from "@canonical/react-components";
import classNames from "classnames";
import { Field, Form, Formik } from "formik";
import * as Yup from "yup";

import { ARCHITECTURES, OPERATING_SYSTEM_NAMES, VALID_IMAGE_FILE_TYPES } from "./constants";

import type { UploadImagePayload } from "@/api/handlers";
import { useAppLayoutContext } from "@/context";
import { useUploadImageMutation } from "@/hooks/react-query";

type UploadImageFormValues = Yup.InferType<typeof UploadImageSchema>;

const isValidFileType = (fileName: string) => {
  if (fileName) {
    const extension = fileName.split(".").pop();
    if (!extension) {
      return false;
    } else {
      return VALID_IMAGE_FILE_TYPES.indexOf(extension) > -1;
    }
  } else {
    return false;
  }
};

const releaseOptions: SelectProps["options"] = [
  {
    label: "Select a release",
    value: "",
    disabled: true,
  },
  ...OPERATING_SYSTEM_NAMES,
];

const baseImageOptions: SelectProps["options"] = [
  {
    label: "Select a base image",
    value: "",
    disabled: true,
  },
  ...OPERATING_SYSTEM_NAMES,
];

const architectureOptions: SelectProps["options"] = [
  {
    label: "Select an architecture",
    value: "",
    disabled: true,
  },
  ...ARCHITECTURES,
];

const UploadImageSchema: Yup.Schema = Yup.object().shape({
  title: Yup.string().required("Release title is required."),
  imageId: Yup.string()
    .matches(/^[a-z0-9-_]*$/, "Image ID can only contain letters, digits, hyphens and underscores.")
    .required("Image ID is required."),
  release: Yup.string().required("Release is required."),
  baseImage: Yup.string(),
  architecture: Yup.string().required("Architecture is required."),
  image: Yup.mixed((input): input is File => input instanceof File)
    .required("Image file is required.")
    .test("is-valid-type", "File type is invalid.", (image) => isValidFileType(image && image.name.toLowerCase())),
});

const UploadImage = () => {
  const { setSidebar } = useAppLayoutContext();
  const uploadImageMutation = useUploadImageMutation({ onSuccess: () => setSidebar(null) });
  const releaseTitleHeadingId = useId();
  const imageIdHeadingId = useId();
  const releaseHeadingId = useId();
  const baseImageHeadingId = useId();
  const architectureHeadingId = useId();

  const initialValues: UploadImageFormValues = {
    title: "",
    imageId: "",
    release: "",
    baseImage: "",
    architecture: "",
    image: null,
  };

  const handleSubmit = (values: UploadImageFormValues) => {
    if (values.image) {
      uploadImageMutation.mutate(values as UploadImagePayload);
    }
  };

  return (
    <ContentSection>
      <ContentSection.Title>Upload image</ContentSection.Title>
      <ContentSection.Content>
        <Formik initialValues={initialValues} onSubmit={handleSubmit} validationSchema={UploadImageSchema}>
          {({
            isSubmitting,
            errors,
            touched,
            isValid,
            dirty,
            values,
            setFieldValue,
            resetForm,
            setFieldTouched,
            setFieldError,
          }) => (
            <Form className="upload-image-form">
              <Label id={releaseTitleHeadingId}>Release title</Label>
              <Field
                aria-labelledby={releaseTitleHeadingId}
                as={Input}
                error={touched.title && errors.title}
                help="The release title that will be shown in the images table."
                name="title"
                required
                type="text"
              />
              <Label id={imageIdHeadingId}>Image ID</Label>
              <Field
                aria-labelledby={imageIdHeadingId}
                as={Input}
                error={touched.imageId && errors.imageId}
                help="A unique image ID. Can only contain letters, numbers, underscores or hyphens."
                name="imageId"
                required
                type="text"
              />
              <Label id={releaseHeadingId}>Release</Label>
              <Field
                aria-labelledby={releaseHeadingId}
                as={Select}
                error={touched.release && errors.release}
                name="release"
                options={releaseOptions}
                required
              />
              {values.release === "Custom" ? (
                <>
                  <Label id={baseImageHeadingId}>Base image</Label>
                  <Field
                    aria-labelledby={baseImageHeadingId}
                    as={Select}
                    error={touched.baseImage && errors.baseImage}
                    help="The base image the custom image is based on."
                    name="baseImage"
                    options={baseImageOptions}
                    required
                  />
                </>
              ) : null}
              <Label id={architectureHeadingId}>Architecture</Label>
              <Field
                aria-labelledby={architectureHeadingId}
                as={Select}
                error={touched.architecture && errors.architecture}
                name="architecture"
                options={architectureOptions}
                required
              />
              <div
                className={classNames("p-form__group p-form-validation", { "is-error": touched.image && errors.image })}
              >
                <Label className="is-required">Upload image</Label>
                <p className="p-form-help-text">
                  Supported file types are tgz, tbz, txz, ddtgz, ddtbz, ddtxz, ddtar, ddbz2, ddgz, ddxz and ddraw.
                </p>
                <div className="p-form__control">
                  <div className="u-padding-bottom--medium">
                    <Field
                      as={FileUpload}
                      error={touched.image && errors.image}
                      name="image"
                      onFileUpload={(files: File[]) => {
                        setFieldTouched("image", true);
                        if (files.length > 1) {
                          setFieldError("image", "Only one image can be uploaded at a time.");
                        } else {
                          setFieldValue("image", files[0]);
                        }
                      }}
                      required
                    />
                  </div>
                </div>
              </div>
              <ContentSection.Footer>
                <Button
                  appearance="base"
                  onClick={() => {
                    resetForm();
                    setSidebar(null);
                  }}
                  type="button"
                >
                  Cancel
                </Button>
                <ActionButton
                  appearance="positive"
                  disabled={!dirty || isSubmitting || !isValid || uploadImageMutation.isPending}
                  loading={isSubmitting || uploadImageMutation.isPending}
                  type="submit"
                >
                  Save
                </ActionButton>
              </ContentSection.Footer>
            </Form>
          )}
        </Formik>
      </ContentSection.Content>
    </ContentSection>
  );
};

export default UploadImage;
