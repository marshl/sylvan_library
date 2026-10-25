import React, { useState } from 'react';
import { fetchJson } from '../api';
import { useApi } from '../useApi';
import CardLink from './CardLink';
import RequireLogin from './RequireLogin';

interface StatsCard {
  card_id: number;
  name: string;
  image_url: string;
  back_image_url: string | null;
}

interface DeckStatsPayload {
  deck_count: number;
  unused_cards: StatsCard[];
  unused_commanders: StatsCard[];
  partner_pairs: [StatsCard, StatsCard][];
  background_pairs: [StatsCard, StatsCard][];
}

function CardList({ cards }: { cards: StatsCard[] }) {
  if (cards.length === 0) return <p className="subtitle">None</p>;
  return (
    <ul>
      {cards.map((card) => (
        <li key={card.card_id}>
          <CardLink name={card.name} imageUrl={card.image_url} backImageUrl={card.back_image_url} />
        </li>
      ))}
    </ul>
  );
}

function PairList({ pairs }: { pairs: [StatsCard, StatsCard][] }) {
  if (pairs.length === 0) return <p className="subtitle">None</p>;
  return (
    <ul>
      {pairs.map(([first, second]) => (
        <li key={`${first.card_id}-${second.card_id}`}>
          <CardLink
            name={first.name}
            imageUrl={first.image_url}
            backImageUrl={first.back_image_url}
          />{' '}
          //{' '}
          <CardLink
            name={second.name}
            imageUrl={second.image_url}
            backImageUrl={second.back_image_url}
          />
        </li>
      ))}
    </ul>
  );
}

function Stats() {
  // Bumped after a reroll so the stats reload with the new seed
  const [version, setVersion] = useState(0);
  const [rerolling, setRerolling] = useState(false);
  const { data, error } = useApi<DeckStatsPayload>('/api/cards/deck-stats/', version);

  async function reroll() {
    setRerolling(true);
    try {
      await fetchJson('/api/cards/deck-stats/reroll/', { method: 'POST' });
      setVersion((v) => v + 1);
    } finally {
      setRerolling(false);
    }
  }

  if (error) return <div className="error">Error: {error}</div>;
  if (!data) return <div>Loading...</div>;

  return (
    <div className="main-content" style={{ color: 'white' }}>
      <div className="group-container">
        <div className="field-container">
          <h2>Some unused cards</h2>
          <CardList cards={data.unused_cards} />
          <h2>Some unused commanders</h2>
          <CardList cards={data.unused_commanders} />
          <h2>Partner pairings</h2>
          <PairList pairs={data.partner_pairs} />
          <h2>Background pairings</h2>
          <PairList pairs={data.background_pairs} />
          <div>
            <button type="button" className="action-button" onClick={reroll} disabled={rerolling}>
              See more unused cards
            </button>
          </div>
          <h2>Decks</h2> {data.deck_count}
        </div>
      </div>
    </div>
  );
}

export default function DeckStats() {
  return (
    <RequireLogin what="see your deck stats">
      <Stats />
    </RequireLogin>
  );
}
