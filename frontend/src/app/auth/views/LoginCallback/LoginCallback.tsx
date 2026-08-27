import { useEffect, useRef } from "react";

import { Col, Notification, Row, Spinner, Strip } from "@canonical/react-components";

import { useGetCallback } from "@/app/api/query/auth";
import { useAuthContext } from "@/app/context";
import { Link, useLocation, useNavigate } from "@/utils/router";

export const Labels = {
  MissingParams: "Missing code or state in the callback URL.",
  CallbackError: "An error occurred during authentication.",
  AlreadyAuthenticated: "You are already authenticated. Redirecting...",
};

const LoginCallback = (): React.ReactElement => {
  const location = useLocation();
  const navigate = useNavigate();
  const { status } = useAuthContext();
  const authenticated = status === "authenticated";

  const params = new URLSearchParams(location.search);
  const code = params.get("code");
  const state = params.get("state");
  const error = params.get("error");
  const errorDescription = params.get("error_description");
  const hasParams = Boolean(code && state);
  const hasError = Boolean(error || errorDescription);

  const callback = useGetCallback(
    {
      query: {
        code: code ?? "",
        state: state ?? "",
      },
    },
    hasParams && !authenticated,
  );

  const hasHandledSuccess = useRef(false);
  const shouldShowMissingParamsError = !authenticated && !hasParams && !callback.isError && !hasError;

  useEffect(() => {
    // Redirect users who are already authenticated on arrival. Skip once we've
    // handled a successful callback so the backend's redirect_target wins.
    if (authenticated && !hasHandledSuccess.current) {
      navigate("/sites", { replace: true });
    }
  }, [authenticated, navigate]);

  useEffect(() => {
    if (!callback.isSuccess || hasHandledSuccess.current) return;

    hasHandledSuccess.current = true;

    navigate(callback.data.redirect_target, { replace: true });
  }, [callback.isSuccess, callback.data, navigate]);

  return (
    <Strip>
      <Row>
        <Col emptyLarge={4} size={6}>
          {hasError && (
            <Notification role="alert" severity="negative">
              {error && `Error: ${error}. `}
              <br />
              {errorDescription}
              <br />
              Please try <Link to="/login">logging in</Link> again.
            </Notification>
          )}
          {shouldShowMissingParamsError && (
            <Notification role="alert" severity="information">
              {Labels.MissingParams}
            </Notification>
          )}
          {code && state && !hasError && callback.isPending && <Spinner aria-label="Loading..." text="Loading..." />}
          {callback.isError && (
            <Notification role="alert" severity="negative">
              {Labels.CallbackError}
              <br />
              Please try <Link to="/login">logging in</Link> again.
            </Notification>
          )}
          {authenticated && (
            <Notification role="alert" severity="positive">
              {Labels.AlreadyAuthenticated}
            </Notification>
          )}
        </Col>
      </Row>
    </Strip>
  );
};

export default LoginCallback;
