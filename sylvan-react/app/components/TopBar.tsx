import React from 'react';
import { Link } from 'react-router-dom';

export default function TopBar() {
  return (
    <div className="top-bar">
      <div className="top-bar-content">
        <div className="header-search-container">
          <form action="/react/search" method="get">
            <input
              type="text"
              name="query"
              className="search-input"
              placeholder="Search for a card..."
            />
          </form>
        </div>
        <div className="profile-button">
          <Link to="/react/decks" className="action-button">
            Decks
          </Link>
        </div>
      </div>
    </div>
  );
}
