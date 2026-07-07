import { ContentSection, FileUpload, useSidePanel } from "@canonical/maas-react-components";
import type { SelectProps } from "@canonical/react-components";
import { ActionButton, Button, Input, Label, Notification, Select } from "@canonical/react-components";
import classNames from "classnames";
import type { FormikHelpers } from "formik";
import { Field, Formik } from "formik";
import * as Yup from "yup";

import { ARCHITECTURES, OPERATING_SYSTEM_NAMES, VALID_IMAGE_FILE_TYPES } from "./constants";

import type { MutationErrorResponse } from "@/app/api";
import { useUploadCustomImage } from "@/app/api/query/images";
import ErrorMessage from "@/app/base/components/ErrorMessage";
import FormikFormContent from "@/app/base/components/FormikFormContent";
import "./_UploadCustomImage.scss";

type UploadImageFormValues = {
  title: string;
  release: string;
  os: string;
  arch: string;
  file: File | null;
};

const isValidFileType = (fileName: string) => {
  if (fileName) {
    const extension = fileName.split(".").pop();
    if (!extension) {
      return false;
    } else {
      return VALID_IMAGE_FILE_TYPES.includes(extension);
    }
  } else {
    return false;
  }
};

const osOptions: SelectProps["options"] = [
  {
    label: "Select an operating system",
    value: "",
    disabled: true,
  },
  ...OPERATING_SYSTEM_NAMES,
];

const archOptions: SelectProps["options"] = [
  {
    label: "Select an architecture",
    value: "",
    disabled: true,
  },
  ...ARCHITECTURES,
];

const UploadImageSchema: Yup.Schema = Yup.object().shape({
  title: Yup.string().required("Release title is required."),
  release: Yup.string().required("Release is required."),
  os: Yup.string().required("OS is required."),
  arch: Yup.string().required("Architecture is required."),
  file: Yup.mixed((input): input is File => input instanceof File)
    .required("Image file is required.")
    .test("is-valid-type", "File type is invalid.", (image) => isValidFileType(image && image.name.toLowerCase())),
});

const UploadCustomImage = () => {
  const { closeSidePanel } = useSidePanel();
  const [uploadProgress, setUploadProgress] = useState(0);
  const uploadImageMutation = useUploadCustomImage({
    onUploadProgress: (progressEvent) => {
      const { loaded, total } = progressEvent;
      if (loaded && total) {
        setUploadProgress(Math.round((loaded * 100) / total));
      }
    },
  });
  const releaseTitleHeadingId = useId();
  const releaseHeadingId = useId();
  const osHeadingId = useId();
  const archHeadingId = useId();

  const initialValues: UploadImageFormValues = {
    title: "",
    release: "",
    os: "",
    arch: "",
    file: null,
  };

  const handleSubmit = (values: UploadImageFormValues, helpers: FormikHelpers<UploadImageFormValues>) => {
    if (values.file) {
      uploadImageMutation.mutate(
        {
          body: {
            os: values.os,
            title: values.title,
            release: values.release,
            arch: values.arch,
            file: values.file,
            filename: values.file.name,
            file_size: values.file.size,
          },
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
        {
          onSuccess: () => {
            closeSidePanel();
          },
        },
      );
    }
    helpers.setSubmitting(false);
  };
  return (
    <ContentSection>
      <ContentSection.Title>Upload custom image</ContentSection.Title>
      <ContentSection.Content>
        {uploadImageMutation.isError && (
          <Notification severity="negative" title="Error while uploading image">
            <ErrorMessage error={uploadImageMutation.error} />
          </Notification>
        )}
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
            <FormikFormContent
              className="upload-image-form"
              errors={[{ body: uploadImageMutation.error?.response?.data }] as MutationErrorResponse[]}
            >
              <Label className="is-required" id={osHeadingId}>
                Operating system
              </Label>
              <Field
                aria-labelledby={osHeadingId}
                as={Select}
                error={touched.os && errors.os}
                help="The operating system the custom image is based on."
                name="os"
                options={osOptions}
                required
              />
              <Label className="is-required" id={releaseTitleHeadingId}>
                Release title
              </Label>
              <Field
                aria-labelledby={releaseTitleHeadingId}
                as={Input}
                error={touched.title && errors.title}
                help="The release title that will be shown in the images table, e.g. 24.04 LTS."
                name="title"
                required
                type="text"
              />
              <Label className="is-required" id={releaseHeadingId}>
                Release codename
              </Label>
              <Field
                aria-labelledby={releaseHeadingId}
                as={Input}
                error={touched.release && errors.release}
                help="The codename for the release, e.g. 'noble'."
                name="release"
                required
                type="text"
              />
              <Label className="is-required" id={archHeadingId}>
                Architecture
              </Label>
              <Field
                aria-labelledby={archHeadingId}
                as={Select}
                error={touched.arch && errors.arch}
                name="arch"
                options={archOptions}
                required
              />
              <div
                className={classNames("p-form__group p-form-validation", { "is-error": touched.file && errors.file })}
              >
                <Label className="is-required">Upload image</Label>
                <p className="p-form-help-text">
                  Supported file types are tgz, tbz, txz, ddtgz, ddtbz, ddtxz, ddtar, ddbz2, ddgz, ddxz and ddraw.
                </p>
                <div className="p-form__control">
                  <div className="u-padding-bottom--medium">
                    <Field
                      as={FileUpload}
                      error={touched.file && errors.file}
                      files={
                        values.file
                          ? [
                              {
                                name: values.file.name,
                                percentUploaded: uploadImageMutation.isPending ? uploadProgress : undefined,
                              },
                            ]
                          : []
                      }
                      name="file"
                      onFileUpload={(files: File[]) => {
                        setFieldTouched("file", true);
                        if (files.length > 1) {
                          setFieldError("file", "Only one image can be uploaded at a time.");
                        } else {
                          setFieldValue("file", files[0]);
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
                    closeSidePanel();
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
            </FormikFormContent>
          )}
        </Formik>
      </ContentSection.Content>
    </ContentSection>
  );
};

export default UploadCustomImage;
