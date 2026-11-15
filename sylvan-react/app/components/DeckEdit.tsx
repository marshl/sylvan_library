import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Link, useBlocker, useNavigate } from 'react-router';
import { ApiError, fetchJson, isAbortError } from '../api';
import { descriptionHtml } from '../html';
import type { BoardKey, DeckDetail } from '../types';
import { useApi } from '../useApi';
import BoardTextInput from './BoardTextInput';
import RichTextEditor from './RichTextEditor';

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

/**
 * A line of board text that couldn't be read, or that was read as a card with a
 * different name to what was typed
 */
interface LineIssue {
  line: number;
  error?: string;
  matched?: string;
}

interface DeckCheck {
  boards: Record<BoardKey, { count: number; issues: LineIssue[] }>;
  format_errors: string[];
}

const BOARDS: { key: BoardKey; label: string }[] = [
  { key: 'main', label: 'Main' },
  { key: 'side', label: 'Side' },
  { key: 'maybe', label: 'Maybe' },
  { key: 'acquire', label: 'Acquire' },
];

const SAVE_SHORTCUT = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘S' : 'Ctrl+S';

// How long typing has to pause before the deck text is checked
const CHECK_DELAY_MS = 500;

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
    description: descriptionHtml(deck.description ?? ''),
    exclude_colours: deck.exclude_colours,
    is_prototype: deck.is_prototype,
    is_private: deck.is_private,
    boards: deck.boards,
  };
}

/**
 * DRF validation errors as a flat list of messages, prefixed with the field they're for,
 * e.g. "date_created" becomes "Date created: "
 */
function errorMessages(err: unknown): string[] {
  if (!(err instanceof ApiError)) return [(err as Error).message];
  if (!err.body || typeof err.body !== 'object') return [err.message];
  return Object.entries(err.body as Record<string, unknown>).flatMap(([field, messages]) => {
    const list = Array.isArray(messages) ? messages : [messages];
    const label = field.replace(/_/g, ' ');
    const prefix =
      field === 'cards' || field === 'non_field_errors' || field === 'detail'
        ? ''
        : `${label.charAt(0).toUpperCase()}${label.slice(1)}: `;
    return list.map((m) => `${prefix}${typeof m === 'string' ? m : JSON.stringify(m)}`);
  });
}

/**
 * Checks the deck's card text on the server a moment after it stops changing. The
 * last result is kept while the next check runs, so the counts don't flicker.
 */
function useDeckCheck(boards: Record<BoardKey, string>, format: string) {
  const [check, setCheck] = useState<DeckCheck | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setChecking(true);
    const timer = setTimeout(() => {
      fetchJson<DeckCheck>('/api/cards/deck/check/', {
        method: 'POST',
        body: { boards, format },
        signal: controller.signal,
      })
        .then((result) => {
          setCheck(result);
          setError(null);
          setChecking(false);
        })
        .catch((err) => {
          if (isAbortError(err)) return;
          setError(errorMessages(err).join(' '));
          setChecking(false);
        });
    }, CHECK_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [boards, format]);

  return { check, checking, error };
}

/**
 * The problem lines in the current board, each of which selects its line when clicked
 */
function BoardIssues({
  issues,
  onSelectLine,
}: {
  issues: LineIssue[];
  onSelectLine: (line: number) => void;
}) {
  if (issues.length === 0) return null;
  return (
    <ul className="deck-line-issues">
      {issues.map((issue) => (
        <li key={issue.line} className={issue.error ? 'line-error' : 'line-matched'}>
          <button type="button" className="link-button" onClick={() => onSelectLine(issue.line)}>
            Line {issue.line}
          </button>
          : {issue.error ?? `read as ${issue.matched}`}
        </li>
      ))}
    </ul>
  );
}

/**
 * Whether the deck's cards follow its format's rules, as of the last check
 */
function FormatStatus({
  check,
  checkError,
  formatLabel,
  isPrototype,
}: {
  check: DeckCheck | null;
  checkError: string | null;
  formatLabel: string | null;
  isPrototype: boolean;
}) {
  if (checkError) {
    return (
      <div className="deck-check-status line-error">Couldn't check the deck: {checkError}</div>
    );
  }
  if (!check || !formatLabel) return null;
  const hasLineErrors = Object.values(check.boards).some((b) =>
    b.issues.some((issue) => issue.error),
  );
  if (check.format_errors.length > 0) {
    return (
      <div className="deck-check-status">
        {check.format_errors.map((error) => (
          <div key={error} className="line-error">
            {error}
          </div>
        ))}
        {isPrototype && (
          <div className="subtitle">Prototypes are saved without checking the format rules</div>
        )}
      </div>
    );
  }
  if (hasLineErrors) return null;
  return <div className="deck-check-status format-ok">Follows the {formatLabel} rules</div>;
}

/**
 * Deletes the deck after a second click to confirm
 */
function DeleteDeckButton({
  deckId,
  disabled,
  onDeleted,
  onError,
}: {
  deckId: number;
  disabled: boolean;
  onDeleted: () => void;
  onError: (messages: string[]) => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function deleteDeck() {
    setDeleting(true);
    try {
      await fetchJson(`/api/cards/deck/${deckId}/`, { method: 'DELETE' });
      onDeleted();
    } catch (err) {
      onError(errorMessages(err));
      setDeleting(false);
      setConfirming(false);
    }
  }

  if (!confirming) {
    return (
      <button
        type="button"
        className="action-button danger"
        disabled={disabled}
        onClick={() => setConfirming(true)}
      >
        Delete deck
      </button>
    );
  }
  return (
    <span className="subtitle delete-confirm">
      Delete this deck for good?
      <button
        type="button"
        className="action-button danger"
        disabled={deleting}
        onClick={deleteDeck}
        autoFocus
      >
        {deleting ? 'Deleting…' : 'Yes, delete it'}
      </button>
      <button
        type="button"
        className="action-button secondary"
        disabled={deleting}
        onClick={() => setConfirming(false)}
      >
        Keep it
      </button>
    </span>
  );
}

function DeckForm({ deckId, initial }: { deckId: number | null; initial: DeckFormState }) {
  const navigate = useNavigate();
  const options = useApi<DeckOptions>('/api/cards/deck-options/');
  const [form, setForm] = useState<DeckFormState>(initial);
  const [savedForm, setSavedForm] = useState<DeckFormState>(initial);
  const [board, setBoard] = useState<BoardKey>('main');
  const [errors, setErrors] = useState<string[]>([]);
  const [skipValidation, setSkipValidation] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const boardInput = useRef<HTMLTextAreaElement>(null);
  // Set just before leaving the page on purpose (after saving or deleting), so leaving
  // isn't stopped by the unsaved changes prompt
  const leaving = useRef(false);

  const { check, checking, error: checkError } = useDeckCheck(form.boards, form.format);
  const dirty = JSON.stringify(form) !== JSON.stringify(savedForm);
  const formatLabel = options.data?.formats.find((f) => f.value === form.format)?.label ?? null;

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      dirty && !leaving.current && currentLocation.pathname !== nextLocation.pathname,
  );

  useEffect(() => {
    if (!dirty) return;
    function warnBeforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault();
      e.returnValue = '';
    }
    window.addEventListener('beforeunload', warnBeforeUnload);
    return () => window.removeEventListener('beforeunload', warnBeforeUnload);
  }, [dirty]);

  // Ctrl+S (or Cmd+S) saves and keeps editing
  const saveRef = useRef(save);
  saveRef.current = save;
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        saveRef.current(true);
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // The board text box grows to fit its text instead of scrolling inside the page
  const boardText = form.boards[board];
  useLayoutEffect(() => {
    const textarea = boardInput.current;
    if (!textarea) return;
    // Shrinking the box to measure it can move the page, so the scroll is put back
    const scrollY = window.scrollY;
    textarea.style.height = 'auto';
    const borders = textarea.offsetHeight - textarea.clientHeight;
    textarea.style.height = `${textarea.scrollHeight + borders}px`;
    window.scrollTo({ top: scrollY });
  }, [boardText]);

  function update<K extends keyof DeckFormState>(key: K, value: DeckFormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
    setSavedMessage(null);
  }

  /**
   * Selects a line of the board text and scrolls it into the middle of the window
   */
  function selectLine(lineNumber: number) {
    const textarea = boardInput.current;
    if (!textarea) return;
    const lines = textarea.value.split('\n');
    const start = lines.slice(0, lineNumber - 1).reduce((total, l) => total + l.length + 1, 0);
    textarea.focus({ preventScroll: true });
    textarea.setSelectionRange(start, start + (lines[lineNumber - 1]?.length ?? 0));
    const style = getComputedStyle(textarea);
    const lineHeight = parseFloat(style.lineHeight) || parseFloat(style.fontSize) * 1.2;
    const lineTop =
      textarea.getBoundingClientRect().top +
      window.scrollY +
      parseFloat(style.paddingTop) +
      (lineNumber - 1) * lineHeight;
    window.scrollTo({ top: lineTop - window.innerHeight / 2, behavior: 'smooth' });
  }

  function toggleExcludedColour(id: number) {
    update(
      'exclude_colours',
      form.exclude_colours.includes(id)
        ? form.exclude_colours.filter((c) => c !== id)
        : [...form.exclude_colours, id],
    );
  }

  function leave(to: string, replace = false) {
    leaving.current = true;
    navigate(to, { replace });
  }

  async function save(continueEditing: boolean) {
    if (saving) return;
    const sent = form;
    setSaving(true);
    setErrors([]);
    setSavedMessage(null);
    try {
      const { id } = await fetchJson<{ id: number }>(
        deckId === null ? '/api/cards/deck/' : `/api/cards/deck/${deckId}/`,
        {
          method: deckId === null ? 'POST' : 'PUT',
          body: { ...sent, skip_validation: skipValidation },
        },
      );
      setSkipValidation(false);
      setSavedForm(sent);
      if (!continueEditing) {
        leave(`/decks/${id}`);
      } else if (deckId === null) {
        leave(`/decks/${id}/edit`, true);
      } else {
        setSavedMessage('Saved');
      }
    } catch (err) {
      setErrors(errorMessages(err));
    } finally {
      setSaving(false);
    }
  }

  const settingsSummary = [
    form.is_prototype && 'Prototype',
    form.is_private && 'Private',
    form.exclude_colours.length > 0 &&
      `Excludes ${(options.data?.colours ?? [])
        .filter((c) => form.exclude_colours.includes(c.id))
        .map((c) => c.name.toLowerCase())
        .join(', ')}`,
  ].filter(Boolean);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save(true);
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
            <label id="deck-description-label">Description</label>
            <RichTextEditor
              labelId="deck-description-label"
              initialValue={initial.description}
              onChange={(html) => update('description', html)}
            />
          </div>
        </div>
      </div>

      <div className="group-container">
        <div className="tab-container">
          <ul className="tab-list" role="tablist">
            {BOARDS.map((b) => {
              const boardCheck = check?.boards[b.key];
              const errorCount = boardCheck?.issues.filter((i) => i.error).length ?? 0;
              return (
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
                  {boardCheck && <span className="tab-count"> {boardCheck.count}</span>}
                  {errorCount > 0 && (
                    <span
                      className="tab-problems"
                      title={`${errorCount} line${errorCount === 1 ? '' : 's'} can't be read`}
                    >
                      {' '}
                      ⚠ {errorCount}
                    </span>
                  )}
                </li>
              );
            })}
            {checking && (
              <li role="presentation" className="deck-checking subtitle">
                Checking…
              </li>
            )}
          </ul>
          <FormatStatus
            check={check}
            checkError={checkError}
            formatLabel={formatLabel}
            isPrototype={form.is_prototype}
          />
          <BoardIssues issues={check?.boards[board].issues ?? []} onSelectLine={selectLine} />
          <BoardTextInput
            key={board}
            textareaRef={boardInput}
            className="board-text"
            ariaLabel={`${board} board`}
            rows={20}
            value={boardText}
            onChange={(text) => update('boards', { ...form.boards, [board]: text })}
          />
        </div>
      </div>

      <div className="group-container">
        <details className="deck-settings">
          <summary>
            Deck settings
            {settingsSummary.length > 0 && (
              <span className="subtitle"> — {settingsSummary.join(' · ')}</span>
            )}
          </summary>
          <div className="row">
            <div className="field-container">
              <label>Exclude colours</label>
              <div>
                {options.data?.colours.map((colour) => (
                  <label key={colour.id} className="exclude-colour">
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
          <div className="row">
            <div className="field-container checkbox-field">
              <label htmlFor="deck-prototype">Prototype</label>
              <input
                id="deck-prototype"
                type="checkbox"
                checked={form.is_prototype}
                onChange={(e) => update('is_prototype', e.target.checked)}
              />
            </div>
            <div className="field-container checkbox-field">
              <label htmlFor="deck-private">Private</label>
              <input
                id="deck-private"
                type="checkbox"
                checked={form.is_private}
                onChange={(e) => update('is_private', e.target.checked)}
              />
            </div>
          </div>
        </details>
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

      <div className="group-container deck-save-bar">
        {blocker.state === 'blocked' ? (
          <div className="deck-save-row" role="alertdialog" aria-label="Unsaved changes">
            <span className="unsaved-changes">This deck has unsaved changes.</span>
            <button
              type="button"
              className="action-button"
              onClick={() => blocker.reset()}
              autoFocus
            >
              Stay
            </button>
            <button
              type="button"
              className="action-button danger"
              onClick={() => blocker.proceed()}
            >
              Leave without saving
            </button>
          </div>
        ) : (
          <div className="deck-save-row">
            <button type="submit" className="action-button primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save'} <kbd>{SAVE_SHORTCUT}</kbd>
            </button>
            <button
              type="button"
              className="action-button"
              disabled={saving}
              onClick={() => save(false)}
            >
              Save &amp; view deck
            </button>
            <Link
              className="action-button secondary"
              to={deckId === null ? '/decks' : `/decks/${deckId}`}
            >
              Cancel
            </Link>
            {dirty ? (
              <span className="subtitle unsaved-changes">Unsaved changes</span>
            ) : (
              savedMessage && <span className="subtitle">{savedMessage}</span>
            )}
            {deckId !== null && (
              <span className="deck-delete">
                <DeleteDeckButton
                  deckId={deckId}
                  disabled={saving}
                  onDeleted={() => leave('/decks')}
                  onError={setErrors}
                />
              </span>
            )}
          </div>
        )}
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
