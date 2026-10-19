import React, { useEffect, useRef } from 'react';
import { Form, Link, useSearchParams } from 'react-router';
import { isTypingTarget } from '../keyboard';
import { loginUrl, logout, useCurrentUser } from '../user';

export default function TopBar() {
  const { user } = useCurrentUser();
  const [searchParams] = useSearchParams();
  const searchInput = useRef<HTMLInputElement>(null);

  // Pressing f jumps to the search box, unless the user is typing somewhere else
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== 'f' || e.ctrlKey || e.metaKey || e.altKey || isTypingTarget(e.target)) return;
      searchInput.current?.focus();
      e.preventDefault();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);

  return (
    <div className="top-bar">
      <div className="top-bar-content">
        <Link to="/" className="action-button">
          Sylvan Library
        </Link>
        <div className="header-search-container">
          <Form action="/search" method="get">
            <input
              ref={searchInput}
              type="text"
              name="query"
              className="search-input"
              placeholder="Search for a card..."
              key={searchParams.get('query') ?? ''}
              defaultValue={searchParams.get('query') ?? ''}
              onFocus={(e) => e.currentTarget.select()}
            />
          </Form>
        </div>
        <Link to="/sets" className="action-button">
          All Sets
        </Link>
        {user?.is_authenticated ? (
          <>
            <Link to="/decks" className="action-button">
              Decks
            </Link>
            <span className="action-button profile-button">{user.username}</span>
            <button type="button" className="action-button" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          user && (
            <a href={loginUrl()} className="action-button">
              Login
            </a>
          )
        )}
      </div>
    </div>
  );
}
