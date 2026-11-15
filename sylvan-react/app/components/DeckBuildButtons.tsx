import React, { useState } from 'react';
import { useBuildingDeck } from '../buildingDeck';
import type { BoardKey } from '../types';

const BOARDS: { key: BoardKey; label: string }[] = [
  { key: 'main', label: 'Main' },
  { key: 'side', label: 'Side' },
];

/**
 * Buttons on a search result for adding the card to the deck being built, or taking it
 * out, with how many are in each board
 */
export default function DeckBuildButtons({
  cardId,
  cardName,
}: {
  cardId: number;
  cardName: string;
}) {
  const { deck, changeCard } = useBuildingDeck();
  const [pending, setPending] = useState(false);
  if (!deck) return null;
  const counts = deck.cards[cardId] ?? {};

  async function change(board: BoardKey, amount: number) {
    setPending(true);
    try {
      await changeCard(cardId, board, amount);
    } finally {
      setPending(false);
    }
  }

  return (
    // Clicks here shouldn't expand or collapse the result
    <div className="deck-build-buttons" onClick={(e) => e.stopPropagation()}>
      {BOARDS.map(({ key, label }) => {
        const count = counts[key] ?? 0;
        return (
          <span key={key} className={`deck-build-board ${count > 0 ? 'in-deck' : ''}`}>
            <span className="deck-build-label">{label}</span>
            <button
              type="button"
              aria-label={`Take a ${cardName} out of the ${label.toLowerCase()} board`}
              disabled={pending || count === 0}
              onClick={() => change(key, -1)}
            >
              −
            </button>
            <span className="deck-build-count">{count}</span>
            <button
              type="button"
              aria-label={`Add a ${cardName} to the ${label.toLowerCase()} board`}
              disabled={pending}
              onClick={() => change(key, 1)}
            >
              +
            </button>
          </span>
        );
      })}
    </div>
  );
}
