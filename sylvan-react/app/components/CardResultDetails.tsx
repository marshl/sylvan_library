import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router';
import { ApiError, fetchJson } from '../api';
import { useApi } from '../useApi';
import { useCurrentUser } from '../user';
import PriceChart, { type PricePoint } from './PriceChart';

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
  release_date: string | null;
  legalities: Legality[];
}

interface Ruling {
  date: string;
  text: string;
}

interface Localisation {
  id: number;
  language: string;
  card_name: string;
}

interface LocalisationSummary {
  localisation_id: number;
  language: string;
  set_code: string;
  set_name: string;
  keyrune_code: string;
  rarity: string;
  number: string | null;
}

interface OwnershipPayload {
  card_name: string;
  ownerships: (LocalisationSummary & { count: number })[];
  changes: (LocalisationSummary & { date: string; difference: number })[];
}

interface DecksPayload {
  card_count: number;
  deck_count: number;
  deck_cards: {
    deck_id: number;
    deck_name: string;
    deck_subtitle: string | null;
    date_created: string;
    count: number;
    board: string;
    board_display: string;
  }[];
}

interface CardLink {
  name: string;
  url: string;
}

interface PricesPayload {
  latest: {
    date: string;
    paper: number | null;
    paper_foil: number | null;
    mtgo: number | null;
    mtgo_foil: number | null;
  } | null;
  paper_history: { date: string; paper: number | null; paper_foil: number | null }[];
}

function pricePoints(
  history: PricesPayload['paper_history'],
  field: 'paper' | 'paper_foil',
): PricePoint[] {
  return history.flatMap((price) => {
    const value = price[field];
    return value === null ? [] : [{ date: price.date, value }];
  });
}

type TabKey =
  'details' | 'rulings' | 'languages' | 'ownership' | 'add' | 'decks' | 'links' | 'prices';

const TABS: { key: TabKey; label: string; loginRequired?: boolean }[] = [
  { key: 'details', label: 'Details' },
  { key: 'rulings', label: 'Rulings' },
  { key: 'languages', label: 'Languages' },
  { key: 'ownership', label: 'Ownership', loginRequired: true },
  { key: 'add', label: 'Add cards', loginRequired: true },
  { key: 'decks', label: 'Decks', loginRequired: true },
  { key: 'links', label: 'Links' },
  { key: 'prices', label: 'Prices' },
];

const SELECTED_TAB_KEY = 'selected_tab';

function loadSelectedTab(): TabKey {
  try {
    const saved = localStorage.getItem(SELECTED_TAB_KEY);
    if (saved && TABS.some((t) => t.key === saved)) return saved as TabKey;
  } catch {
    // storage blocked
  }
  return 'details';
}

function saveSelectedTab(tab: TabKey) {
  try {
    localStorage.setItem(SELECTED_TAB_KEY, tab);
  } catch {
    // storage blocked
  }
}

/**
 * Shows loading/error states for a tab, and its content once the data arrives
 */
function TabBody<T>({
  state,
  children,
}: {
  state: { data: T | null; loading: boolean; error: string | null };
  children: (data: T) => React.ReactNode;
}) {
  if (state.error) return <div className="error">Error: {state.error}</div>;
  if (state.loading || state.data === null) return <div className="subtitle">Loading…</div>;
  return <div className="extraDetails">{children(state.data)}</div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <span className="subtitle">
        <b>{label}: </b>
      </span>
      <span className="subtitle">{children}</span>
    </div>
  );
}

function DetailsTab({ printingId }: { printingId: number }) {
  const state = useApi<DetailsPayload>(`/api/cards/printing-details/${printingId}/`);
  return (
    <TabBody state={state}>
      {(data) => (
        <>
          {data.flavour_text && (
            <Field label="Flavour">
              <i>{data.flavour_text}</i>
            </Field>
          )}
          {data.artist && (
            <Field label="Artist">
              <Link
                to={`/search?query=${encodeURIComponent(`artist:"${data.artist.replace(/[\\"]/g, '\\$&')}"`)}`}
              >
                {data.artist}
              </Link>
            </Field>
          )}
          <Field label="Set">
            <Link to={`/search?query=${encodeURIComponent(`set:${data.set.code}`)}`}>
              {data.set.name}
            </Link>
          </Field>
          {data.release_date && <Field label="Release date">{data.release_date}</Field>}
          {data.number && (
            <Field label="Number">
              {data.number}
              {data.set.total_set_size ? `/${data.set.total_set_size}` : ''}
            </Field>
          )}
          {data.legalities.length > 0 && (
            <div>
              <div className="subtitle">
                <b>Legalities:</b>
              </div>
              {data.legalities.map((l) => (
                <div key={l.format}>
                  <span className="subtitle">{l.format}: </span>
                  <span className={`subtitle ${l.restriction.toLowerCase()}`}>{l.restriction}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </TabBody>
  );
}

function RulingsTab({ cardId }: { cardId: number }) {
  const state = useApi<Ruling[]>(`/api/cards/card/${cardId}/rulings/`);
  return (
    <TabBody state={state}>
      {(rulings) =>
        rulings.length === 0 ? (
          <span className="subtitle">No rulings!</span>
        ) : (
          rulings.map((ruling, i) => (
            <div key={i}>
              <span className="subtitle">
                <b>{ruling.date}: </b>
              </span>
              <span className="subtitle">
                <div>{ruling.text}</div>
              </span>
            </div>
          ))
        )
      }
    </TabBody>
  );
}

function LanguagesTab({ printingId }: { printingId: number }) {
  const state = useApi<Localisation[]>(`/api/cards/printing/${printingId}/languages/`);
  return (
    <TabBody state={state}>
      {(localisations) =>
        localisations.length === 0 ? (
          <span className="subtitle">No other languages!</span>
        ) : (
          localisations.map((l) => (
            <Field key={l.id} label={l.language}>
              {l.card_name}
            </Field>
          ))
        )
      }
    </TabBody>
  );
}

function localisationLabel(l: LocalisationSummary): string {
  return `${l.language} ${l.set_name} (${l.set_code}${l.number ? ` #${l.number}` : ''})`;
}

function OwnershipTab({ cardId, version }: { cardId: number; version: number }) {
  const state = useApi<OwnershipPayload>(`/api/cards/card/${cardId}/ownership/`, version);
  return (
    <TabBody state={state}>
      {(data) => (
        <>
          {data.ownerships.length > 0 ? (
            <div>
              <span className="subtitle">
                <b>You own: </b>
              </span>
              {data.ownerships.map((o) => (
                <div key={o.localisation_id}>
                  <i
                    className={`setIcon ss ss-2x ss-${o.keyrune_code} ${
                      o.set_code === 'TSB' ? 'ss-timeshifted' : `ss-${o.rarity.toLowerCase()}`
                    }`}
                  />
                  <span className="subtitle">
                    {o.count} {localisationLabel(o)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <span className="subtitle">You don't own {data.card_name}</span>
          )}
          {data.changes.length > 0 && (
            <>
              <span className="subtitle">
                <b>Changes: </b>
              </span>
              {data.changes.map((c, i) => (
                <div key={i}>
                  <span className="subtitle">
                    {c.difference > 0 ? '+' : ''}
                    {c.difference} {new Date(c.date).toLocaleString()} {localisationLabel(c)}
                  </span>
                </div>
              ))}
            </>
          )}
        </>
      )}
    </TabBody>
  );
}

function AddCardsTab({
  printingId,
  printingLabel,
  onChanged,
}: {
  printingId: number;
  printingLabel: string;
  onChanged: () => void;
}) {
  const state = useApi<Localisation[]>(`/api/cards/printing/${printingId}/languages/`);
  const [count, setCount] = useState('');
  const [localisationId, setLocalisationId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const countInput = useRef<HTMLInputElement>(null);

  // The languages endpoint puts English first, which is what people add most
  const localisations = state.data ?? [];
  const selectedId = localisationId ?? localisations[0]?.id ?? null;

  useEffect(() => {
    setLocalisationId(null);
    setMessage(null);
  }, [printingId]);

  useEffect(() => {
    if (state.data) countInput.current?.focus();
  }, [state.data]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const change = Number(count);
    if (!Number.isInteger(change) || change === 0 || selectedId === null) return;
    setSubmitting(true);
    setMessage(null);
    try {
      await fetchJson('/api/cards/ownership-changes/', {
        method: 'POST',
        body: { count: change, localisation: selectedId },
      });
      setCount('');
      setMessage(`${change > 0 ? 'Added' : 'Removed'} ${Math.abs(change)}`);
      onChanged();
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
      countInput.current?.focus();
    }
  }

  return (
    <TabBody state={state}>
      {() => (
        <form onSubmit={onSubmit}>
          <p>Add to {printingLabel}</p>
          <span className="text-input add-card-count-input">
            <input
              ref={countInput}
              type="number"
              step={1}
              value={count}
              onChange={(e) => setCount(e.target.value)}
              disabled={submitting}
              aria-label="Number of cards to add (negative to remove)"
            />
          </span>
          <span className="select-group">
            <select
              value={selectedId ?? ''}
              onChange={(e) => setLocalisationId(Number(e.target.value))}
              disabled={submitting}
              aria-label="Language"
            >
              {localisations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.language}
                </option>
              ))}
            </select>
          </span>
          <input type="submit" className="action-button" value="Submit" disabled={submitting} />
          {message && <span className="subtitle"> {message}</span>}
        </form>
      )}
    </TabBody>
  );
}

function DecksTab({ cardId, version }: { cardId: number; version: number }) {
  const state = useApi<DecksPayload>(`/api/cards/card/${cardId}/decks/`, version);
  return (
    <TabBody state={state}>
      {(data) =>
        data.deck_cards.length === 0 ? (
          <span className="subtitle">You have never used this card in a deck</span>
        ) : (
          <>
            {data.card_count} used in {data.deck_count} decks
            {data.deck_cards.map((dc, i) => (
              <div key={i}>
                <span className="subtitle">
                  {dc.count}x in{' '}
                  <Link
                    to={`/decks/${dc.deck_id}`}
                    target="_blank"
                    rel="noopener"
                    className="card-link"
                  >
                    {dc.deck_name} {dc.deck_subtitle ?? ''} ({dc.date_created})
                    {dc.board !== 'main' && <em> ({dc.board_display}board)</em>}
                  </Link>
                </span>
              </div>
            ))}
          </>
        )
      }
    </TabBody>
  );
}

function LinksTab({ cardId }: { cardId: number }) {
  const state = useApi<CardLink[]>(`/api/cards/card/${cardId}/links/`);
  return (
    <TabBody state={state}>
      {(links) =>
        links.map((link) => (
          <div key={link.url}>
            <span className="subtitle">
              <a href={link.url} target="_blank" rel="noreferrer" className="card-link">
                {link.name} <i className="fa fa-external-link" aria-hidden="true" />
              </a>
            </span>
          </div>
        ))
      }
    </TabBody>
  );
}

function formatPrice(value: number | null): string {
  return value === null ? '–' : `$${value.toFixed(2)}`;
}

function PricesTab({ printingId }: { printingId: number }) {
  const state = useApi<PricesPayload>(`/api/cards/printing/${printingId}/prices/`);
  return (
    <TabBody state={state}>
      {(data) =>
        data.latest === null ? (
          <span className="subtitle">No price data for this printing</span>
        ) : (
          <>
            <span className="subtitle">
              <b>Paper: </b> {formatPrice(data.latest.paper)}
            </span>{' '}
            <span className="subtitle">
              <b>Paper Foil: </b> {formatPrice(data.latest.paper_foil)}
            </span>{' '}
            <span className="subtitle">
              <b>MTGO: </b> {formatPrice(data.latest.mtgo)}
            </span>{' '}
            <span className="subtitle">
              <b>MTGO Foil: </b> {formatPrice(data.latest.mtgo_foil)}
            </span>
            {data.paper_history.length > 0 && (
              <PriceChart
                title="Paper price"
                series={[
                  {
                    key: 'paper',
                    label: 'Non-foil',
                    points: pricePoints(data.paper_history, 'paper'),
                  },
                  {
                    key: 'paper_foil',
                    label: 'Foil',
                    points: pricePoints(data.paper_history, 'paper_foil'),
                  },
                ]}
              />
            )}
          </>
        )
      }
    </TabBody>
  );
}

export default function CardResultDetails({
  cardId,
  printingId,
  printingLabel,
  expanded,
  onExpand,
  ownershipVersion,
  onOwnershipChanged,
}: {
  cardId: number;
  printingId: number;
  // e.g. "Limited Edition Alpha (#161)", shown on the Add cards form
  printingLabel: string;
  expanded: boolean;
  onExpand: () => void;
  ownershipVersion: number;
  onOwnershipChanged: () => void;
}) {
  const { user } = useCurrentUser();
  const [tab, setTab] = useState<TabKey>(loadSelectedTab);
  // Every result is on the page from the start, so expanding one picks up the tab
  // last chosen on any of the others
  const [wasExpanded, setWasExpanded] = useState(expanded);
  if (expanded !== wasExpanded) {
    setWasExpanded(expanded);
    if (expanded) setTab(loadSelectedTab());
  }
  const tabs = TABS.filter((t) => !t.loginRequired || user?.is_authenticated);
  const activeTab = tabs.some((t) => t.key === tab) ? tab : 'details';

  function selectTab(key: TabKey) {
    setTab(key);
    saveSelectedTab(key);
  }

  if (!expanded) {
    return (
      <div className="search-result-tab-container">
        <span
          className="tab-expander"
          role="button"
          tabIndex={0}
          onClick={onExpand}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onExpand();
          }}
        >
          Details ▼
        </span>
      </div>
    );
  }

  return (
    <div className="search-result-tab-container">
      <div className="tab-container">
        <ul className="tab-list" role="tablist">
          {tabs.map((t) => (
            <li
              key={t.key}
              role="tab"
              aria-selected={t.key === activeTab}
              tabIndex={0}
              className={`tab ${t.key === activeTab ? 'selected' : ''}`}
              onClick={() => selectTab(t.key)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') selectTab(t.key);
              }}
            >
              {t.label}
            </li>
          ))}
        </ul>
        <div className="tab-content" role="tabpanel">
          {activeTab === 'details' && <DetailsTab printingId={printingId} />}
          {activeTab === 'rulings' && <RulingsTab cardId={cardId} />}
          {activeTab === 'languages' && <LanguagesTab printingId={printingId} />}
          {activeTab === 'ownership' && <OwnershipTab cardId={cardId} version={ownershipVersion} />}
          {activeTab === 'add' && (
            <AddCardsTab
              printingId={printingId}
              printingLabel={printingLabel}
              onChanged={onOwnershipChanged}
            />
          )}
          {activeTab === 'decks' && <DecksTab cardId={cardId} version={ownershipVersion} />}
          {activeTab === 'links' && <LinksTab cardId={cardId} />}
          {activeTab === 'prices' && <PricesTab printingId={printingId} />}
        </div>
      </div>
    </div>
  );
}
