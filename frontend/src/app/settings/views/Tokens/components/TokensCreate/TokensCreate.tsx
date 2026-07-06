import { useId } from "react";

import { Button, Input, Label, Notification } from "@canonical/react-components";
import type { FormikHelpers } from "formik";
import { Field, Formik } from "formik";
import pluralize from "pluralize";
import * as Yup from "yup";

import { humanIntervalToISODuration } from "./utils";

import type { MutationErrorResponse } from "@/app/api";
import { useCreateTokens } from "@/app/api/query/tokens";
import FormikFormContent from "@/app/base/components/FormikFormContent";
import { useAppLayoutContext } from "@/app/context";

const initialValues = {
  count: "",
  duration: "",
};

type TokensCreateFormValues = typeof initialValues;

const TokensCreateSchema = Yup.object().shape({
  count: Yup.number().positive().required("Please enter a valid number"),
  duration: Yup.string()
    .matches(
      /^((\d)+ ?(minute|hour|day|week|month|year)(s)? ?(and)? ?)+$/,
      "Time unit must be a `string` type with a value of weeks, days, hours, and/or minutes.",
    )
    .test("Please enter a valid time unit", function (value) {
      if (!value) {
        return false;
      }
      try {
        return !!humanIntervalToISODuration(value);
      } catch {
        return false;
      }
    })
    .required("Please enter a valid time unit"),
});

const TokensCreate = () => {
  const headingId = useId();
  const durationId = useId();
  const countId = useId();
  const tokensCreateMutation = useCreateTokens();
  const { setSidebar } = useAppLayoutContext();
  const handleSubmit = async (
    { count, duration }: TokensCreateFormValues,
    { setSubmitting }: FormikHelpers<TokensCreateFormValues>,
  ) => {
    await tokensCreateMutation.mutateAsync(
      {
        body: {
          count: Number(count),
          duration: humanIntervalToISODuration(duration) as string,
        },
      },
      {
        onSuccess: () => {
          setSidebar(null);
        },
      },
    );
    setSubmitting(false);
  };

  return (
    <div className="tokens-create">
      <h3 className="tokens-create__heading p-heading--4" id={headingId}>
        Generate new enrollment tokens
      </h3>
      {tokensCreateMutation.isError && (
        <Notification severity="negative">There was an error generating the token(s).</Notification>
      )}
      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validateOnBlur={false}
        validationSchema={TokensCreateSchema}
      >
        {({ isSubmitting, errors, touched, isValid, dirty, values }) => (
          <FormikFormContent
            aria-labelledby={headingId}
            className="tokens-create"
            errors={[{ body: tokensCreateMutation.error?.response?.data.error } as MutationErrorResponse]}
            noValidate
          >
            <Label htmlFor={countId}>Amount of tokens to generate</Label>
            <Field
              as={Input}
              error={touched.count && errors.count}
              id={countId}
              name="count"
              placeholder="1"
              required
              type="text"
            />
            <Label htmlFor={durationId}>Expiration time</Label>
            <Field
              as={Input}
              error={touched.duration && errors.duration}
              id={durationId}
              name="duration"
              placeholder="12 hours"
              required
              type="text"
            />
            <p className="u-text--muted">
              Use this token once to request an enrollment in the specified timeframe. Allowed time units are seconds,
              minutes, hours, days and weeks.
            </p>
            <hr className="tokens-create__separator" />
            <div className="tokens-create__buttons">
              <Button
                appearance="base"
                onClick={() => {
                  setSidebar(null);
                }}
                type="button"
              >
                Cancel
              </Button>
              <Button
                appearance="positive"
                disabled={!dirty || !isValid || tokensCreateMutation.isPending || isSubmitting}
                type="submit"
              >
                Generate {values.count !== "" ? values.count : "0"} {pluralize("token", parseInt(values.count))}
              </Button>
            </div>
          </FormikFormContent>
        )}
      </Formik>
    </div>
  );
};

export default TokensCreate;
