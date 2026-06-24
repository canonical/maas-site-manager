import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { ContextualMenu, Icon, CheckboxInput } from "@canonical/react-components";
import type { Column } from "@tanstack/react-table";

import type { Site } from "@/app/apiclient";

function ColumnsVisibilityControl({ columns }: { columns: Column<Site>[] }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredColumns = columns.filter(
    (column) =>
      column.id !== "p-generic-table__select" &&
      column.id !== "select" &&
      column.id !== "name" &&
      column.id !== "actions",
  );
  const hiddenColumns = filteredColumns.filter((column) => !column.getIsVisible());
  const selectedColumnsLength = filteredColumns.length - hiddenColumns.length;
  const someColumnsChecked = selectedColumnsLength > 0 && selectedColumnsLength < filteredColumns.length;

  const handleToggleAll = (isChecked: boolean) => {
    filteredColumns
      // If the "select all" checkbox is checked, find all hidden columns. Otherwise, find all visible columns
      .filter((column) => (isChecked ? !column.getIsVisible() : column.getIsVisible()))
      .forEach((column) => {
        column.toggleVisibility();
      });
  };

  useEffect(() => {
    if (isOpen) {
      const firstFocusable = dropdownRef.current?.querySelector<HTMLElement>(
        'input, button, [tabindex]:not([tabindex="-1"])',
      );
      firstFocusable?.focus();
    }
  }, [isOpen]);

  return (
    <ContextualMenu
      dropdownClassName="columns-visibility__dropdown"
      dropdownProps={{ "aria-label": "columns menu" }}
      onToggleMenu={setIsOpen}
      position="right"
      toggleAppearance="base"
      toggleClassName="columns-visibility-control is-dense"
      toggleLabel={<Icon name="settings">Columns</Icon>}
      toggleLabelFirst
    >
      <div className="columns-visibility-select-wrapper u-no-padding--top" ref={dropdownRef}>
        <div className="columns-visibility-checkbox">
          <CheckboxInput
            checked={hiddenColumns.length === 0}
            indeterminate={someColumnsChecked}
            label={`${selectedColumnsLength} out of ${filteredColumns.length} selected`}
            onChange={(e: ChangeEvent<HTMLInputElement>) => {
              handleToggleAll(e.target.checked);
            }}
          />
        </div>
      </div>
      <hr />
      <div className="columns-visibility-select-wrapper u-no-padding--top">
        {filteredColumns.map((column) => {
          return (
            <div className="columns-visibility-checkbox u-capitalize" key={column.id}>
              <CheckboxInput
                aria-label={column.id}
                label={column.id}
                {...{
                  checked: column.getIsVisible(),
                  onChange: column.getToggleVisibilityHandler(),
                }}
              />
            </div>
          );
        })}
      </div>
    </ContextualMenu>
  );
}

export default ColumnsVisibilityControl;
