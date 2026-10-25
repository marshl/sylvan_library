import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router';
import { logout, type CurrentUser } from '../user';

interface MenuItem {
  label: string;
  // Either a page in the app, a full page load (e.g. Django admin), or an action
  to?: string;
  href?: string;
  onSelect?: () => void;
}

function menuItems(user: CurrentUser): MenuItem[] {
  return [
    { label: 'My Decks', to: '/decks' },
    ...(user.is_staff ? [{ label: 'Admin', href: '/admin/' }] : []),
    { label: 'Log out', onSelect: logout },
  ];
}

function formatDate(isoDate: string): string {
  // Parsed as local midnight so the date doesn't shift with the timezone
  return new Date(`${isoDate}T00:00`).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/**
 * The username button in the top bar, which opens a menu of the user's details and links
 */
export default function ProfileMenu({ user }: { user: CurrentUser }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const itemRefs = useRef<(HTMLElement | null)[]>([]);
  const location = useLocation();
  const items = menuItems(user);

  // Following a link in the menu closes it
  useEffect(() => setOpen(false), [location]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(e: PointerEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, [open]);

  function focusItem(index: number) {
    const count = items.length;
    itemRefs.current[(index + count) % count]?.focus();
  }

  function onButtonKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      setOpen(true);
      // Wait for the menu to render before moving focus into it
      requestAnimationFrame(() => focusItem(e.key === 'ArrowDown' ? 0 : -1));
    }
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (open && e.key === 'Escape') {
      e.preventDefault();
      setOpen(false);
      buttonRef.current?.focus();
    }
  }

  function onMenuKeyDown(e: React.KeyboardEvent) {
    const index = itemRefs.current.findIndex((el) => el === document.activeElement);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      focusItem(index + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      focusItem(index - 1);
    } else if (e.key === 'Home') {
      e.preventDefault();
      focusItem(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      focusItem(-1);
    } else if (e.key === 'Tab') {
      setOpen(false);
    }
  }

  return (
    <div ref={containerRef} className="profile-menu" onKeyDown={onKeyDown}>
      <button
        ref={buttonRef}
        type="button"
        className="action-button profile-button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls="profile-menu"
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onButtonKeyDown}
      >
        {user.username} <i className={`fa fa-caret-${open ? 'up' : 'down'}`} aria-hidden="true" />
      </button>
      {open && (
        <div className="profile-container" onKeyDown={onMenuKeyDown}>
          <div className="profile-details">
            <p>
              <b>{user.username}</b>
            </p>
            {user.email && <p>{user.email}</p>}
            {user.date_joined && <p>Joined {formatDate(user.date_joined)}</p>}
          </div>
          <ul
            id="profile-menu"
            role="menu"
            aria-label={`${user.username} menu`}
            onClick={() => setOpen(false)}
          >
            {items.map((item, i) => {
              const props = {
                ref: (el: HTMLElement | null) => {
                  itemRefs.current[i] = el;
                },
                role: 'menuitem',
                className: 'profile-menu-item',
              };
              return (
                <li key={item.label} role="none">
                  {item.to ? (
                    <Link {...props} to={item.to}>
                      {item.label}
                    </Link>
                  ) : item.href ? (
                    <a {...props} href={item.href}>
                      {item.label}
                    </a>
                  ) : (
                    <button {...props} type="button" onClick={item.onSelect}>
                      {item.label}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
