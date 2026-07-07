import { ExternalLink, useSidePanel } from "@canonical/maas-react-components";
import { Accordion, ActionButton, Button, Input, Label, Spinner, Notification } from "@canonical/react-components";
import type { FormikErrors, FormikHelpers } from "formik";
import { Field, Form, Formik, useFormikContext } from "formik";
import { mapValues } from "lodash";
import * as Yup from "yup";

import { useEditSite, useSites } from "@/app/api/query/sites";
import type { Site } from "@/app/apiclient";
import ErrorMessage from "@/app/base/components/ErrorMessage/ErrorMessage";
import { coordinateSchema } from "@/app/sites/components/EditSite/constants";
import type { CoordinatesFormValue } from "@/app/sites/components/EditSite/types";
import { parseCoordinatesFormValue } from "@/app/sites/components/EditSite/utils";

import "./_SitesMissingData.scss";

type SitesMissingDataValues = {
  sitesCoordinates: Record<
    Site["id"],
    {
      coordinates: CoordinatesFormValue;
    }
  >;
};

const SitesMissingDataSchema = Yup.object().shape({
  sitesCoordinates: Yup.lazy((object) =>
    // since we don't know site IDs in advance, we use yup.lazy and lodash.mapValues to
    // create the schema *after* the sites are received
    Yup.object(mapValues(object, () => Yup.object().shape({ coordinates: coordinateSchema }))),
  ),
});

const SiteMissingDataField = ({ site }: { site: Site }) => {
  const fieldId = useId();
  const { touched, errors } = useFormikContext<SitesMissingDataValues>();

  const fieldErrors = errors.sitesCoordinates?.[site.id] as FormikErrors<
    SitesMissingDataValues["sitesCoordinates"][number]
  >;

  return (
    <span>
      <hr />
      <Accordion
        sections={[
          {
            content: (
              <>
                <Label>Latitude and Longitude</Label>
                <Field
                  as={Input}
                  error={touched.sitesCoordinates?.[site.id]?.coordinates && fieldErrors?.coordinates}
                  help="Coordinates need to be a comma-separated pair."
                  id={fieldId}
                  name={`sitesCoordinates[${site.id}].coordinates`}
                  type="text"
                />
              </>
            ),
            title: (
              <>
                <span>
                  {site.name}
                  <br />
                  {site.url && (
                    <ExternalLink className="sites-missing-data__link" to={site.url}>
                      {site.url}
                    </ExternalLink>
                  )}
                </span>
              </>
            ),
          },
        ]}
      />
    </span>
  );
};

const SitesMissingData = () => {
  const headingId = useId();
  const { closeSidePanel } = useSidePanel();
  const { data, error, isPending } = useSites({ query: { coordinates: false, page: 1, size: 20 } });
  const sites = data?.items;

  // Store formik helpers in a ref, since we can't access formik context here, and storing them in state
  // would trigger re-renders, while the hook uses an out of date `null` value.
  const formikHelpers = useRef<FormikHelpers<SitesMissingDataValues> | null>(null);
  const updateSite = useEditSite();

  useEffect(() => {
    // Close the side panel if there's no more sites with missing data
    if (!isPending && !error && sites && sites.length === 0) {
      closeSidePanel();
    }
  }, [sites, isPending, error, closeSidePanel]);

  const handleSubmit = async (values: SitesMissingDataValues, helpers: FormikHelpers<SitesMissingDataValues>) => {
    const { sitesCoordinates } = values;
    formikHelpers.current = helpers;

    // Cast id to number since Formik converts it to string
    const keys = Object.keys(sitesCoordinates).map((id) => Number(id));
    const filteredValues = keys.reduce((acc: { id: number; coordinates: CoordinatesFormValue }[], id) => {
      // Only submit fields that have coordinates
      if (sitesCoordinates[id].coordinates) {
        acc.push({ id, coordinates: sitesCoordinates[id].coordinates });
      }
      return acc;
    }, []);

    const toSubmit = filteredValues.map(({ id, coordinates }) => ({
      id,
      coordinates: parseCoordinatesFormValue(coordinates),
    }));

    toSubmit.forEach((site) => {
      updateSite.mutate(
        { path: { id: site.id }, body: { coordinates: site.coordinates } },
        {
          onError: (error, variables) => {
            const errorMessage = error.response?.data.error.details?.[0].messages[0];
            if (formikHelpers.current) {
              formikHelpers.current.setFieldError(`sitesCoordinates[${variables.path.id}].coordinates`, errorMessage);
            }
          },
        },
      );
    });

    // Need to call this manually, otherwise Formik gets stuck in a submitting state
    // and the Submit button will always be disabled
    helpers.setSubmitting(false);
  };

  if (isPending) {
    return <Spinner text="Loading..." />;
  }

  if (error) {
    return (
      <Notification severity="negative" title="Error while fetching sites">
        <ErrorMessage error={error} />
      </Notification>
    );
  }

  if (!sites) {
    return null;
  }

  const initialValues: SitesMissingDataValues = {
    sitesCoordinates: sites.reduce((acc, site) => Object.assign(acc, { [site.id]: { coordinates: "" } }), {}),
  };

  return (
    <div className="sites-missing-data">
      <h3 className="p-heading--4 u-no-margin" id={headingId}>
        Sites with missing data
      </h3>
      <p>
        The following sites have missing latitude and longitude data and are therefore not shown on the map. Add
        latitude and longitude data to the sites in order for them to show up on the map.
        <br />
        {/* TODO: Enable the link below once we have filtering on the sites list https://warthogs.atlassian.net/browse/MAASENG-3442 */}
        {/* <Link to="/sites/list?missing_coordinates=true">Show missing MAAS sites in table view</Link> */}
      </p>
      {!!updateSite.error && (
        <Notification severity="negative" title="Error while updating sites">
          <ErrorMessage error={updateSite.error} />
        </Notification>
      )}
      <strong className="u-uppercase p-text--small">
        Name
        <br />
        URL
      </strong>
      <Formik initialValues={initialValues} onSubmit={handleSubmit} validationSchema={SitesMissingDataSchema}>
        {({ dirty, isValid, isSubmitting, resetForm }) => (
          <Form aria-labelledby={headingId}>
            {sites.map((site) => (
              <SiteMissingDataField key={site.id} site={site} />
            ))}
            <div className="sites-missing-data__form-buttons-wrapper">
              <hr />
              <div className="sites-missing-data__form-buttons">
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
                  disabled={!dirty || !isValid || isSubmitting}
                  loading={isSubmitting}
                  type="submit"
                >
                  Save
                </ActionButton>
              </div>
            </div>
          </Form>
        )}
      </Formik>
    </div>
  );
};

export default SitesMissingData;
