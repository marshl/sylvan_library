import React from 'react';
import { Link, useSearchParams } from 'react-router';
import type { DeckSummary, Paginated } from '../types';
import { useApi } from '../useApi';
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

function DeckList({
  isPrototype,
  pageParam,
}: {
  isPrototype: boolean;
  // The URL param holding this list's page, so both lists can be paged separately
  pageParam: string;
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get(pageParam) ?? '1') || 1;
  const { data, loading, error } = useApi<Paginated<DeckSummary>>(
    `/api/cards/deck/?${new URLSearchParams({
      is_prototype: String(isPrototype),
      page: String(page),
    })}`,
  );

  function setPage(nextPage: number) {
    setSearchParams((params) => {
      if (nextPage > 1) params.set(pageParam, String(nextPage));
      else params.delete(pageParam);
      return params;
    });
  }

  if (error) return <div className="error">Error: {error}</div>;
  if (loading || !data) return <div>Loading...</div>;
  if (data.results.length === 0) return <div className="subtitle">No decks yet</div>;

  return (
    <>
      <div className="search-result-list">
        {data.results.map((deck) => (
          <div key={deck.id} className="search-result" style={{ flexDirection: 'row', gap: 16 }}>
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
              {deck.description && (
                <h3
                  className="subtitle"
                  dangerouslySetInnerHTML={{ __html: descriptionPreview(deck.description) }}
                />
              )}
            </div>
          </div>
        ))}
      </div>
      <Pager count={data.count} page={page} pageSize={PAGE_SIZE} onPageChange={setPage} />
    </>
  );
}

export default function Decks() {
  return (
    <RequireLogin what="see your decks">
      <div className="main-content">
        <h1>Your Decks</h1>
        <div style={{ margin: '15px' }}>
          <Link to="/decks/create" className="action-button">
            Create New Deck
          </Link>{' '}
          <Link to="/decks/stats" className="action-button">
            Deck Stats
          </Link>
        </div>
        <DeckList isPrototype={false} pageParam="page" />

        <h1>Prototype Decks</h1>
        <DeckList isPrototype pageParam="prototype_page" />
      </div>
    </RequireLogin>
  );
}
