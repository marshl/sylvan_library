import React from 'react';

interface PagerProps {
  count: number;
  page: number;
  onPageChange: (page: number) => void;
}

export default function Pager({ count, page, onPageChange }: PagerProps) {
  const pageCount = Math.ceil(count / 25);
  const pages = Array.from({ length: pageCount }, (_, i) => i + 1);

  return (
    <div className="pagination-container">
      <div className="page-button-list">
        {pages.map((p) => (
          <button
            key={p}
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
