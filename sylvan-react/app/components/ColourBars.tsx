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
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
      <span className="subtitle" style={{ width: 44, flexShrink: 0, color: '#999' }}>
        {label}
      </span>
      <div style={{ position: 'relative', flex: 1 }}>
        <div
          style={{ display: 'flex', gap: 2, height: 20 }}
          onMouseLeave={() => setHovered(null)}
        >
          {total === 0 ? (
            <div style={{ flex: 1, background: '#444', borderRadius: 4 }} />
          ) : (
            counts.map((c, i) => {
              const percent = (c.count / total) * 100;
              return (
                <div
                  key={c.symbol}
                  onMouseEnter={() => setHovered(c)}
                  style={{
                    width: `${percent}%`,
                    background: c.chart_colour,
                    outline: hovered === c ? '1px solid #fff' : undefined,
                    borderRadius:
                      counts.length === 1
                        ? 4
                        : i === 0
                          ? '4px 0 0 4px'
                          : i === counts.length - 1
                            ? '0 4px 4px 0'
                            : 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 3,
                    color: '#222',
                    fontSize: 12,
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                  }}
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
          <div
            style={{
              position: 'absolute',
              bottom: '100%',
              left: 0,
              marginBottom: 4,
              background: '#222',
              border: '1px solid #444',
              borderRadius: 3,
              padding: '2px 8px',
              fontSize: 12,
              color: '#ddd',
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
              zIndex: 10,
            }}
          >
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
  if (!data) return <div style={{ height: 52 }} />;

  return (
    <figure style={{ margin: 0, minWidth: 220 }}>
      <Bar label="Costs" counts={data.mana_symbols} noun="mana symbols" />
      <Bar label="Lands" counts={data.land_symbols} noun="lands" />
      <figcaption className="subtitle" style={{ fontSize: 12, color: '#999' }}>
        Costs: {summary(data.mana_symbols)} — Lands: {summary(data.land_symbols)}
      </figcaption>
    </figure>
  );
}
