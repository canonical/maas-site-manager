import { http, HttpResponse } from "msw";

import { ExceptionCode } from "@/app/apiclient";
import type {
  CreateV1ExternalAuthPostError,
  GetActiveProviderV1ExternalAuthGetError,
  OidcProviderResponse,
  UpdateV1ExternalAuthIdPatchError,
} from "@/app/apiclient";
import { oidcProviderFactory } from "@/mocks/factories";
import { apiUrls } from "@/utils/test-urls";

const mockProvider = oidcProviderFactory.build();

const mockGetProviderNotFoundError: GetActiveProviderV1ExternalAuthGetError = {
  error: {
    code: ExceptionCode.MISSING_RESOURCE,
    message: "No active OIDC provider has been configured",
  },
};

const mockCreateProviderError: CreateV1ExternalAuthPostError = {
  error: {
    code: ExceptionCode.NOT_AUTHENTICATED,
    message: "You must be authenticated to configure an OIDC provider",
  },
};

const mockUpdateProviderError: UpdateV1ExternalAuthIdPatchError = {
  error: {
    code: ExceptionCode.MISSING_PERMISSIONS,
    message: "You do not have permission to update this OIDC provider",
  },
};

const oidcResolvers = {
  getActiveProvider: {
    resolved: false,
    handler: (data: OidcProviderResponse = mockProvider) => {
      return http.get(apiUrls.externalAuth, () => {
        oidcResolvers.getActiveProvider.resolved = true;
        return HttpResponse.json(data);
      });
    },
    notFound: (error: GetActiveProviderV1ExternalAuthGetError = mockGetProviderNotFoundError) => {
      return http.get(apiUrls.externalAuth, () => {
        oidcResolvers.getActiveProvider.resolved = true;
        return HttpResponse.json(error, { status: 404 });
      });
    },
    error: (error: GetActiveProviderV1ExternalAuthGetError = mockGetProviderNotFoundError) => {
      return http.get(apiUrls.externalAuth, () => {
        oidcResolvers.getActiveProvider.resolved = true;
        return HttpResponse.json(error, { status: 500 });
      });
    },
  },
  createProvider: {
    resolved: false,
    handler: (data: OidcProviderResponse = mockProvider) => {
      return http.post(apiUrls.externalAuth, async ({ request }) => {
        const body = (await request.json()) as Partial<OidcProviderResponse>;
        oidcResolvers.createProvider.resolved = true;
        return HttpResponse.json({ ...data, ...body });
      });
    },
    error: (error: CreateV1ExternalAuthPostError = mockCreateProviderError) => {
      return http.post(apiUrls.externalAuth, () => {
        oidcResolvers.createProvider.resolved = true;
        return HttpResponse.json(error, { status: 401 });
      });
    },
  },
  updateProvider: {
    resolved: false,
    handler: (data: OidcProviderResponse = mockProvider) => {
      return http.patch(`${apiUrls.externalAuth}/:id`, async ({ request }) => {
        const body = (await request.json()) as Partial<OidcProviderResponse>;
        oidcResolvers.updateProvider.resolved = true;
        return HttpResponse.json({ ...data, ...body });
      });
    },
    error: (error: UpdateV1ExternalAuthIdPatchError = mockUpdateProviderError) => {
      return http.patch(`${apiUrls.externalAuth}/:id`, () => {
        oidcResolvers.updateProvider.resolved = true;
        return HttpResponse.json(error, { status: 403 });
      });
    },
  },
};

export { oidcResolvers };
