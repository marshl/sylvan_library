import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { ApiError, fetchJson } from './api';
import type { BoardKey } from './types';
import { useCurrentUser } from './user';

/**
 * The deck being built from the search page: its board sizes, and how many of each card
 * are in each board, keyed by card ID
 */
export interface BuildingDeck {
  id: number;
  name: string;
  is_prototype: boolean;
  board_counts: Record<BoardKey, number>;
  cards: Record<string, Partial<Record<BoardKey, number>>>;
}

interface BuildingDeckState {
  deck: BuildingDeck | null;
  start: (deckId: number) => Promise<void>;
  stop: () => void;
  // Adds copies of a card to a board, or takes them out with a negative change
  changeCard: (cardId: number, board: BoardKey, change: number) => Promise<void>;
  error: string | null;
}

// Remembered in this browser only, so building carries on across page loads
const STORAGE_KEY = 'building-deck-id';

function storedDeckId(): number | null {
  try {
    const value = Number(localStorage.getItem(STORAGE_KEY));
    return value > 0 ? value : null;
  } catch {
    return null;
  }
}

function storeDeckId(deckId: number | null) {
  try {
    if (deckId === null) localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, String(deckId));
  } catch {
    // Building still works until the page is reloaded
  }
}

const BuildingDeckContext = createContext<BuildingDeckState>({
  deck: null,
  start: async () => {},
  stop: () => {},
  changeCard: async () => {},
  error: null,
});

export function BuildingDeckProvider({ children }: { children: React.ReactNode }) {
  const { user } = useCurrentUser();
  const [deckId, setDeckId] = useState<number | null>(storedDeckId);
  const [deck, setDeck] = useState<BuildingDeck | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stop = useCallback(() => {
    storeDeckId(null);
    setDeckId(null);
    setDeck(null);
    setError(null);
  }, []);

  const load = useCallback(
    async (id: number) => {
      try {
        setDeck(await fetchJson<BuildingDeck>(`/api/cards/deck/${id}/card-counts/`));
      } catch (err) {
        // The deck has been deleted, or belongs to someone else
        if (err instanceof ApiError && err.status === 404) stop();
      }
    },
    [stop],
  );

  // Loaded once the user is known, and again whenever the window gets focus, in case the
  // deck was changed in another tab
  const loggedIn = user?.is_authenticated ?? false;
  useEffect(() => {
    if (deckId === null || !loggedIn) return;
    load(deckId);
    const onFocus = () => load(deckId);
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [deckId, loggedIn, load]);

  const start = useCallback(
    async (id: number) => {
      storeDeckId(id);
      setDeckId(id);
      setError(null);
      await load(id);
    },
    [load],
  );

  const changeCard = useCallback(
    async (cardId: number, board: BoardKey, change: number) => {
      if (deckId === null) return;
      try {
        setDeck(
          await fetchJson<BuildingDeck>(`/api/cards/deck/${deckId}/cards/`, {
            method: 'POST',
            body: { card: cardId, board, change },
          }),
        );
        setError(null);
      } catch (err) {
        const body = err instanceof ApiError ? (err.body as { card?: string[] } | null) : null;
        setError(body?.card?.join(' ') ?? (err as Error).message);
      }
    },
    [deckId],
  );

  return (
    <BuildingDeckContext.Provider
      value={{ deck: loggedIn ? deck : null, start, stop, changeCard, error }}
    >
      {children}
    </BuildingDeckContext.Provider>
  );
}

export function useBuildingDeck(): BuildingDeckState {
  return useContext(BuildingDeckContext);
}
