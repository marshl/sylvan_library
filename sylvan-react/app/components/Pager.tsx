import React from 'react';

interface PagerProps {
  count: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export default function Pager({ count, page, pageSize, onPageChange }: PagerProps) {
  const pageCount = Math.max(1, Math.ceil(count / pageSize));
  if (pageCount <= 1) return null;
  const pages = Array.from({ length: pageCount }, (_, i) => i + 1);

  return (
    <div className="pagination-container">
      <div className="page-button-list">
        {pages.map((p) => (
          <button
            key={p}
            type="button"
            className={`page-button ${p === page ? 'is-active' : ''}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}
