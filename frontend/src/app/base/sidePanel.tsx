/**
 * Props shared by side panels that can be opened on top of another panel (e.g.
 * the edit/remove site panels opened from the site details panel). When an
 * `onClose` callback is provided, the panel calls it instead of closing the
 * side panel outright, allowing the caller to restore the previous panel.
 *
 * The intersection with `Record<string, unknown>` keeps the type compatible
 * with `openSidePanel`'s `TProps extends Record<string, unknown>` constraint.
 */
export type ReturnablePanelProps = Record<string, unknown> & {
  onClose?: () => void;
};
