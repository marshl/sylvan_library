import React, { createContext, useContext, useEffect, useState } from 'react';
import { fetchJson } from './api';

export interface CurrentUser {
  is_authenticated: boolean;
  username: string | null;
}

interface UserState {
  user: CurrentUser | null;
  loading: boolean;
}

const UserContext = createContext<UserState>({ user: null, loading: true });

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<UserState>({ user: null, loading: true });

  useEffect(() => {
    fetchJson<CurrentUser>('/api/me/')
      .then((user) => setState({ user, loading: false }))
      .catch(() =>
        setState({
          user: { is_authenticated: false, username: null },
          loading: false,
        }),
      );
  }, []);

  return <UserContext.Provider value={state}>{children}</UserContext.Provider>;
}

export function useCurrentUser(): UserState {
  return useContext(UserContext);
}

/**
 * Django's login page, sending the user back to where they were afterwards
 */
export function loginUrl(): string {
  const next = window.location.pathname + window.location.search;
  return `/api-auth/login/?next=${encodeURIComponent(next)}`;
}

export async function logout(): Promise<void> {
  // Django only accepts a POST for logout; it responds with a redirect we
  // don't need to follow
  await fetchJson('/api-auth/logout/', { method: 'POST' }).catch(() => {});
  window.location.reload();
}
