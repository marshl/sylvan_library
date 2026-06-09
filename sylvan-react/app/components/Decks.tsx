import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Deck {
  id: number;
  name: string;
  subtitle: string;
  description: string;
  is_prototype: boolean;
}

function DeckList({ decks }: { decks: Deck[] }) {
  return (
    <div className="search-result-list">
      {decks.map((deck) => (
        <div
          key={deck.id}
          className="search-result js-deck-result"
          style={{ flexDirection: 'row' }}
          data-deck-id={deck.id}
        >
          <div>
            <canvas
              className="js-mini-deck-chart"
              height="75px"
              data-deck-id={deck.id}
            ></canvas>
          </div>
          <div>
            <h2 className="search-result-title">
              <Link to={`/react/decks/${deck.id}`}>
                {deck.is_prototype ? (
                  <em>{deck.name} [prototype]</em>
                ) : (
                  deck.name
                )}
              </Link>
            </h2>

            {deck.subtitle && (
              <h3 className="search-result-subtitle">{deck.subtitle}</h3>
            )}
            {deck.description && (
              <h3 className="subtitle">
                {deck.description.length > 200
                  ? `${deck.description.slice(0, 200)}...`
                  : deck.description}
              </h3>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Decks() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDecks() {
      try {
        const response = await fetch('/api/cards/deck/');
        if (!response.ok) {
          throw new Error('Failed to fetch decks');
        }
        const data = await response.json();
        setDecks(data.results);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }

    fetchDecks();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const finalDecks = decks.filter((d) => !d.is_prototype);
  const prototypeDecks = decks.filter((d) => d.is_prototype);

  return (
    <div className="main-content">
      <h1>Your Decks</h1>
      <div style={{ margin: '15px' }}>
        <Link to="/react/decks/create" className="action-button">
          Create New Deck
        </Link>
        <Link to="/react/decks/stats" className="action-button">
          Deck Stats
        </Link>
      </div>
      <DeckList decks={finalDecks} />

      <h1>Prototype Decks</h1>
      <DeckList decks={prototypeDecks} />
    </div>
  );
}
