import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { ApiError, fetchJson } from '../api';
import type { BoardKey, DeckDetail } from '../types';
import { useApi } from '../useApi';

interface DeckOptions {
  formats: { value: string; label: string }[];
  colours: { id: number; name: string; symbol: string }[];
}

interface DeckFormState {
  name: string;
  subtitle: string;
  format: string;
  date_created: string;
  description: string;
  exclude_colours: number[];
  is_prototype: boolean;
  is_private: boolean;
  boards: Record<BoardKey, string>;
}

const BOARDS: { key: BoardKey; label: string }[] = [
  { key: 'main', label: 'Main' },
  { key: 'side', label: 'Side' },
  { key: 'maybe', label: 'Maybe' },
  { key: 'acquire', label: 'Acquire' },
];

function today(): string {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function emptyDeck(): DeckFormState {
  return {
    name: '',
    subtitle: '',
    format: '',
    date_created: today(),
    description: '',
    exclude_colours: [],
    is_prototype: false,
    is_private: false,
    boards: { main: '', side: '', maybe: '', acquire: '' },
  };
}

function fromDeck(deck: DeckDetail): DeckFormState {
  return {
    name: deck.name,
    subtitle: deck.subtitle ?? '',
    format: deck.format,
    date_created: deck.date_created,
    description: deck.description ?? '',
    exclude_colours: deck.exclude_colours,
    is_prototype: deck.is_prototype,
    is_private: deck.is_private,
    boards: deck.boards,
  };
}

/**
 * DRF validation errors as a flat list of messages, prefixed with the field they're for
 */
function errorMessages(err: unknown): string[] {
  if (!(err instanceof ApiError)) return [(err as Error).message];
  if (!err.body || typeof err.body !== 'object') return [err.message];
  return Object.entries(err.body as Record<string, unknown>).flatMap(([field, messages]) => {
    const list = Array.isArray(messages) ? messages : [messages];
    const prefix = field === 'cards' || field === 'non_field_errors' || field === 'detail' ? '' : `${field}: `;
    return list.map((m) => `${prefix}${typeof m === 'string' ? m : JSON.stringify(m)}`);
  });
}

function CardNameInput({
  value,
  onChange,
  inputRef,
}: {
  value: string;
  onChange: (value: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}) {
  const [names, setNames] = useState<string[]>([]);

  useEffect(() => {
    if (value.trim().length < 2) {
      setNames([]);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetchJson<string[]>(`/api/cards/card-names/?${new URLSearchParams({ q: value })}`, {
        signal: controller.signal,
      })
        .then(setNames)
        .catch(() => {});
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value]);

  return (
    <>
      <input
        id="card-input"
        ref={inputRef}
        list="card-name-options"
        autoComplete="off"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <datalist id="card-name-options">
        {names.map((name) => (
          <option key={name} value={name} />
        ))}
      </datalist>
    </>
  );
}

function DeckForm({ deckId, initial }: { deckId: number | null; initial: DeckFormState }) {
  const navigate = useNavigate();
  const options = useApi<DeckOptions>('/api/cards/deck-options/');
  const [form, setForm] = useState<DeckFormState>(initial);
  const [board, setBoard] = useState<BoardKey>('main');
  const [cardName, setCardName] = useState('');
  const [quantity, setQuantity] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [skipValidation, setSkipValidation] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const cardInput = useRef<HTMLInputElement>(null);

  function update<K extends keyof DeckFormState>(key: K, value: DeckFormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
    setSavedMessage(null);
  }

  function addCardToBoard() {
    const name = cardName.trim();
    if (!name) return;
    const line = `${Number(quantity) > 0 ? Number(quantity) : 1}x ${name}`;
    const current = form.boards[board];
    update('boards', { ...form.boards, [board]: current ? `${current.replace(/\n+$/, '')}\n${line}` : line });
    setCardName('');
    cardInput.current?.focus();
  }

  function toggleExcludedColour(id: number) {
    update(
      'exclude_colours',
      form.exclude_colours.includes(id)
        ? form.exclude_colours.filter((c) => c !== id)
        : [...form.exclude_colours, id],
    );
  }

  async function save(continueEditing: boolean) {
    setSaving(true);
    setErrors([]);
    setSavedMessage(null);
    try {
      const { id } = await fetchJson<{ id: number }>(
        deckId === null ? '/api/cards/deck/' : `/api/cards/deck/${deckId}/`,
        {
          method: deckId === null ? 'POST' : 'PUT',
          body: { ...form, skip_validation: skipValidation },
        },
      );
      setSkipValidation(false);
      if (!continueEditing) {
        navigate(`/decks/${id}`);
      } else if (deckId === null) {
        navigate(`/decks/${id}/edit`, { replace: true });
      } else {
        setSavedMessage('Saved');
      }
    } catch (err) {
      setErrors(errorMessages(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save(false);
      }}
    >
      <div className="group-container">
        <div className="row">
          <div className="field-container">
            <label htmlFor="deck-name">Name</label>
            <input
              id="deck-name"
              required
              value={form.name}
              onChange={(e) => update('name', e.target.value)}
            />
          </div>
          <div className="field-container">
            <label htmlFor="deck-subtitle">Subtitle</label>
            <input
              id="deck-subtitle"
              value={form.subtitle}
              onChange={(e) => update('subtitle', e.target.value)}
            />
          </div>
          <div className="field-container">
            <label htmlFor="deck-format">Format</label>
            <select
              id="deck-format"
              required
              value={form.format}
              onChange={(e) => update('format', e.target.value)}
            >
              <option value="" disabled>
                Choose a format
              </option>
              {options.data?.formats.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field-container">
            <label htmlFor="deck-date">Date created</label>
            <input
              id="deck-date"
              type="date"
              required
              value={form.date_created}
              onChange={(e) => update('date_created', e.target.value)}
            />
          </div>
        </div>
        <div className="row">
          <div className="field-container">
            <label htmlFor="deck-description">Description (HTML)</label>
            <textarea
              id="deck-description"
              rows={5}
              value={form.description}
              onChange={(e) => update('description', e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="group-container">
        <div className="row">
          <div className="column">
            <div className="row">
              <div className="field-container">
                <label htmlFor="card-input">Card</label>
                <CardNameInput value={cardName} onChange={setCardName} inputRef={cardInput} />
              </div>
            </div>
            <div className="row">
              <div className="field-container">
                <label htmlFor="card-quantity">Quantity</label>
                <input
                  id="card-quantity"
                  type="number"
                  min={1}
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>
            </div>
            <div className="row">
              <button type="button" onClick={addCardToBoard}>
                Add card to {BOARDS.find((b) => b.key === board)!.label.toLowerCase()} board &gt;&gt;
              </button>
            </div>
          </div>
          <div className="column">
            <div className="field-container">
              <div className="search-result-tab-container">
                <div className="tab-container">
                  <ul className="tab-list" role="tablist">
                    {BOARDS.map((b) => (
                      <li
                        key={b.key}
                        role="tab"
                        tabIndex={0}
                        aria-selected={b.key === board}
                        className={`tab ${b.key === board ? 'selected' : ''}`}
                        onClick={() => setBoard(b.key)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') setBoard(b.key);
                        }}
                      >
                        {b.label}
                      </li>
                    ))}
                  </ul>
                  <textarea
                    aria-label={`${board} board`}
                    rows={20}
                    value={form.boards[board]}
                    onChange={(e) => update('boards', { ...form.boards, [board]: e.target.value })}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="group-container">
        <div className="row">
          <div className="field-container">
            <label>Exclude colours</label>
            <div>
              {options.data?.colours.map((colour) => (
                <label key={colour.id} style={{ marginRight: 12, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={form.exclude_colours.includes(colour.id)}
                    onChange={() => toggleExcludedColour(colour.id)}
                  />{' '}
                  <i className={`ms ms-${colour.symbol.toLowerCase()} ms-cost`} /> {colour.name}
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="group-container">
        <div className="row">
          <div className="field-container" style={{ flexDirection: 'row' }}>
            <label htmlFor="deck-prototype">Prototype</label>
            <input
              id="deck-prototype"
              type="checkbox"
              checked={form.is_prototype}
              onChange={(e) => update('is_prototype', e.target.checked)}
            />
          </div>
          <div className="field-container" style={{ flexDirection: 'row' }}>
            <label htmlFor="deck-private">Private</label>
            <input
              id="deck-private"
              type="checkbox"
              checked={form.is_private}
              onChange={(e) => update('is_private', e.target.checked)}
            />
          </div>
        </div>
      </div>

      {errors.length > 0 && (
        <div className="group-container" role="alert">
          {errors.map((error, i) => (
            <div key={i}>
              <strong>{error}</strong>
            </div>
          ))}
          <label htmlFor="skip-validation">Skip format validation</label>{' '}
          <input
            id="skip-validation"
            type="checkbox"
            checked={skipValidation}
            onChange={(e) => setSkipValidation(e.target.checked)}
          />
        </div>
      )}

      <div className="group-container">
        <div className="row" style={{ gap: 8, alignItems: 'center' }}>
          <input type="submit" value="Save" disabled={saving} />
          <input
            type="button"
            value="Save & Continue"
            disabled={saving}
            onClick={() => save(true)}
          />
          <Link to={deckId === null ? '/decks' : `/decks/${deckId}`}>Cancel</Link>
          {savedMessage && <span className="subtitle">{savedMessage}</span>}
        </div>
      </div>
    </form>
  );
}

export default function DeckEdit({ deckId }: { deckId: number | null }) {
  const existing = useApi<DeckDetail>(deckId === null ? null : `/api/cards/deck/${deckId}/`);

  if (deckId === null) {
    return (
      <div className="main-content">
        <title>New deck — Sylvan Library</title>
        <DeckForm deckId={null} initial={emptyDeck()} />
      </div>
    );
  }
  if (existing.error) return <div className="error">Error: {existing.error}</div>;
  if (!existing.data) return <div>Loading...</div>;
  return (
    <div className="main-content">
      <title>{`Edit ${existing.data.name || 'deck'} — Sylvan Library`}</title>
      {/* Keyed so saving a new deck and moving to its edit URL starts from the saved deck */}
      <DeckForm key={deckId} deckId={deckId} initial={fromDeck(existing.data)} />
    </div>
  );
}
