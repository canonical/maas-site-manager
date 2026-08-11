import type { Options } from "@hey-api/client-axios";
import type { UseQueryOptions } from "@tanstack/react-query";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";

import type {
  CreateV1ExternalAuthPostData,
  CreateV1ExternalAuthPostError,
  CreateV1ExternalAuthPostResponse,
  GetActiveProviderV1ExternalAuthGetData,
  GetActiveProviderV1ExternalAuthGetError,
  GetActiveProviderV1ExternalAuthGetResponse,
  PostV1LoginPostData,
  UpdateV1ExternalAuthIdPatchData,
  UpdateV1ExternalAuthIdPatchError,
  UpdateV1ExternalAuthIdPatchResponse,
} from "@/app/apiclient";
import {
  createV1ExternalAuthPostMutation,
  getActiveProviderV1ExternalAuthGetOptions,
  getActiveProviderV1ExternalAuthGetQueryKey,
  postV1LoginPostMutation,
  updateV1ExternalAuthIdPatchMutation,
} from "@/app/apiclient/@tanstack/react-query.gen";

export const useLogin = (mutationOptions?: Options<PostV1LoginPostData>) => {
  return useMutation({
    ...postV1LoginPostMutation(mutationOptions),
  });
};

export const useActiveOauthProvider = (options?: Options<GetActiveProviderV1ExternalAuthGetData>) => {
  return useQuery({
    ...(getActiveProviderV1ExternalAuthGetOptions(options) as UseQueryOptions<
      GetActiveProviderV1ExternalAuthGetData,
      GetActiveProviderV1ExternalAuthGetError,
      GetActiveProviderV1ExternalAuthGetResponse
    >),
    retry: false, // Don't retry as the backend returns 404 when no provider is configured
  });
};

export const useCreateOauthProvider = (mutationOptions?: Options<CreateV1ExternalAuthPostData>) => {
  const queryClient = useQueryClient();

  return useMutation<
    CreateV1ExternalAuthPostResponse,
    AxiosError<CreateV1ExternalAuthPostError>,
    Options<CreateV1ExternalAuthPostData>
  >({
    ...createV1ExternalAuthPostMutation(mutationOptions),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: getActiveProviderV1ExternalAuthGetQueryKey() });
    },
  });
};

export const useUpdateOauthProvider = (mutationOptions?: Options<UpdateV1ExternalAuthIdPatchData>) => {
  const queryClient = useQueryClient();

  return useMutation<
    UpdateV1ExternalAuthIdPatchResponse,
    AxiosError<UpdateV1ExternalAuthIdPatchError>,
    Options<UpdateV1ExternalAuthIdPatchData>
  >({
    ...updateV1ExternalAuthIdPatchMutation(mutationOptions),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: getActiveProviderV1ExternalAuthGetQueryKey() });
    },
  });
};
