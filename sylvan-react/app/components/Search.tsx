import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router';
import Pager from './Pager';
import SearchResult from './SearchResult';
import { fetchJson, isAbortError } from '../api';
import type { SearchMode, SearchResponse, SearchResult as Result } from '../types';

const MODES: { mode: SearchMode; label: string }[] = [
  { mode: 'cards', label: 'Cards' },
  { mode: 'printings', label: 'Printings' },
];

// Printings of the same card are separate results when searching by printing
function resultId(result: Result, mode: SearchMode): number {
  return mode === 'printings' ? result.selected_printing.id : result.card.id;
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlQuery = searchParams.get('query') ?? '';
  const urlPage = Number(searchParams.get('page') ?? '1') || 1;
  const submittedQuery = urlQuery;
  const page = urlPage;
  const mode: SearchMode = searchParams.get('mode') === 'printings' ? 'printings' : 'cards';
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    if (!submittedQuery) {
      setResponse(null);
      return;
    }
    const controller = new AbortController();
    async function fetchResults() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          q: submittedQuery,
          page: String(page),
          mode,
        });
        const data = await fetchJson<SearchResponse>(`/api/search/search/?${params}`, {
          signal: controller.signal,
        });
        setResponse(data);
        // A single result is almost certainly the card being looked for
        setExpandedId(data.results.length === 1 ? resultId(data.results[0], data.mode) : null);
      } catch (err) {
        if (isAbortError(err)) return;
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    fetchResults();
    return () => controller.abort();
  }, [submittedQuery, page, mode]);

  function navigate(nextPage: number, nextMode: SearchMode) {
    const params: Record<string, string> = {};
    if (submittedQuery) params.query = submittedQuery;
    if (nextPage > 1) params.page = String(nextPage);
    if (nextMode !== 'cards') params.mode = nextMode;
    setSearchParams(params);
    window.scrollTo(0, 0);
  }

  function setPage(nextPage: number) {
    navigate(nextPage, mode);
  }

  const results = response?.results ?? [];
  const count = response?.count ?? 0;
  const pageSize = response?.page_size ?? 25;
  // The previous results stay up while the next ones load, so they're shown in the
  // mode they were searched in
  const resultMode = response?.mode ?? mode;

  return (
    <div className="results-page">
      {!submittedQuery && (
        <div className="no-search-results">
          <div className="no-search-results-content">
            Search for a card using the search bar above
          </div>
        </div>
      )}

      {error && <div className="error">Error: {error}</div>}

      {submittedQuery && !error && (
        <>
          <div className="action-bar">
            <div className="action-bar-row">
              {response?.error_message && (
                <div className="result-count-container">{response.error_message}</div>
              )}
              <div className="result-count-container">
                <div className="results-count">
                  {loading || !response
                    ? 'Searching…'
                    : `${count} ${resultMode === 'printings' ? 'printing' : 'card'}${
                        count === 1 ? '' : 's'
                      } found${
                        response.pretty_query_message
                          ? ` where ${response.pretty_query_message}`
                          : ''
                      }`}
                </div>
              </div>
              <div className="toggle-group" role="group" aria-label="Search by">
                {MODES.map((option) => (
                  <button
                    key={option.mode}
                    type="button"
                    className={`page-button ${mode === option.mode ? 'is-active' : ''}`}
                    aria-pressed={mode === option.mode}
                    onClick={() => mode !== option.mode && navigate(1, option.mode)}
                  >
                    <span className="page-button-text">{option.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
          <Pager count={count} page={page} pageSize={pageSize} onPageChange={setPage} />
          <div className="search-result-list">
            {results.map((result) => (
              <SearchResult
                // Keyed on the page too so a card's local state (selected printing,
                // ownership refreshes) doesn't leak between searches
                key={`${submittedQuery}:${resultMode}:${page}:${resultId(result, resultMode)}`}
                result={result}
                expanded={expandedId === resultId(result, resultMode)}
                onExpand={() => setExpandedId(resultId(result, resultMode))}
              />
            ))}
          </div>
          {response && !loading && results.length === 0 && (
            <div className="no-search-results">
              <div className="no-search-results-content">No results found</div>
            </div>
          )}
          <Pager count={count} page={page} pageSize={pageSize} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
