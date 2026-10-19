import React from 'react';
import { Form, Link, useSearchParams } from 'react-router';
import { loginUrl, logout, useCurrentUser } from '../user';

export default function TopBar() {
  const { user } = useCurrentUser();
  const [searchParams] = useSearchParams();

  return (
    <div className="top-bar">
      <div className="top-bar-content">
        <Link to="/" className="action-button">
          Sylvan Library
        </Link>
        <div className="header-search-container">
          <Form action="/search" method="get">
            <input
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
