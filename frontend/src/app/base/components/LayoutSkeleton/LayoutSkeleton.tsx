import type { ComponentProps, FC } from "react";

import { ContentSection, GenericTable, Placeholder } from "@canonical/maas-react-components";

type LayoutSkeletonComponent = FC & {
  TableView: FC;
  SettingsView: FC;
};

type LayoutSkeletonTableColumns = ComponentProps<typeof GenericTable>["columns"];

const tableColumns: LayoutSkeletonTableColumns = [
  {
    accessorKey: "name",
    header: () => <Placeholder variant="block" width="8ch" />,
    meta: {
      skeleton: () => (
        <div>
          <Placeholder variant="block" width="18ch" />
          <Placeholder variant="block" width="24ch" />
        </div>
      ),
    },
  },
  {
    accessorKey: "details",
    header: () => <Placeholder variant="block" width="12ch" />,
    meta: {
      skeleton: () => (
        <div>
          <Placeholder variant="block" width="18ch" />
          <Placeholder variant="block" width="14ch" />
        </div>
      ),
    },
  },
  {
    accessorKey: "status",
    header: () => <Placeholder variant="block" width="10ch" />,
    meta: {
      skeleton: () => <Placeholder variant="block" width="12ch" />,
    },
  },
  {
    accessorKey: "updated",
    header: () => <Placeholder variant="block" width="16ch" />,
    meta: {
      skeleton: () => <Placeholder variant="block" width="10ch" />,
    },
  },
  {
    accessorKey: "actions",
    header: () => <Placeholder variant="block" width="10ch" />,
    meta: {
      skeleton: () => (
        <div>
          <Placeholder variant="block" width="2ch" />
          <Placeholder variant="block" width="2ch" />
        </div>
      ),
    },
  },
];

const TableView: FC = () => (
  <ContentSection aria-hidden="true" className="layout-skeleton">
    <ContentSection.Header>
      {/* Replaces the page title and primary header actions. */}
      <div className="layout-skeleton__header">
        <Placeholder height="2rem" variant="block" width="24ch" />
        <Placeholder height="2rem" variant="block" width="100%" />
        <Placeholder height="2rem" variant="block" width="18ch" />
        <Placeholder height="2rem" variant="block" width="18ch" />
      </div>
    </ContentSection.Header>
    <ContentSection.Content>
      {/* Replaces pagination. */}
      <div className="layout-skeleton__pagination">
        <Placeholder height="2rem" variant="block" width="24ch" />
        <div className="layout-skeleton__pagination-controls">
          <Placeholder height="2rem" variant="block" width="16ch" />
          <Placeholder height="2rem" variant="block" width="16ch" />
        </div>
      </div>
      {/* Replaces the main table region using GenericTable's built-in skeleton rows. */}
      <GenericTable
        className="layout-skeleton__table"
        columns={tableColumns}
        data={[]}
        isLoading
        loadingVariant="skeleton"
      />
    </ContentSection.Content>
  </ContentSection>
);

const SettingsView: FC = () => (
  <ContentSection aria-hidden="true" className="layout-skeleton" variant="narrow">
    {/* Replaces the settings page title. */}
    <ContentSection.Title>
      <Placeholder height="2rem" variant="block" width="16ch" />
    </ContentSection.Title>
    {/* Replaces the stacked form fields in narrow settings/account views. */}
    <div className="layout-skeleton__form">
      {Array.from({ length: 3 }).map((_, index) => (
        <div className="layout-skeleton__form-field" key={`layout-skeleton-field-${index}`}>
          <Placeholder height="1.5rem" variant="block" width="14ch" />
          <Placeholder height="2rem" variant="block" width="100%" />
        </div>
      ))}
    </div>
    {/* Replaces the settings form footer actions. */}
    <ContentSection.Footer>
      <Placeholder height="2rem" variant="block" width="8ch" />
    </ContentSection.Footer>
  </ContentSection>
);

const LayoutSkeleton = Object.assign(() => <TableView />, {
  TableView,
  SettingsView,
}) as LayoutSkeletonComponent;

export { TableView, SettingsView };

export default LayoutSkeleton;
