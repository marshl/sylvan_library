import React from 'react';
import { Link, useNavigate } from 'react-router';
import { useBuildingDeck } from '../buildingDeck';
import { descriptionHtml, linkifyHtml } from '../html';
import type { DeckCard, DeckDetail } from '../types';
import { useApi } from '../useApi';
import CardLink from './CardLink';
import StatBars from './StatBars';

function formatDate(isoDate: string): string {
  // Parsed as local midnight so the date doesn't shift with the timezone
  return new Date(`${isoDate}T00:00`).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function DeckCardRow({ deckCard }: { deckCard: DeckCard }) {
  return (
    <div className="deck-card">
      {deckCard.count}x{' '}
      <CardLink
        name={deckCard.card_name}
        imageUrl={deckCard.image_url}
        backImageUrl={deckCard.back_image_url}
        sideways={deckCard.sideways}
        newTab
      />
      {deckCard.icon && (
        <>
          {' '}
          <i className={`ms ms-${deckCard.icon}`} />
        </>
      )}
    </div>
  );
}

export default function DeckView({ deckId }: { deckId: number }) {
  const { data: deck, loading, error } = useApi<DeckDetail>(`/api/cards/deck/${deckId}/`);
  const { deck: building, start: startBuilding } = useBuildingDeck();
  const navigate = useNavigate();

  if (error) return <div className="error">Error: {error}</div>;
  if (loading || !deck) return <div>Loading...</div>;

  return (
    <div className="main-content">
      <title>{`${deck.name || 'View Deck'} — Sylvan Library`}</title>
      <div className="group-container">
        <div className="field-container">
          <h1>
            {deck.name} {deck.is_prototype && <em>[prototype]</em>}
          </h1>
          {deck.subtitle && <h2>{deck.subtitle}</h2>}
          <div className="deck-meta">
            <span className="deck-format">{deck.format_display}</span>
            <span>Created {formatDate(deck.date_created)}</span>
          </div>
        </div>
        {deck.description && (
          // The description is HTML the owner wrote in the deck editor, and only
          // the owner can see the deck
          <div
            className="field-container rich-text deck-description"
            dangerouslySetInnerHTML={{ __html: linkifyHtml(descriptionHtml(deck.description)) }}
          />
        )}
        <StatBars deckId={deck.id} />
      </div>
      <div className="group-container">
        <div className="deck-card-list">
          <div className="deck-board-title">Main {deck.mainboard_count}</div>
          {deck.card_groups.map((group) => (
            <div key={group.code} className="card-group">
              <div className="group-title">
                {group.count} {group.name}
                {/* Modal DFCs can be played as lands without being in the Lands group */}
                {group.code === 'land' && group.count !== deck.total_land_count && (
                  <>
                    {' '}
                    ({deck.total_land_count} <i className="ms ms-land" />)
                  </>
                )}
              </div>
              {group.cards.map((deckCard) => (
                <DeckCardRow key={deckCard.id} deckCard={deckCard} />
              ))}
            </div>
          ))}
          {deck.sideboard.length > 0 && (
            <div className="card-group">
              <div className="group-title">Sideboard</div>
              {deck.sideboard.map((deckCard) => (
                <DeckCardRow key={deckCard.id} deckCard={deckCard} />
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="group-container">
        <div className="deck-action-bar">
          <Link className="action-button" to="/decks">
            Back
          </Link>
          <Link className="action-button" to={`/decks/${deck.id}/edit`}>
            Edit
          </Link>
          {building?.id !== deck.id && (
            <button
              type="button"
              className="action-button"
              onClick={async () => {
                await startBuilding(deck.id);
                navigate('/search');
              }}
            >
              Build in search
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
