import { useMemo } from "react";

import type { Options } from "@hey-api/client-axios";
import type { UseQueryOptions, UseQueryResult } from "@tanstack/react-query";
import { useQueries, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";

import type {
  PostV1TokensPostResponse,
  GetV1TokensGetData,
  GetV1TokensGetError,
  GetV1TokensGetResponse,
  PostV1TokensPostData,
  PostV1TokensPostError,
  DeleteManyV1TokensDeleteData,
  DeleteManyV1TokensDeleteResponse,
  DeleteManyV1TokensDeleteError,
  GetExportV1TokensExportGetData,
  GetExportV1TokensExportGetResponses,
  GetExportV1TokensExportGetErrors,
} from "@/app/apiclient";
import {
  deleteManyV1TokensDeleteMutation,
  getExportV1TokensExportGetOptions,
  getV1TokensGetOptions,
  getV1TokensGetQueryKey,
  postV1TokensPostMutation,
} from "@/app/apiclient/@tanstack/react-query.gen";

const maxPageSize = 100;

export const useTokens = (options?: Options<GetV1TokensGetData>) => {
  return useQuery(
    getV1TokensGetOptions(options) as UseQueryOptions<GetV1TokensGetData, GetV1TokensGetError, GetV1TokensGetResponse>,
  );
};

export const useTokenCount = (options?: Options<GetV1TokensGetData>, enabled = true) => {
  return useQuery({
    ...getV1TokensGetOptions(options),
    select: (data) => data.total ?? 0,
    enabled,
  } as UseQueryOptions<GetV1TokensGetResponse, GetV1TokensGetError, number>);
};

export const useCreateTokens = (mutationOptions?: Options<PostV1TokensPostData>) => {
  const queryClient = useQueryClient();

  return useMutation<PostV1TokensPostResponse, AxiosError<PostV1TokensPostError>, Options<PostV1TokensPostData>>({
    ...postV1TokensPostMutation(mutationOptions),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: getV1TokensGetQueryKey() });
    },
  });
};

const useExportTokensByIds = (
  options?: Options<GetExportV1TokensExportGetData>,
): UseQueryResult | UseQueryResult<GetExportV1TokensExportGetResponses, GetExportV1TokensExportGetErrors> => {
  return useQuery({
    ...getExportV1TokensExportGetOptions({
      ...options,
      query: {
        page: 1,
        size: maxPageSize,
        id: options?.query?.id,
      },
    }),
    enabled: !!options?.query?.id?.length,
  });
};

const combineExportPages = (results: UseQueryResult[]) => ({
  responses: results.map((result) => result.data).filter((data): data is string => !!data),
  isLoading: results.some((result) => result.isLoading),
  isError: results.some((result) => result.isError),
  error: results.find((result) => result.error)?.error,
});

const useExportAllTokens = (options?: Options<GetExportV1TokensExportGetData>) => {
  const { data: totalTokens } = useTokenCount(options, !options?.query?.id?.length);

  const pagesToLoad = useMemo(() => {
    if (!totalTokens || !!options?.query?.id?.length) return 0;
    return Math.ceil(totalTokens / maxPageSize);
  }, [totalTokens, options?.query?.id]);

  return useQueries({
    queries: useMemo(
      () =>
        Array.from({ length: pagesToLoad }, (_, i) => ({
          ...getExportV1TokensExportGetOptions({
            query: { page: i + 1, size: maxPageSize },
          }),
          enabled: !options?.query?.id?.length && !!totalTokens,
        })),
      [pagesToLoad, options?.query?.id, totalTokens],
    ),
    combine: combineExportPages,
  });
};

export const useExportTokens = (options?: Options<GetExportV1TokensExportGetData>) => {
  const idBasedExport = useExportTokensByIds(options);
  const allPages = useExportAllTokens(options);

  const combinedData = useMemo(() => {
    if (options?.query?.id?.length) {
      return idBasedExport.data;
    }

    const { responses } = allPages;
    if (allPages.isLoading || !responses.length) return null;

    const newLines = /\r\n|\r|\n/g;
    const header = responses[0].split(newLines)[0];
    const pages = responses
      .map((response) => {
        const lines = response.split(newLines);
        lines.shift();
        return lines.join("\n");
      })
      .join("");

    return [header, pages].join("\n");
  }, [idBasedExport.data, allPages, options?.query?.id]);

  return {
    data: combinedData,
    isLoading: options?.query?.id?.length ? idBasedExport.isLoading : allPages.isLoading,
    isError: options?.query?.id?.length ? idBasedExport.isError : allPages.isError,
    error: options?.query?.id?.length ? idBasedExport.error : allPages.error,
  };
};

export const useDeleteTokens = (mutationOptions?: Options<DeleteManyV1TokensDeleteData>) => {
  const queryClient = useQueryClient();

  return useMutation<
    DeleteManyV1TokensDeleteResponse,
    AxiosError<DeleteManyV1TokensDeleteError>,
    Options<DeleteManyV1TokensDeleteData>
  >({
    ...deleteManyV1TokensDeleteMutation(mutationOptions),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: getV1TokensGetQueryKey() });
    },
  });
};
