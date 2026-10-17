import React, { useEffect, useState } from 'react';

interface Legality {
  format: string;
  restriction: string;
}

interface DetailsPayload {
  id: number;
  number: string | null;
  flavour_text: string | null;
  artist: string | null;
  set: {
    code: string;
    name: string;
    release_date: string | null;
    total_set_size: number | null;
  };
  legalities: Legality[];
}

type TabKey =
  | 'details'
  | 'rulings'
  | 'languages'
  | 'ownership'
  | 'add'
  | 'decks'
  | 'links'
  | 'prices';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'details', label: 'Details' },
  { key: 'rulings', label: 'Rulings' },
  { key: 'languages', label: 'Languages' },
  { key: 'ownership', label: 'Ownership' },
  { key: 'add', label: 'Add cards' },
  { key: 'decks', label: 'Decks' },
  { key: 'links', label: 'Links' },
  { key: 'prices', label: 'Prices' },
];

function DetailsTab({ printingId }: { printingId: number }) {
  const [data, setData] = useState<DetailsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    async function fetchDetails() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/cards/printing-details/${printingId}/`,
          { signal: controller.signal },
        );
        if (!response.ok) {
          throw new Error(`Details request failed (${response.status})`);
        }
        setData(await response.json());
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    fetchDetails();
    return () => controller.abort();
  }, [printingId]);

  if (loading) return <div className="subtitle">Loading…</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="extraDetails">
      {data.flavour_text && (
        <div>
          <span className="subtitle">
            <b>Flavour: </b>
          </span>
          <span className="subtitle">
            <i>{data.flavour_text}</i>
          </span>
        </div>
      )}
      {data.artist && (
        <div>
          <span className="subtitle">
            <b>Artist: </b>
          </span>
          <span className="subtitle">{data.artist}</span>
        </div>
      )}
      <div>
        <span className="subtitle">
          <b>Set: </b>
        </span>
        <span className="subtitle">
          {data.set.name} ({data.set.code})
        </span>
      </div>
      {data.set.release_date && (
        <div>
          <span className="subtitle">
            <b>Release date: </b>
          </span>
          <span className="subtitle">{data.set.release_date}</span>
        </div>
      )}
      {data.number && (
        <div>
          <span className="subtitle">
            <b>Number: </b>
          </span>
          <span className="subtitle">
            {data.number}
            {data.set.total_set_size ? `/${data.set.total_set_size}` : ''}
          </span>
        </div>
      )}
      {data.legalities.length > 0 && (
        <div>
          <div className="subtitle">
            <b>Legalities:</b>
          </div>
          {data.legalities.map((l) => (
            <div key={l.format}>
              <span className="subtitle">{l.format}: </span>
              <span className={`subtitle ${l.restriction.toLowerCase()}`}>
                {l.restriction}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ComingSoon({ label }: { label: string }) {
  return (
    <div className="subtitle">
      {label} — not yet ported from the Django UI.
    </div>
  );
}

export default function CardResultDetails({ printingId }: { printingId: number }) {
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState<TabKey>('details');

  return (
    <div className="search-result-tab-container">
      <span
        className="tab-expander"
        role="button"
        tabIndex={0}
        onClick={() => setExpanded((e) => !e)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') setExpanded((v) => !v);
        }}
      >
        Details {expanded ? '▲' : '▼'}
      </span>
      {expanded && (
        <div className="tab-container">
          <ul className="tab-list">
            {TABS.map((t) => (
              <li
                key={t.key}
                className={`tab ${t.key === tab ? 'selected' : ''}`}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </li>
            ))}
          </ul>
          <div className="tab-content">
            {tab === 'details' ? (
              <DetailsTab printingId={printingId} />
            ) : (
              <ComingSoon label={TABS.find((t) => t.key === tab)!.label} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
