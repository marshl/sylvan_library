import React from 'react';
import { Link } from 'react-router';
import { descriptionHtml, linkifyHtml } from '../html';
import type { DeckCard, DeckDetail } from '../types';
import { useApi } from '../useApi';
import CardLink from './CardLink';
import ColourBars from './ColourBars';

function DeckCardRow({ deckCard }: { deckCard: DeckCard }) {
  return (
    <div className="deck-card">
      {deckCard.count}x{' '}
      <CardLink
        name={deckCard.card_name}
        imageUrl={deckCard.image_url}
        backImageUrl={deckCard.back_image_url}
        layout={deckCard.layout}
        side={deckCard.side}
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

  if (error) return <div className="error">Error: {error}</div>;
  if (loading || !deck) return <div>Loading...</div>;

  return (
    <div className="main-content" style={{ color: 'white' }}>
      <title>{`${deck.name || 'View Deck'} — Sylvan Library`}</title>
      <div className="group-container">
        <div className="field-container">
          <h1>
            {deck.name} {deck.is_prototype && <em>[prototype]</em>}
          </h1>
          {deck.subtitle && <h2>{deck.subtitle}</h2>}
        </div>
        {deck.description && (
          // The description is HTML the owner wrote in the deck editor, and only
          // the owner can see the deck
          <div
            className="field-container rich-text"
            dangerouslySetInnerHTML={{ __html: linkifyHtml(descriptionHtml(deck.description)) }}
          />
        )}
        <div className="field-container">
          {deck.format_display} · {deck.date_created}
        </div>
        <div style={{ maxWidth: 400 }}>
          <ColourBars deckId={deck.id} />
        </div>
      </div>
      <div className="group-container">
        <div className="deck-card-list">
          <div style={{ fontWeight: 'bold' }}>Main {deck.mainboard_count}</div>
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
        </div>
      </div>
    </div>
  );
}
