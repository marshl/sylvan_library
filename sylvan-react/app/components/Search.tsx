import React, { useState, useEffect } from 'react';
import Pager from './Pager';

interface Card {
  id: number;
  name: string;
  mana_cost: string;
  type: string;
  text: string;
  power: string;
  toughness: string;
}

export default function Search() {
  const [results, setResults] = useState<Card[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState('name');

  useEffect(() => {
    async function fetchResults() {
      setLoading(true);
      try {
        const response = await fetch(
          `/api/cards/card/?ordering=${sortOrder}&page=${page}`
        );
        if (!response.ok) {
          throw new Error('Failed to fetch search results');
        }
        const data = await response.json();
        setResults(data.results);
        setCount(data.count);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }

    fetchResults();
  }, [sortOrder, page]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="results-page">
      <div className="action-bar">
        <div className="action-bar-row">
          <div className="result-count-container">
            <div className="results-count">{count} results found</div>
          </div>
          <div className="select-group">
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            >
              <option value="name">Name (ascending)</option>
              <option value="-name">Name (descending)</option>
              <option value="mana_value">Mana value (ascending)</option>
              <option value="-mana_value">Mana value (descending)</option>
            </select>
          </div>
        </div>
      </div>
      <Pager count={count} page={page} onPageChange={setPage} />
      <div className="search-result-list">
        {results.map((card) => (
          <div key={card.id} className="search-result">
            <div className="search-result-base-details">
              <div className="search-result-title">{card.name}</div>
              <div className="search-result-mana-cost">{card.mana_cost}</div>
              <div className="search-result-subtitle">{card.type}</div>
              <div
                className="search-result-text"
                dangerouslySetInnerHTML={{ __html: card.text }}
              />
              {card.power && (
                <div className="search-result-pow-tuff">
                  {card.power}/{card.toughness}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <Pager count={count} page={page} onPageChange={setPage} />
    </div>
  );
}
