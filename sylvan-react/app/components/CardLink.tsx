import React, { useState } from 'react';
import { Link } from 'react-router';

// One card image and its border
const POPUP_WIDTH = 260;
const POPUP_HEIGHT = 362;
const BACK_GAP = 4;

function rotation(layout?: string, side?: string | null): number {
  if (layout === 'aftermath' && side === 'b') return -90;
  if (layout === 'flip' && side === 'b') return 180;
  return 0;
}

/**
 * A card name that links to a search for the card and shows its image on hover. Two
 * faced cards show the front and back side by side.
 */
export default function CardLink({
  name,
  imageUrl,
  backImageUrl,
  layout,
  side,
  newTab = false,
}: {
  name: string;
  imageUrl: string;
  backImageUrl?: string | null;
  layout?: string;
  side?: string | null;
  newTab?: boolean;
}) {
  const [popup, setPopup] = useState<{ top: number; left: number } | null>(null);

  function onMouseEnter(e: React.MouseEvent<HTMLAnchorElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const offset = 20;
    const margin = 8;
    const width = backImageUrl ? POPUP_WIDTH * 2 + BACK_GAP : POPUP_WIDTH;
    const fitsRight = rect.right + offset + width <= window.innerWidth - margin;
    const fitsLeft = rect.left - offset - width >= margin;
    if (fitsRight || fitsLeft) {
      // Beside the link, on the left if it would go off the right of the window
      setPopup({
        left: fitsRight ? rect.right + offset : rect.left - offset - width,
        top: Math.max(
          margin,
          Math.min(
            rect.top + rect.height / 2 - POPUP_HEIGHT / 2,
            window.innerHeight - POPUP_HEIGHT - margin,
          ),
        ),
      });
      return;
    }
    // Otherwise below the link, or above it if there's more room there, so it doesn't
    // cover the link
    const below = window.innerHeight - rect.bottom >= rect.top;
    setPopup({
      left: Math.max(margin, Math.min(rect.left, window.innerWidth - width - margin)),
      top: below
        ? Math.min(rect.bottom + margin, window.innerHeight - POPUP_HEIGHT - margin)
        : Math.max(rect.top - margin - POPUP_HEIGHT, margin),
    });
  }

  return (
    <span className="card-link">
      <Link
        to={`/search?${new URLSearchParams({ query: name })}`}
        target={newTab ? '_blank' : undefined}
        rel="noreferrer"
        onMouseEnter={onMouseEnter}
        onMouseLeave={() => setPopup(null)}
      >
        {name}
      </Link>
      {popup && (
        <div
          className="image-popup-container"
          style={{
            position: 'fixed',
            top: popup.top,
            left: popup.left,
            display: 'flex',
            gap: BACK_GAP,
            transform: `rotate(${rotation(layout, side)}deg)`,
          }}
        >
          <img src={imageUrl} alt={backImageUrl ? `${name} (front)` : name} />
          {backImageUrl && <img src={backImageUrl} alt={`${name} (back)`} />}
        </div>
      )}
    </span>
  );
}
