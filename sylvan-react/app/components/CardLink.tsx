import React, { useState } from 'react';
import { Link } from 'react-router';

const POPUP_WIDTH = 260;
const POPUP_HEIGHT = 362;

function rotation(layout?: string, side?: string | null): number {
  if (layout === 'aftermath' && side === 'b') return -90;
  if (layout === 'flip' && side === 'b') return 180;
  return 0;
}

/**
 * A card name that links to a search for the card and shows its image on hover
 */
export default function CardLink({
  name,
  imageUrl,
  layout,
  side,
  newTab = false,
}: {
  name: string;
  imageUrl: string;
  layout?: string;
  side?: string | null;
  newTab?: boolean;
}) {
  const [popup, setPopup] = useState<{ top: number; left: number } | null>(null);

  function onMouseEnter(e: React.MouseEvent<HTMLAnchorElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const offset = 20;
    let left = rect.right + offset;
    // Flip to the left of the link if it would go off the right of the window
    if (left + POPUP_WIDTH > window.innerWidth) left = rect.left - offset - POPUP_WIDTH;
    const top = Math.max(
      8,
      Math.min(rect.top + rect.height / 2 - POPUP_HEIGHT / 2, window.innerHeight - POPUP_HEIGHT - 8),
    );
    setPopup({ top, left });
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
            transform: `rotate(${rotation(layout, side)}deg)`,
          }}
        >
          <img src={imageUrl} alt={name} />
        </div>
      )}
    </span>
  );
}
