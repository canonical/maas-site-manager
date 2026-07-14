import { ContentSection, ExternalLink, MainToolbar, useSidePanel } from "@canonical/maas-react-components";
import { Button, Notification } from "@canonical/react-components";
import pluralize from "pluralize";

import TokensTable from "./components/TokensTable/TokensTable";

import { useDeleteTokens, useExportTokens } from "@/app/api/query/tokens";
import ErrorMessage from "@/app/base/components/ErrorMessage";
import RemoveButton from "@/app/base/components/RemoveButton";
import docsUrls from "@/app/base/docsUrls";
import usePagination from "@/app/base/hooks/usePagination";
import { lazySidePanel } from "@/app/base/sidePanel";
import { useRowSelection } from "@/app/context";
import { saveToFile } from "@/utils";

const DEFAULT_PAGE_SIZE = 50;

const TokensCreate = lazySidePanel(() => import("@/app/settings/views/Tokens/components/TokensCreate"));

const TokensList = () => {
  const { openSidePanel } = useSidePanel();
  const { page, debouncedPage, size, handlePageSizeChange, setPage } = usePagination(DEFAULT_PAGE_SIZE);
  const { rowSelection, setRowSelection, clearRowSelection } = useRowSelection("tokens", {
    currentPage: page,
    pageSize: size,
  });

  const selectedTokenCount = useMemo(() => Object.keys(rowSelection).length, [rowSelection]);

  const {
    data: exportTokensData,
    error: exportTokensError,
    isLoading: isLoadingExportTokens,
  } = useExportTokens({ query: { id: Object.keys(rowSelection).map((id) => Number(id)) } });

  const exportTokens = async () => {
    if (exportTokensData) {
      saveToFile(exportTokensData as BlobPart, "site-manager-tokens.csv", "text/csv");
    }
  };

  const tokensDeleteMutation = useDeleteTokens();

  const handleTokenDelete = () => {
    const selectedIds = Object.keys(rowSelection).map((id) => Number(id));
    tokensDeleteMutation.mutate({ query: { ids: selectedIds } }, { onSuccess: clearRowSelection });
  };

  const deletedTokensCount = tokensDeleteMutation.variables?.query.ids.length;

  return (
    <ContentSection>
      {tokensDeleteMutation.isSuccess && deletedTokensCount ? (
        <Notification severity="information" title="Deleted">
          {`${deletedTokensCount === 1 ? "An" : ""} ${pluralize(
            "enrollment token",
            deletedTokensCount,
            deletedTokensCount > 1,
          )} ${deletedTokensCount === 1 ? "was" : "were"} deleted.`}
        </Notification>
      ) : null}
      {exportTokensError ? (
        <Notification severity="negative" title="Error">
          <ErrorMessage error={exportTokensError} />
        </Notification>
      ) : null}
      {tokensDeleteMutation.isError ? (
        <Notification severity="negative" title="Error">
          <ErrorMessage
            defaultMessage="An error occured while deleting the tokens"
            error={tokensDeleteMutation.error}
          />
        </Notification>
      ) : null}
      <ContentSection.Header className="tokens-list-header">
        <p className="tokens-list-instructions">
          Follow the enrollment steps outlined in the{" "}
          {/* TODO: Update link once documentation is live https://warthogs.atlassian.net/browse/MAASENG-1585 */}
          <ExternalLink to={docsUrls.enrollmentRequest}>documentation</ExternalLink> to enroll new sites. Once an
          enrollment request was made use the following certificate data to compare against the certificate shown in the
          enrollment request:
        </p>
        {/* TODO: Add actual certificate here once endpoint is ready https://warthogs.atlassian.net/browse/MAASENG-1584 */}
        <code className="tokens-list-certificate">
          <span>CN:</span>
          <span>sitemanager.example.com</span>
          <span>Expiration date:</span>
          <span>Thu, 29 Jul. 2035</span>
          <span>Fingerprint:</span>
          <span>15cf96e8bad3eea3ef3c10badcd88f66fe236e0de99027451120bc7cd69c0012</span>
          <span>Issued by:</span>
          <span>Let's Encrypt</span>
        </code>
        <MainToolbar>
          <MainToolbar.Controls>
            <RemoveButton disabled={!selectedTokenCount} label="Delete" onClick={handleTokenDelete} />
            <Button disabled={isLoadingExportTokens} onClick={exportTokens}>
              {`Export ${selectedTokenCount ? `${selectedTokenCount} ${pluralize("token", selectedTokenCount)}` : "all tokens"}`}
            </Button>
            <Button
              className="p-button--positive"
              onClick={() => {
                openSidePanel({ component: TokensCreate, title: "Generate tokens" });
              }}
              type="button"
            >
              Generate tokens
            </Button>
          </MainToolbar.Controls>
        </MainToolbar>
      </ContentSection.Header>
      <TokensTable
        debouncedPage={debouncedPage}
        handlePageSizeChange={handlePageSizeChange}
        page={page}
        rowSelection={rowSelection}
        setPage={setPage}
        setRowSelection={setRowSelection}
        size={size}
      />
    </ContentSection>
  );
};

export default TokensList;
