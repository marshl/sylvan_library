import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router';
import Pager from './Pager';
import CardResultDetails from './CardResultDetails';
import { fetchJson, isAbortError } from '../api';

interface CardFace {
  id: number;
  name: string;
  mana_cost: string | null;
  type_line: string | null;
  rules_text: string | null;
  power: string | null;
  toughness: string | null;
  loyalty: string | null;
}

interface Card {
  id: number;
  name: string;
  faces: CardFace[];
}

interface CardFacePrinting {
  id: number;
  image_url: string;
}

interface CardSet {
  id: number;
  name: string;
  code: string;
}

interface CardPrinting {
  id: number;
  set: CardSet;
  face_printings: CardFacePrinting[];
}

interface SearchResult {
  card: Card;
  selected_printing: CardPrinting;
}

interface SearchResponse {
  count: number;
  page: number;
  page_size: number;
  num_pages: number;
  pretty_query_message: string | null;
  error_message: string | null;
  results: SearchResult[];
}

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
        setResponse(
          await fetchJson<SearchResponse>(`/api/search/search/?${params}`, {
            signal: controller.signal,
          }),
        );
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
            {results.map(({ card, selected_printing }) => {
              const facePrintings = selected_printing?.face_printings ?? [];
              return (
                <div key={card.id} className="search-result">
                  <div className="search-result-images">
                    {facePrintings.map((fp) => (
                      <img
                        key={fp.id}
                        className="search-result-image"
                        src={fp.image_url}
                        alt={card.name}
                        loading="lazy"
                      />
                    ))}
                  </div>
                  <div className="search-result-faces">
                    {card.faces.map((face) => (
                      <div key={face.id} className="search-result-base-details">
                        <div className="search-result-title">
                          <span className="face-name">{face.name}</span>
                          {face.mana_cost && (
                            <span className="search-result-mana-cost">
                              {' '}
                              {face.mana_cost}
                            </span>
                          )}
                        </div>
                        {face.type_line && (
                          <div className="search-result-subtitle">{face.type_line}</div>
                        )}
                        {face.rules_text && (
                          <div className="search-result-text">{face.rules_text}</div>
                        )}
                        {face.power !== null && face.toughness !== null && (
                          <div className="search-result-pow-tuff">
                            {face.power}/{face.toughness}
                          </div>
                        )}
                        {face.loyalty !== null && (
                          <div className="search-result-loyalty">
                            Loyalty: {face.loyalty}
                          </div>
                        )}
                      </div>
                    ))}
                    {selected_printing?.set && (
                      <div className="search-result-set">
                        {selected_printing.set.name} ({selected_printing.set.code})
                      </div>
                    )}
                    {selected_printing?.id && (
                      <CardResultDetails printingId={selected_printing.id} />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          <Pager count={count} page={page} pageSize={pageSize} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
