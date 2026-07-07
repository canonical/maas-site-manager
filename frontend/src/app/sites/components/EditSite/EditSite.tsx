import { useId } from "react";

import { useSidePanel } from "@canonical/maas-react-components";
import { ActionButton, Button, Input, Label, Notification, Select, Spinner } from "@canonical/react-components";
import { Field, Formik } from "formik";
import en from "i18n-iso-countries/langs/en.json";
import * as Yup from "yup";

import { coordinateSchema } from "./constants";
import type { CoordinatesFormValue } from "./types";
import { parseCoordinatesFormValue } from "./utils";

import type { MutationErrorResponse } from "@/app/api";
import { useEditSite, useSite } from "@/app/api/query/sites";
import type { Site } from "@/app/apiclient";
import ErrorMessage from "@/app/base/components/ErrorMessage/ErrorMessage";
import FormikFormContent from "@/app/base/components/FormikFormContent";
import type { ReturnablePanelProps } from "@/app/base/sidePanel";
import type { SiteDetailsContextValue } from "@/app/context/SiteDetailsContext";
import { useSiteDetailsContext } from "@/app/context/SiteDetailsContext";
import { getCountryName } from "@/utils";

const countryOptions = [
  { value: "", label: "Select country...", disabled: true },
  ...Object.keys(en.countries).map((countryCode) => ({
    value: countryCode,
    label: getCountryName(countryCode),
  })),
] as const;

type EditSiteFormValues = Record<"coordinates", CoordinatesFormValue> &
  Record<keyof Pick<Site, "address" | "city" | "country" | "postal_code" | "state">, string>;

const baseInitialValues: EditSiteFormValues = {
  country: "",
  state: "",
  address: "",
  city: "",
  postal_code: "",
  coordinates: "",
};

const EditSiteSchema = Yup.object().shape({
  state: Yup.string(),
  address: Yup.string(),
  city: Yup.string(),
  postal_code: Yup.string(),
  coordinates: coordinateSchema,
});

type SiteFormValues = typeof baseInitialValues;

const EditSiteContent = ({
  siteId,
  setSiteId,
  onClose,
}: {
  siteId: NonNullable<SiteDetailsContextValue["selected"]>;
  setSiteId: NonNullable<SiteDetailsContextValue["setSelected"]>;
  onClose?: () => void;
}) => {
  const headingId = useId();
  const countryId = useId();
  const stateId = useId();
  const addressId = useId();
  const postalCodeId = useId();
  const cityId = useId();
  const coordinatesId = useId();

  const [initialValues, setInitialValues] = useState<SiteFormValues>(baseInitialValues);
  const { closeSidePanel } = useSidePanel();
  const { data: site, error, isPending } = useSite({ path: { id: siteId } });

  const updateSite = useEditSite();

  useEffect(() => {
    if (site) {
      setInitialValues({
        address: site.address ?? "",
        city: site.city ?? "",
        state: site.state ?? "",
        country: site.country ?? "",
        postal_code: site.postal_code ?? "",
        coordinates: site.coordinates ? `${site.coordinates?.latitude}, ${site.coordinates?.longitude}` : "",
      });
    }
  }, [site]);

  const handleSubmit = async (values: SiteFormValues) => {
    const coordinates = parseCoordinatesFormValue(values.coordinates);
    const { address, city, postal_code, state, country } = values;
    const requestBody = {
      name: site!.name,
      url: site!.url,
      address,
      city,
      postal_code,
      state,
      country,
      coordinates,
    };
    updateSite.mutate({ path: { id: siteId }, body: requestBody }, { onSuccess: resetForm });
  };

  const resetForm = () => {
    setInitialValues(baseInitialValues);
    if (onClose) {
      onClose();
    } else {
      setSiteId(null);
      closeSidePanel();
    }
  };

  return (
    <div>
      {!isPending && site && initialValues !== baseInitialValues ? (
        <>
          <h3 className="p-heading--4 u-no-margin" id={headingId}>
            Edit <strong>{site.name}</strong>
          </h3>
          <p>Data not shown in this form is reported by the MAAS site and can't be edited in Site Manager.</p>
          {updateSite.isError ? (
            <Notification severity="negative" title="Error while updating site">
              {updateSite.error.response?.data.error.message || "An unknown error occurred."}
            </Notification>
          ) : null}
          <Formik initialValues={initialValues} onSubmit={handleSubmit} validationSchema={EditSiteSchema}>
            {({ isSubmitting, errors, touched, isValid, dirty }) => (
              <FormikFormContent
                aria-labelledby={headingId}
                errors={[{ body: updateSite.error?.response?.data } as MutationErrorResponse]}
                noValidate
              >
                <h4 className="p-heading--5">Geolocation data</h4>
                <Label htmlFor={countryId}>Country/Region</Label>
                <Field
                  as={Select}
                  error={touched.country && errors.country}
                  id={countryId}
                  name="country"
                  options={countryOptions}
                />
                <Label htmlFor={stateId}>Administrative region</Label>
                <Field
                  as={Input}
                  error={touched.state && errors.state}
                  help={<small className="u-text--muted">e.g. state, province etc.</small>}
                  id={stateId}
                  name="state"
                  type="text"
                />
                <Label htmlFor={cityId}>City</Label>
                <Field as={Input} error={touched.city && errors.city} id={cityId} name="city" type="text" />
                <Label htmlFor={addressId}>Address</Label>
                <Field as={Input} error={touched.address && errors.address} id={addressId} name="address" type="text" />
                <Label htmlFor={postalCodeId}>Postal code</Label>
                <Field
                  as={Input}
                  error={touched.postal_code && errors.postal_code}
                  id={postalCodeId}
                  name="postal_code"
                  type="text"
                />
                <Label htmlFor={coordinatesId}>Latitude and Longitude</Label>
                <Field
                  as={Input}
                  error={touched.coordinates && errors.coordinates}
                  help={<small className="u-text--muted">Coordinates need to be a comma-separated pair.</small>}
                  id={coordinatesId}
                  name="coordinates"
                  type="text"
                />
                {/* TODO: Add timezone input field https://warthogs.atlassian.net/browse/MAASENG-2018 */}
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
        </>
      ) : error ? (
        <Notification severity="negative" title="Error while fetching site">
          <ErrorMessage error={error} />
        </Notification>
      ) : (
        <Spinner text="Loading..." />
      )}
    </div>
  );
};

const EditSite = ({ onClose }: ReturnablePanelProps) => {
  const { selected: siteId, setSelected: setSiteId } = useSiteDetailsContext();

  return siteId ? <EditSiteContent onClose={onClose} setSiteId={setSiteId} siteId={siteId} /> : null;
};

export default EditSite;
