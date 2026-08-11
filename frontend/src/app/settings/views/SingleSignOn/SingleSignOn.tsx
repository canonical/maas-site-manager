import { useState } from "react";

import { ContentSection } from "@canonical/maas-react-components";
import { ActionButton, Input, Notification, Select, Spinner } from "@canonical/react-components";
import type { AxiosError } from "axios";
import { Field, Formik } from "formik";
import * as Yup from "yup";

import type { MutationErrorResponse } from "@/app/api";
import { useActiveOauthProvider, useCreateOauthProvider, useUpdateOauthProvider } from "@/app/api/query/auth";
import type { OidcProviderResponse } from "@/app/apiclient";
import { OidcProviderAccessTokenType } from "@/app/apiclient";
import ErrorMessage from "@/app/base/components/ErrorMessage/ErrorMessage";
import FormikFormContent from "@/app/base/components/FormikFormContent";

export type SingleSignOnFormValues = {
  name: string;
  client_id: string;
  client_secret: string;
  issuer_url: string;
  redirect_uri: string;
  scopes: string;
  token_type: OidcProviderAccessTokenType;
};

const DEFAULT_REDIRECT_URI = `${window.location.origin}/api/v1/external-auth/callback`;

// Yup's built-in `.url()` matcher rejects hostnames without a dot (e.g.
// `http://localhost`), but the backend accepts them (pydantic `AnyHttpUrl`).
const isHttpUrl = (value?: string): boolean => {
  if (!value) {
    return true;
  }
  try {
    const { protocol } = new URL(value);
    return protocol === "http:" || protocol === "https:";
  } catch {
    return false;
  }
};

const getInitialValues = (provider?: OidcProviderResponse): SingleSignOnFormValues => ({
  name: provider?.name ?? "",
  client_id: provider?.client_id ?? "",
  client_secret: provider?.client_secret ?? "",
  issuer_url: provider?.issuer_url ?? "",
  redirect_uri: provider?.redirect_uri ?? DEFAULT_REDIRECT_URI,
  scopes: provider?.scopes ?? "openid profile email",
  token_type: provider?.token_type ?? OidcProviderAccessTokenType.JWT,
});

const SingleSignOnSchema = Yup.object().shape({
  name: Yup.string().required("Name is a required field."),
  client_id: Yup.string().required("Client ID is a required field."),
  client_secret: Yup.string().required("Client secret is a required field."),
  issuer_url: Yup.string()
    .test("is-http-url", "Must be a valid URL.", isHttpUrl)
    .required("Issuer URL is a required field."),
  redirect_uri: Yup.string()
    .test("is-http-url", "Must be a valid URL.", isHttpUrl)
    .required("Redirect URI is a required field."),
  scopes: Yup.string().required("Scopes is a required field."),
  token_type: Yup.mixed<OidcProviderAccessTokenType>()
    .oneOf(Object.values(OidcProviderAccessTokenType))
    .required("Token type is a required field."),
});

const SingleSignOn = () => {
  const [success, setSuccess] = useState(false);
  const { data: provider, error, isPending } = useActiveOauthProvider();
  const createProvider = useCreateOauthProvider();
  const updateProvider = useUpdateOauthProvider();

  // A 404 means no provider has been configured yet
  const fetchStatus = (error as AxiosError | null)?.response?.status;
  const isMissingProvider = fetchStatus === 404;

  const handleSubmit = (values: SingleSignOnFormValues) => {
    setSuccess(false);
    const body = { ...values, enabled: true };
    if (provider) {
      updateProvider.mutate(
        { path: { id: provider.id }, body },
        {
          onSuccess: () => {
            setSuccess(true);
          },
        },
      );
    } else {
      createProvider.mutate(
        { body },
        {
          onSuccess: () => {
            setSuccess(true);
          },
        },
      );
    }
  };

  if (isPending) {
    return <Spinner text="Loading..." />;
  }

  if (error && !isMissingProvider) {
    return (
      <Notification severity="negative" title="Error while fetching OIDC provider">
        <ErrorMessage error={error} />
      </Notification>
    );
  }

  const mutationErrors = [
    { body: createProvider.error?.response?.data },
    { body: updateProvider.error?.response?.data },
  ] as MutationErrorResponse[];

  return (
    <ContentSection variant="narrow">
      <ContentSection.Title>OIDC/Single sign-on</ContentSection.Title>
      <ContentSection.Content>
        <Notification severity="information" title="Single sign-on">
          Configure an OpenID Connect (OIDC) provider to enable single sign-on for MAAS Site Manager.
        </Notification>
        <Formik
          initialValues={getInitialValues(provider)}
          onSubmit={handleSubmit}
          validationSchema={SingleSignOnSchema}
        >
          {({ isSubmitting, errors, touched, isValid, dirty }) => (
            <FormikFormContent
              aria-label="Single sign-on form"
              errors={mutationErrors}
              onChange={() => {
                setSuccess(false);
              }}
            >
              <Field
                as={Input}
                error={touched.name && errors.name}
                help="A unique, human-readable name identifying the OIDC provider."
                label="Name"
                name="name"
                required
                type="text"
              />
              <Field
                as={Input}
                error={touched.client_id && errors.client_id}
                help="The client ID issued by the OIDC provider to identify your application."
                label="Client ID"
                name="client_id"
                required
                type="text"
              />
              <Field
                as={Input}
                error={touched.client_secret && errors.client_secret}
                help="The client secret issued by the OIDC provider, used to authenticate your application securely."
                label="Client secret"
                name="client_secret"
                required
                type="password"
              />
              <Field
                as={Input}
                error={touched.issuer_url && errors.issuer_url}
                help="The base URL of the OIDC provider's authorization server."
                label="Issuer URL"
                name="issuer_url"
                required
                type="text"
              />
              <Field
                as={Input}
                error={touched.redirect_uri && errors.redirect_uri}
                help="The redirect URI where the OIDC provider will redirect users after successful authentication."
                label="Redirect URI"
                name="redirect_uri"
                required
                type="text"
              />
              <Field
                as={Input}
                error={touched.scopes && errors.scopes}
                help="A space-separated list of OIDC scopes defining the information requested from the provider."
                label="Scopes"
                name="scopes"
                required
                type="text"
              />
              <Field
                as={Select}
                error={touched.token_type && errors.token_type}
                help="The type of access tokens issued by the OIDC provider. Encrypted JWT tokens should be treated as opaque."
                label="Token type"
                name="token_type"
                options={[
                  { label: "JWT", value: OidcProviderAccessTokenType.JWT },
                  { label: "Opaque", value: OidcProviderAccessTokenType.OPAQUE },
                ]}
                required
              />
              <ContentSection.Footer>
                <ActionButton
                  appearance="positive"
                  disabled={!dirty || !isValid || isSubmitting}
                  loading={isSubmitting || createProvider.isPending || updateProvider.isPending}
                  success={success}
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

export default SingleSignOn;
