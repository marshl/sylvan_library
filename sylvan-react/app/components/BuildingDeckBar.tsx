import React from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router';
import { useBuildingDeck } from '../buildingDeck';

/**
 * Shown under the top bar while a deck is being built from the search page, with links
 * to the deck and to filter searches by it
 */
export default function BuildingDeckBar() {
  const { deck, stop, error } = useBuildingDeck();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  if (!deck) return null;

  const filter = `deck:${deck.id}`;
  const query = searchParams.get('query') ?? '';
  const onSearchPage = location.pathname === '/search';
  // Whether the search already hides the deck's cards
  const hiding = new RegExp(`(^|\\s)-${filter}(\\s|$)`).test(query);

  function search(newQuery: string) {
    const params = new URLSearchParams(searchParams);
    params.set('query', newQuery);
    params.delete('page');
    navigate(`/search?${params}`);
  }

  function toggleHiding() {
    if (hiding) {
      search(query.replace(new RegExp(`(^|\\s)-${filter}(?=\\s|$)`), '').trim());
    } else {
      search(`${query} -${filter}`.trim());
    }
  }

  const { main, side } = deck.board_counts;
  return (
    <div className="building-deck-bar" role="status">
      <span>
        Building <Link to={`/decks/${deck.id}`}>{deck.name}</Link>
        <span className="subtitle">
          {' '}
          · Main {main}
          {side > 0 && ` · Side ${side}`}
        </span>
      </span>
      {error && <span className="line-error">{error}</span>}
      <span className="building-deck-actions">
        {onSearchPage && query && (
          <button type="button" className="link-button" onClick={toggleHiding}>
            {hiding ? 'Show cards in the deck' : 'Hide cards in the deck'}
          </button>
        )}
        <button type="button" className="link-button" onClick={() => search(filter)}>
          Search the deck
        </button>
        <Link to={`/decks/${deck.id}/edit`}>Edit</Link>
        <button type="button" className="link-button" onClick={stop}>
          Stop building
        </button>
      </span>
    </div>
  );
}
