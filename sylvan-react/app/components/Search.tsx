import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router';
import Pager from './Pager';
import SearchResult from './SearchResult';
import { fetchJson, isAbortError } from '../api';
import type { SearchResponse } from '../types';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlQuery = searchParams.get('query') ?? '';
  const urlPage = Number(searchParams.get('page') ?? '1') || 1;
  const [query, setQuery] = useState(urlQuery);
  const submittedQuery = urlQuery;
  const page = urlPage;
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCardId, setExpandedCardId] = useState<number | null>(null);

  useEffect(() => {
    setQuery(urlQuery);
  }, [urlQuery]);

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
        });
        const data = await fetchJson<SearchResponse>(`/api/search/search/?${params}`, {
          signal: controller.signal,
        });
        setResponse(data);
        // A single result is almost certainly the card being looked for
        setExpandedCardId(data.results.length === 1 ? data.results[0].card.id : null);
      } catch (err) {
        if (isAbortError(err)) return;
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    fetchResults();
    return () => controller.abort();
  }, [submittedQuery, page]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setSearchParams({});
    } else {
      setSearchParams({ query: trimmed });
    }
  }

  function setPage(nextPage: number) {
    const params: Record<string, string> = {};
    if (submittedQuery) params.query = submittedQuery;
    if (nextPage > 1) params.page = String(nextPage);
    setSearchParams(params);
    window.scrollTo(0, 0);
  }

  const results = response?.results ?? [];
  const count = response?.count ?? 0;
  const pageSize = response?.page_size ?? 25;

  return (
    <div className="results-page">
      <form className="search-form" onSubmit={onSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search cards (e.g. lightning bolt)"
          aria-label="Card search"
        />
        <button type="submit">Search</button>
      </form>

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
                    : `${count} result${count === 1 ? '' : 's'} found${
                        response.pretty_query_message
                          ? ` where ${response.pretty_query_message}`
                          : ''
                      }`}
                </div>
              </div>
            </div>
          </div>
          <Pager count={count} page={page} pageSize={pageSize} onPageChange={setPage} />
          <div className="search-result-list">
            {results.map((result) => (
              <SearchResult
                // Keyed on the page too so a card's local state (selected printing,
                // ownership refreshes) doesn't leak between searches
                key={`${submittedQuery}:${page}:${result.card.id}`}
                result={result}
                expanded={expandedCardId === result.card.id}
                onExpand={() => setExpandedCardId(result.card.id)}
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
