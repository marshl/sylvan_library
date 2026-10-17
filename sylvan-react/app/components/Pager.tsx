import React from 'react';

interface PagerProps {
  count: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  // How many page numbers to show either side of the current page
  pageSpan?: number;
}

interface PageButton {
  key: string;
  label: string;
  page: number | null;
  active?: boolean;
}

function getPageButtons(page: number, pageCount: number, span: number): PageButton[] {
  const buttons: PageButton[] = [];
  for (let p = Math.max(1, page - span); p <= Math.min(pageCount, page + span); p++) {
    buttons.push({ key: String(p), label: String(p), page: p, active: p === page });
  }

  if (page - span > 1) {
    buttons.unshift({ key: 'start-spacer', label: '...', page: null });
    buttons.unshift({ key: '1', label: '1', page: 1 });
  }
  if (page + span <= pageCount - 2) {
    buttons.push({ key: 'end-spacer', label: '...', page: null });
  }
  if (page + span <= pageCount - 1) {
    buttons.push({ key: String(pageCount), label: String(pageCount), page: pageCount });
  }

  buttons.unshift({ key: 'previous', label: 'Previous', page: page > 1 ? page - 1 : null });
  buttons.push({ key: 'next', label: 'Next', page: page < pageCount ? page + 1 : null });
  return buttons;
}

export default function Pager({
  count,
  page,
  pageSize,
  onPageChange,
  pageSpan = 3,
}: PagerProps) {
  const pageCount = Math.max(1, Math.ceil(count / pageSize));
  if (pageCount <= 1) return null;

  return (
    <div className="pagination-container">
      <div className="page-button-list">
        {getPageButtons(page, pageCount, pageSpan).map((button) => (
          <button
            key={button.key}
            type="button"
            className={`page-button ${button.active ? 'is-active' : ''} ${
              button.page === null ? 'disabled is-disabled' : ''
            }`}
            disabled={button.page === null}
            onClick={() => button.page !== null && onPageChange(button.page)}
          >
            <span className="page-button-text">{button.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
