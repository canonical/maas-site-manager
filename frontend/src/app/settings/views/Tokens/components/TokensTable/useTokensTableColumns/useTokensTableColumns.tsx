import { useCallback, useState } from "react";

import type { ColumnDef } from "@tanstack/react-table";

import type { Token } from "@/app/apiclient";
import CopyButton from "@/app/base/components/CopyButton";
import TooltipButton from "@/app/base/components/TooltipButton";
import { copyToClipboard, createAccessor, formatDistanceToNow, formatUTCDateString } from "@/utils";

type TokenColumnDef = ColumnDef<Token, Partial<Token>>;

export const useTokensTableColumns = () => {
  const [copiedText, setCopiedText] = useState("");
  const isTokenCopied = useCallback((token: string) => token === copiedText, [copiedText]);

  const resetCopiedText = (timeout = 500) => {
    setTimeout(() => {
      setCopiedText("");
    }, timeout);
  };

  const handleTokenCopy = useCallback((token: string) => {
    copyToClipboard(token, setCopiedText);
    resetCopiedText();
  }, []);

  return useMemo<TokenColumnDef[]>(
    () => [
      {
        id: "token",
        accessorFn: createAccessor("value"),
        enableSorting: false,
        header: "Token",
        cell: ({ getValue }) => {
          const { value } = getValue();
          return (
            <div
              className="token-cell"
              onClick={() => {
                handleTokenCopy(value!);
              }}
            >
              <span className="token-text">{value}</span>
              <CopyButton isCopied={isTokenCopied(value!)} value={value || ""} />
            </div>
          );
        },
      },
      {
        id: "expirationTime",
        accessorFn: createAccessor("expired"),
        enableSorting: false,
        header: "Time until expiration",
        cell: ({ getValue }) => {
          const { expired } = getValue();
          return (
            <TooltipButton message={expired ? `${formatUTCDateString(expired)} (UTC)` : null} position="btm-center">
              {expired ? formatDistanceToNow(expired) : null}
            </TooltipButton>
          );
        },
      },
      {
        id: "created",
        accessorFn: createAccessor("created"),
        enableSorting: false,
        header: "Created (UTC)",
        cell: ({ getValue }) => {
          const { created } = getValue();
          return <div>{created ? formatUTCDateString(created) : null}</div>;
        },
      },
    ],
    [handleTokenCopy, isTokenCopied],
  );
};
