import { ContentSection, useSidePanel } from "@canonical/maas-react-components";
import type { MultiSelectItem } from "@canonical/react-components";
import { ActionButton, Button, Spinner, Notification, Accordion, MultiSelect } from "@canonical/react-components";
import { Field, Form, Formik } from "formik";

import ErrorMessage from "../../../base/components/ErrorMessage";

import { useAddImagesToSelection, useSelectableImages } from "@/app/api/query/images";
import type { SelectableImage } from "@/app/apiclient";

import "./_AddToAvailableImages.scss";

type GroupedImages = Record<string, ReleasesWithArches>;

export type ReleasesWithArches = Record<string, MultiSelectItem[]>;

type ImagesByName = Record<string, SelectableImage[]>;

const groupImagesByName = (images: SelectableImage[]) => {
  if (!images) return {};
  const imagesByName: ImagesByName = {};

  images.forEach((image) => {
    if (!!imagesByName[image.os]) {
      imagesByName[image.os].push(image);
    } else {
      imagesByName[image.os] = [image];
    }
  });

  return imagesByName;
};

const groupArchesByRelease = (images: ImagesByName) => {
  const groupedImages: GroupedImages = {};

  Object.keys(images).forEach((os) => {
    if (!groupedImages[os]) {
      groupedImages[os] = {};
    }
    images[os].forEach((image) => {
      if (!groupedImages[os][image.release!]) {
        groupedImages[os][image.release!] = [{ label: image.arch, value: image.selection_id }];
      } else {
        groupedImages[os][image.release!].push({
          label: image.arch,
          value: image.selection_id,
        });
      }
    });
  });

  return groupedImages;
};

const getInitialState = (images: ImagesByName) => {
  const initialState: ReleasesWithArches = {};

  Object.keys(images).forEach((os) => {
    images[os].forEach((image) => {
      if (!initialState[getValueKey(os, image.release!)]) {
        initialState[getValueKey(os, image.release!)] = [];
      }
    });
  });

  return initialState;
};

const removeSpacesAndDots = (str: string) => str.replace(/\s+/g, "-").replace(/\./g, "-");

const getValueKey = (os: string, release: string) => removeSpacesAndDots(`${os}-${release}`);

const AddToAvailableImages = () => {
  const { data, isPending, isError, error } = useSelectableImages();

  const [images, setImages] = useState<ImagesByName>({});
  const [groupedImages, setGroupedImages] = useState<GroupedImages>({});
  const [initialValues, setInitialValues] = useState<ReleasesWithArches>({});

  const headingId = useId();

  useEffect(() => {
    if (data) {
      const imagesByName = groupImagesByName(data.items);
      setImages(imagesByName);
      setGroupedImages(groupArchesByRelease(imagesByName));
      setInitialValues(getInitialState(imagesByName));
    }
  }, [data]);

  const { closeSidePanel } = useSidePanel();

  const resetForm = () => {
    closeSidePanel();
    setInitialValues(images ? getInitialState(images) : {});
  };

  const addImagesToSelection = useAddImagesToSelection();

  const hasUpstreamImages = Object.keys(groupedImages).length > 0;

  return (
    <ContentSection className="add-to-available-images">
      <ContentSection.Header>
        <ContentSection.Title id={headingId}>Add upstream images to available images</ContentSection.Title>
        <p>
          Below you can select which images should be synced from upstream image sources. Selected images will be made
          available to connected MAAS sites.
        </p>
      </ContentSection.Header>
      <ContentSection.Content>
        {isPending ? (
          <Spinner text="Loading..." />
        ) : isError ? (
          <Notification severity="negative" title="Error while fetching upstream images">
            <ErrorMessage error={error} />
          </Notification>
        ) : groupedImages && data ? (
          <Formik
            enableReinitialize={true}
            initialValues={initialValues}
            onSubmit={(values, helpers) => {
              const selectionIds = Object.values(values)
                .flat()
                .map((item) => (typeof item.value === "string" ? Number.parseInt(item.value) : item.value));
              addImagesToSelection.mutate({
                body: {
                  selection_ids: selectionIds,
                },
              });
              helpers.setSubmitting(false);
              resetForm();
            }}
          >
            {({ isSubmitting, dirty, values, setFieldValue }) => (
              <Form aria-labelledby={headingId}>
                {addImagesToSelection.isError && (
                  <Notification severity="negative" title="Error while selecting images">
                    <ErrorMessage error={addImagesToSelection.error} />
                  </Notification>
                )}
                {hasUpstreamImages ? (
                  <Accordion
                    sections={Object.keys(groupedImages).map((os) => ({
                      title: os,
                      content: (
                        <span key={os}>
                          <table className="download-images__table">
                            <thead>
                              <tr>
                                <th>Release</th>
                                <th>Architecture</th>
                              </tr>
                            </thead>
                            <tbody>
                              {Object.keys(groupedImages[os]).map((release) => (
                                <tr aria-label={release} key={release}>
                                  <td>{release}</td>
                                  <td>
                                    <Field
                                      as={MultiSelect}
                                      items={groupedImages[os][release]}
                                      name={removeSpacesAndDots(`${os}-${release}`)}
                                      onItemsUpdate={(items: MultiSelectItem) =>
                                        setFieldValue(getValueKey(os, release), items)
                                      }
                                      placeholder="Select architectures"
                                      selectedItems={values[getValueKey(os, release)]}
                                      variant="condensed"
                                    />
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </span>
                      ),
                    }))}
                    titleElement="h4"
                  />
                ) : (
                  <p className="u-text--muted">
                    No selectable upstream images found. This might be because there are no upstream images, or all
                    upstream images are already selected.
                  </p>
                )}
                <ContentSection.Footer>
                  <Button appearance="base" onClick={resetForm} type="button">
                    Cancel
                  </Button>
                  <ActionButton
                    appearance="positive"
                    disabled={!dirty || isSubmitting || addImagesToSelection.isPending}
                    loading={isSubmitting || addImagesToSelection.isPending}
                    type="submit"
                  >
                    Save
                  </ActionButton>
                </ContentSection.Footer>
              </Form>
            )}
          </Formik>
        ) : null}
      </ContentSection.Content>
    </ContentSection>
  );
};

export default AddToAvailableImages;
