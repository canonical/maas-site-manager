import { Button, Tooltip } from "@canonical/react-components";
import classNames from "classnames";

type Props = {
  className?: string;
  hasBorder?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  onExpand?: () => void;
  editTooltip?: string;
  deleteTooltip?: string;
  editDisabled?: boolean;
  deleteDisabled?: boolean;
  isDense?: boolean;
  editLabel?: string;
  deleteLabel?: string;
};

const TableActions = ({
  className,
  hasBorder,
  editTooltip,
  deleteTooltip,
  onEdit,
  onDelete,
  onExpand,
  editDisabled,
  deleteDisabled,
  isDense = true,
  editLabel = "Edit",
  deleteLabel = "Delete",
}: Props) => {
  return (
    <div className={classNames("table-actions u-flex", { "table-actions-bordered": hasBorder }, className)}>
      {onEdit && (
        <Tooltip message={editTooltip} position="left">
          <Button
            appearance="base"
            aria-label={editLabel}
            className={classNames("is-dense table-actions-btn", { "u-table-cell-padding-overlap": isDense })}
            disabled={editDisabled}
            hasIcon
            onClick={onEdit}
            type="button"
          >
            <i className="p-icon--edit">Edit</i>
          </Button>
        </Tooltip>
      )}
      {onExpand ? (
        <Button appearance="base" onClick={onExpand} type="button">
          expand
        </Button>
      ) : (
        <>
          {onEdit && onDelete ? <span className="table-actions-vertical-divider"></span> : null}
          {onDelete && (
            <Tooltip message={deleteTooltip} position="left">
              <Button
                appearance="base"
                aria-label={deleteLabel}
                className={classNames("is-dense table-actions-btn", { "u-table-cell-padding-overlap": isDense })}
                disabled={deleteDisabled}
                hasIcon
                onClick={onDelete}
                type="button"
              >
                <i className="p-icon--delete">Delete</i>
              </Button>
            </Tooltip>
          )}
        </>
      )}
    </div>
  );
};

export default TableActions;
