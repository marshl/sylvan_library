import React, { useState } from 'react';
import type { StatCount, ColourWeights } from '../types';
import { useApi } from '../useApi';

// Segments narrower than this don't get an inline label; the summary line and
// tooltip still show their count
const MIN_LABEL_PERCENT = 12;

function Bar({
  label,
  counts,
  noun,
  isColourBar,
}: {
  label: string;
  counts: StatCount[];
  noun: string;
  isColourBar: boolean;
}) {
  const [hovered, setHovered] = useState<StatCount | null>(null);
  const total = counts.reduce((sum, c) => sum + c.count, 0);
  return (
    <div className="stat-bar">
      <span className="subtitle stat-bar-label">{label}</span>
      <div className="stat-bar-track">
        <div className="stat-bar-segments" onMouseLeave={() => setHovered(null)}>
          {total === 0 ? (
            <div className="stat-bar-empty" />
          ) : (
            counts.map((c) => {
              const percent = (c.count / total) * 100;
              return (
                <div
                  key={c.symbol}
                  onMouseEnter={() => setHovered(c)}
                  className={`stat-bar-segment ${hovered === c ? 'hovered' : ''}`}
                  style={{ width: `${percent}%`, background: c.chart_colour }}
                >
                  {percent >= MIN_LABEL_PERCENT && (
                    <>
                      {isColourBar && (
                        <i className={`ms ms-${c.symbol.toLowerCase()}`} aria-hidden="true" />
                      )}{' '}
                      {c.count}
                    </>
                  )}
                </div>
              );
            })
          )}
        </div>
        {hovered && (
          <div className="chart-tooltip">
            {hovered.count} {hovered.name.toLowerCase()} {noun}
          </div>
        )}
      </div>
    </div>
  );
}

function summary(counts: StatCount[], isColourBar: boolean): React.ReactNode {
  if (counts.length === 0) return 'none';
  return counts.map((c, i) => (
    <React.Fragment key={c.symbol}>
      {i > 0 && ' · '}
      {isColourBar ? (
        <i className={`ms ms-${c.symbol.toLowerCase()} ms-cost`} aria-label={c.name} />
      ) : (
        c.name
      )}{' '}
      {c.count}
    </React.Fragment>
  ));
}

/**
 * How a deck's coloured mana costs compare to the colours its lands can make
 */
function ColourBars({ deckId }: { deckId: number }) {
  const { data, error } = useApi<ColourWeights>(`/api/cards/deck/${deckId}/colour-weights/`);
  if (error) return <div className="subtitle">Couldn't load colours</div>;
  if (!data) return <div className="stat-bars-loading" />;

  return (
    <figure className="stat-bars">
      <Bar label="Costs" counts={data.mana_symbols} noun="mana symbols" isColourBar={true} />
      <Bar label="Lands" counts={data.land_symbols} noun="lands" isColourBar={true} />
      <figcaption className="subtitle stat-bars-caption">
        Costs: {summary(data.mana_symbols, true)} — Lands: {summary(data.land_symbols, true)}
      </figcaption>
    </figure>
  );
}

/**
 * How a deck's rarity weights
 */
function RarityBars({ deckId }: { deckId: number }) {
  const { data, error } = useApi<StatCount[]>(`/api/cards/deck/${deckId}/rarity-weights/`);
  if (error) return <div className="subtitle">Couldn't load rarities</div>;
  if (!data) return <div className="rarity-bars-loading" />;

  return (
    <figure className="stat-bars">
      <Bar label="Rarities" counts={data} noun="cards" isColourBar={false} />
      <figcaption className="subtitle stat-bars-caption">
        Rarities: {summary(data, false)}
      </figcaption>
    </figure>
  );
}

export default function StatBars({ deckId }: { deckId: number }) {
  return (
    <>
      <div className="deck-stat-bars">
        <ColourBars deckId={deckId} />
      </div>
      <div className="deck-stat-bars">
        <RarityBars deckId={deckId} />
      </div>
    </>
  );
}
