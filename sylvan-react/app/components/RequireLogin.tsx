import React from 'react';
import { loginUrl, useCurrentUser } from '../user';

/**
 * Shows a login link instead of the children for anonymous users
 */
export default function RequireLogin({
  what,
  children,
}: {
  // e.g. "see your decks"
  what: string;
  children: React.ReactNode;
}) {
  const { user, loading } = useCurrentUser();
  if (loading) return <div>Loading...</div>;
  if (!user?.is_authenticated) {
    return (
      <div className="main-content">
        <a href={loginUrl()}>Log in</a> to {what}.
      </div>
    );
  }
  return <>{children}</>;
}
