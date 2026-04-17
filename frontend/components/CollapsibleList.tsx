"use client";

import { Fragment, type ReactNode, useMemo, useState } from "react";

interface CollapsibleListProps<T> {
  items: T[];
  getKey: (item: T, index: number) => string | number;
  renderItem: (item: T, index: number) => ReactNode;
  className: string;
  emptyText?: string;
  initialVisibleCount?: number;
}

export function CollapsibleList<T>({
  items,
  getKey,
  renderItem,
  className,
  emptyText,
  initialVisibleCount = 4,
}: CollapsibleListProps<T>) {
  const [expanded, setExpanded] = useState(false);
  const shouldCollapse = items.length > initialVisibleCount;

  const visibleItems = useMemo(() => {
    if (!shouldCollapse || expanded) {
      return items;
    }
    // Lists are passed in priority order, so collapsed state keeps first 4 records.
    return items.slice(0, initialVisibleCount);
  }, [expanded, initialVisibleCount, items, shouldCollapse]);

  if (items.length === 0) {
    return emptyText ? <p>{emptyText}</p> : null;
  }

  return (
    <>
      <ul className={className}>
        {visibleItems.map((item, index) => (
          <Fragment key={getKey(item, index)}>{renderItem(item, index)}</Fragment>
        ))}
      </ul>

      {shouldCollapse ? (
        <div className="list-toggle-row">
          <button type="button" className="list-toggle" onClick={() => setExpanded((current) => !current)}>
            {expanded ? "Свернуть список" : `Показать все (${items.length})`}
          </button>
        </div>
      ) : null}
    </>
  );
}
