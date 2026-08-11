import { useActiveOauthProvider, useCreateOauthProvider, useLogin, useUpdateOauthProvider } from "./auth";

import type { OidcProviderCreateRequest, OidcProviderUpdateRequest } from "@/app/apiclient";
import { oidcProviderFactory } from "@/mocks/factories";
import { authResolvers } from "@/testing/resolvers/auth";
import { oidcResolvers } from "@/testing/resolvers/oidc";
import { Providers, renderHook, setupServer, waitFor } from "@/utils/test-utils";

const mockProvider = oidcProviderFactory.build();
const mockServer = setupServer(
  authResolvers.login.handler(),
  oidcResolvers.getActiveProvider.handler(mockProvider),
  oidcResolvers.createProvider.handler(mockProvider),
  oidcResolvers.updateProvider.handler(mockProvider),
);

beforeAll(() => {
  mockServer.listen();
});

afterEach(() => {
  mockServer.resetHandlers();
});

afterAll(() => {
  mockServer.close();
});

describe("useLogin", () => {
  it("should return an access token when login is successful", async () => {
    const { result } = renderHook(() => useLogin(), { wrapper: Providers });
    const login = result.current.mutateAsync;
    const { access_token } = await login({ body: { username: "admin", password: "admin" } });
    await waitFor(() => {
      expect(access_token).toBeDefined();
    });
  });
});

describe("useActiveOauthProvider", () => {
  it("should return the active OIDC provider", async () => {
    const { result } = renderHook(() => useActiveOauthProvider(), { wrapper: Providers });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockProvider);
  });

  it("should return an error when no provider is configured", async () => {
    mockServer.use(oidcResolvers.getActiveProvider.notFound());

    const { result } = renderHook(() => useActiveOauthProvider(), { wrapper: Providers });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("useCreateOauthProvider", () => {
  it("should create an OIDC provider", async () => {
    const newProvider: OidcProviderCreateRequest = {
      name: "My provider",
      client_id: "client-id",
      client_secret: "client-secret",
      issuer_url: "https://issuer.example.com",
      redirect_uri: "http://localhost:3000/api/v1/external-auth/callback",
      scopes: "openid profile email",
      token_type: mockProvider.token_type,
      enabled: true,
    };

    const { result } = renderHook(() => useCreateOauthProvider(), { wrapper: Providers });
    result.current.mutate({ body: newProvider });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.name).toBe(newProvider.name);
  });
});

describe("useUpdateOauthProvider", () => {
  it("should update an OIDC provider", async () => {
    const updateData: OidcProviderUpdateRequest = {
      name: "Updated provider",
    };

    const { result } = renderHook(() => useUpdateOauthProvider(), { wrapper: Providers });
    result.current.mutate({ body: updateData, path: { id: mockProvider.id } });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.name).toBe(updateData.name);
  });
});
