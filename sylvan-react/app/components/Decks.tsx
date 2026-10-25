import React, { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { descriptionHtml, linkifyHtml } from '../html';
import type { DeckSummary, Paginated } from '../types';
import { useApi } from '../useApi';
import CardNameInput from './CardNameInput';
import ColourBars from './ColourBars';
import Pager from './Pager';
import RequireLogin from './RequireLogin';

// Matches PAGE_SIZE in the DRF settings
const PAGE_SIZE = 10;

/**
 * The description HTML cut down to a preview length of visible text, keeping its
 * formatting. Descriptions are HTML from the rich text editor.
 */
function descriptionPreview(html: string, length = 200): string {
  const body = new DOMParser().parseFromString(html, 'text/html').body;
  const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  let remaining = length;
  while (walker.nextNode()) {
    const text = walker.currentNode as Text;
    if (text.data.length <= remaining) {
      remaining -= text.data.length;
      continue;
    }
    text.data = `${text.data.slice(0, remaining)}...`;
    // Drop everything after the cut, at every level up to the body
    for (let node: Node | null = text; node && node !== body; node = node.parentNode) {
      while (node.nextSibling) node.nextSibling.remove();
    }
    break;
  }
  return body.innerHTML;
}

type ShowOption = 'decks' | 'prototypes' | 'all';

const SHOW_OPTIONS: { value: ShowOption; label: string; prototypes: string }[] = [
  { value: 'decks', label: 'Decks', prototypes: 'exclude' },
  { value: 'prototypes', label: 'Prototypes', prototypes: 'only' },
  { value: 'all', label: 'Both', prototypes: 'include' },
];

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'name', label: 'Name' },
];

// The URL params that filter the list, which a new filter resets the page for
const FILTER_PARAMS = ['q', 'card', 'format', 'from', 'to', 'show'];

interface DeckFormat {
  value: string;
  label: string;
  count: number;
}

type UpdateParams = (changes: Record<string, string>, replace?: boolean) => void;

/**
 * A text filter that's kept in the URL. The URL is updated a moment after typing stops,
 * so each keystroke doesn't start a new search or add to the history.
 */
function useUrlText(
  name: string,
  urlValue: string,
  updateParams: UpdateParams,
): [string, (value: string) => void] {
  const [value, setValue] = useState(urlValue);
  const written = useRef(urlValue);

  // Going back or forward changes the URL without typing
  useEffect(() => {
    if (urlValue !== written.current) {
      written.current = urlValue;
      setValue(urlValue);
    }
  }, [urlValue]);

  // Only typing restarts the wait. updateParams is left out of the dependencies as it's
  // a new function on every render.
  useEffect(() => {
    if (value === written.current) return;
    const timer = setTimeout(() => {
      written.current = value;
      updateParams({ [name]: value }, true);
    }, 300);
    return () => clearTimeout(timer);
  }, [value]);

  return [value, setValue];
}

function DeckFilters({
  searchParams,
  updateParams,
  formats,
}: {
  searchParams: URLSearchParams;
  updateParams: UpdateParams;
  formats: DeckFormat[];
}) {
  const [text, setText] = useUrlText('q', searchParams.get('q') ?? '', updateParams);
  const [card, setCard] = useUrlText('card', searchParams.get('card') ?? '', updateParams);
  const [from, setFrom] = useUrlText('from', searchParams.get('from') ?? '', updateParams);
  const [to, setTo] = useUrlText('to', searchParams.get('to') ?? '', updateParams);
  const show = searchParams.get('show') ?? 'decks';

  return (
    <div className="group-container deck-filters">
      <div className="row">
        <div className="field-container">
          <label htmlFor="deck-search">Search</label>
          <input
            id="deck-search"
            type="search"
            placeholder="Name, subtitle or description"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>
        <div className="field-container">
          <label htmlFor="deck-card">Contains card</label>
          <CardNameInput
            id="deck-card"
            placeholder="Card name, or !name for an exact match"
            exactOnPick
            value={card}
            onChange={setCard}
          />
        </div>
        <div className="field-container">
          <label htmlFor="deck-format">Format</label>
          <select
            id="deck-format"
            value={searchParams.get('format') ?? ''}
            onChange={(e) => updateParams({ format: e.target.value })}
          >
            <option value="">All formats</option>
            {formats.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label} ({f.count})
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="row">
        <div className="field-container">
          <label htmlFor="deck-year-from">Created</label>
          <div className="deck-year-range">
            <input
              id="deck-year-from"
              type="number"
              placeholder="From year"
              aria-label="From year"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
            />
            <span>to</span>
            <input
              type="number"
              placeholder="To year"
              aria-label="To year"
              value={to}
              onChange={(e) => setTo(e.target.value)}
            />
          </div>
        </div>
        <div className="field-container">
          <span className="field-label" id="deck-show-label">
            Show
          </span>
          <div className="toggle-group" role="group" aria-labelledby="deck-show-label">
            {SHOW_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`page-button ${show === option.value ? 'is-active' : ''}`}
                aria-pressed={show === option.value}
                onClick={() => updateParams({ show: option.value === 'decks' ? '' : option.value })}
              >
                <span className="page-button-text">{option.label}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="field-container">
          <label htmlFor="deck-sort">Sort by</label>
          <select
            id="deck-sort"
            value={searchParams.get('sort') ?? 'newest'}
            onChange={(e) =>
              updateParams({ sort: e.target.value === 'newest' ? '' : e.target.value })
            }
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function DeckList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get('page') ?? '1') || 1;
  const show = SHOW_OPTIONS.find((o) => o.value === searchParams.get('show')) ?? SHOW_OPTIONS[0];
  const formats = useApi<DeckFormat[]>('/api/cards/deck/formats/');
  const formatLabels = new Map((formats.data ?? []).map((f) => [f.value, f.label]));

  const apiParams = new URLSearchParams({ prototypes: show.prototypes, page: String(page) });
  for (const [param, apiParam] of [
    ['q', 'q'],
    ['card', 'card'],
    ['format', 'deck_format'],
    ['from', 'year_from'],
    ['to', 'year_to'],
    ['sort', 'sort'],
  ]) {
    const value = searchParams.get(param);
    if (value) apiParams.set(apiParam, value);
  }
  const { data, loading, error } = useApi<Paginated<DeckSummary>>(`/api/cards/deck/?${apiParams}`);

  const updateParams: UpdateParams = (changes, replace = false) => {
    setSearchParams(
      (params) => {
        for (const [key, value] of Object.entries(changes)) {
          if (value) params.set(key, value);
          else params.delete(key);
        }
        if (Object.keys(changes).some((key) => FILTER_PARAMS.includes(key))) {
          params.delete('page');
        }
        return params;
      },
      { replace },
    );
  };

  function setPage(nextPage: number) {
    updateParams({ page: nextPage > 1 ? String(nextPage) : '' });
    window.scrollTo(0, 0);
  }

  const filtered = FILTER_PARAMS.some((param) => searchParams.has(param));

  return (
    <>
      <DeckFilters
        searchParams={searchParams}
        updateParams={updateParams}
        formats={formats.data ?? []}
      />
      {error && <div className="error">Error: {error}</div>}
      {!data && !error && <div>Loading...</div>}
      {data && (
        <>
          <div className="deck-list-count subtitle">
            {loading
              ? 'Searching…'
              : `${data.count} ${show.value === 'prototypes' ? 'prototype' : 'deck'}${
                  data.count === 1 ? '' : 's'
                }`}
            {filtered && (
              <button
                type="button"
                className="link-button"
                onClick={() =>
                  setSearchParams((params) => {
                    for (const param of [...FILTER_PARAMS, 'page']) params.delete(param);
                    return params;
                  })
                }
              >
                Clear filters
              </button>
            )}
          </div>
          {data.results.length === 0 ? (
            <div className="subtitle">
              {filtered ? 'No decks match these filters' : 'No decks yet'}
            </div>
          ) : (
            <div className="search-result-list">
              {data.results.map((deck) => (
                <div
                  key={deck.id}
                  className="search-result"
                  style={{ flexDirection: 'row', gap: 16 }}
                >
                  <div style={{ width: 260, flexShrink: 0, padding: 8 }}>
                    <ColourBars deckId={deck.id} />
                  </div>
                  <div>
                    <h2 className="search-result-title">
                      <Link to={`/decks/${deck.id}`}>
                        {deck.is_prototype ? <em>{deck.name} [prototype]</em> : deck.name}
                      </Link>
                    </h2>
                    {deck.subtitle && <h3 className="search-result-subtitle">{deck.subtitle}</h3>}
                    <div className="deck-list-meta">
                      {formatLabels.get(deck.format) ?? deck.format} ·{' '}
                      {formatDate(deck.date_created)}
                    </div>
                    {deck.description && (
                      <h3
                        className="subtitle rich-text"
                        dangerouslySetInnerHTML={{
                          __html: linkifyHtml(
                            descriptionPreview(descriptionHtml(deck.description)),
                          ),
                        }}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
          <Pager count={data.count} page={page} pageSize={PAGE_SIZE} onPageChange={setPage} />
        </>
      )}
    </>
  );
}

export default function Decks() {
  return (
    <RequireLogin what="see your decks">
      <div className="main-content">
        <h1>Your Decks</h1>
        <div style={{ margin: '15px 0' }}>
          <Link to="/decks/create" className="action-button">
            Create New Deck
          </Link>{' '}
          <Link to="/decks/stats" className="action-button">
            Deck Stats
          </Link>
        </div>
        <DeckList />
      </div>
    </RequireLogin>
  );
}
