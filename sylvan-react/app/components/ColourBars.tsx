import React, { useState } from 'react';
import type { ColourCount, ColourWeights } from '../types';
import { useApi } from '../useApi';

// Segments narrower than this don't get an inline label; the summary line and
// tooltip still show their count
const MIN_LABEL_PERCENT = 12;

function Bar({ label, counts, noun }: { label: string; counts: ColourCount[]; noun: string }) {
  const [hovered, setHovered] = useState<ColourCount | null>(null);
  const total = counts.reduce((sum, c) => sum + c.count, 0);

  return (
    <div className="colour-bar">
      <span className="subtitle colour-bar-label">{label}</span>
      <div className="colour-bar-track">
        <div className="colour-bar-segments" onMouseLeave={() => setHovered(null)}>
          {total === 0 ? (
            <div className="colour-bar-empty" />
          ) : (
            counts.map((c) => {
              const percent = (c.count / total) * 100;
              return (
                <div
                  key={c.symbol}
                  onMouseEnter={() => setHovered(c)}
                  className={`colour-bar-segment ${hovered === c ? 'hovered' : ''}`}
                  style={{ width: `${percent}%`, background: c.chart_colour }}
                >
                  {percent >= MIN_LABEL_PERCENT && (
                    <>
                      <i className={`ms ms-${c.symbol.toLowerCase()}`} aria-hidden="true" />
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

function summary(counts: ColourCount[]): React.ReactNode {
  if (counts.length === 0) return 'none';
  return counts.map((c, i) => (
    <React.Fragment key={c.symbol}>
      {i > 0 && ' · '}
      <i className={`ms ms-${c.symbol.toLowerCase()} ms-cost`} aria-label={c.name} /> {c.count}
    </React.Fragment>
  ));
}

/**
 * How a deck's coloured mana costs compare to the colours its lands can make
 */
export default function ColourBars({ deckId }: { deckId: number }) {
  const { data, error } = useApi<ColourWeights>(`/api/cards/deck/${deckId}/colour-weights/`);
  if (error) return <div className="subtitle">Couldn't load colours</div>;
  if (!data) return <div className="colour-bars-loading" />;

  return (
    <figure className="colour-bars">
      <Bar label="Costs" counts={data.mana_symbols} noun="mana symbols" />
      <Bar label="Lands" counts={data.land_symbols} noun="lands" />
      <figcaption className="subtitle colour-bars-caption">
        Costs: {summary(data.mana_symbols)} — Lands: {summary(data.land_symbols)}
      </figcaption>
    </figure>
  );
}
