import React, { useState } from 'react';
import { Link } from 'react-router';

// Card images are shown 256px wide, and are 488x680 at full size
const IMAGE_WIDTH = 256;
const IMAGE_HEIGHT = Math.round((IMAGE_WIDTH * 680) / 488);
// The white border around each image
const FRAME = 2;
const BACK_GAP = 4;

/**
 * One card image in its white border. Sideways cards are turned to read across.
 */
function PopupCard({ src, alt, sideways }: { src: string; alt: string; sideways: boolean }) {
  if (!sideways) {
    return (
      <div className="popup-card">
        <img src={src} alt={alt} />
      </div>
    );
  }
  return (
    <div className="popup-card">
      <div style={{ position: 'relative', width: IMAGE_HEIGHT, height: IMAGE_WIDTH }}>
        <img
          src={src}
          alt={alt}
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%) rotate(90deg)',
          }}
        />
      </div>
    </div>
  );
}

/**
 * A card name that links to a search for the card and shows its image on hover. Two
 * faced cards show the front and back side by side, and sideways cards (split cards,
 * battles etc.) are turned to read across. Only the front of a card can be sideways.
 */
export default function CardLink({
  name,
  imageUrl,
  backImageUrl,
  sideways = false,
  newTab = false,
}: {
  name: string;
  imageUrl: string;
  backImageUrl?: string | null;
  sideways?: boolean;
  newTab?: boolean;
}) {
  const [popup, setPopup] = useState<{ top: number; left: number } | null>(null);

  function onMouseEnter(e: React.MouseEvent<HTMLAnchorElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const offset = 20;
    const margin = 8;
    const upright = { width: IMAGE_WIDTH + FRAME * 2, height: IMAGE_HEIGHT + FRAME * 2 };
    const front = sideways ? { width: upright.height, height: upright.width } : upright;
    const width = backImageUrl ? front.width + BACK_GAP + upright.width : front.width;
    const height = backImageUrl ? upright.height : front.height;
    const fitsRight = rect.right + offset + width <= window.innerWidth - margin;
    const fitsLeft = rect.left - offset - width >= margin;
    if (fitsRight || fitsLeft) {
      // Beside the link, on the left if it would go off the right of the window
      setPopup({
        left: fitsRight ? rect.right + offset : rect.left - offset - width,
        top: Math.max(
          margin,
          Math.min(rect.top + rect.height / 2 - height / 2, window.innerHeight - height - margin),
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
        ? Math.min(rect.bottom + margin, window.innerHeight - height - margin)
        : Math.max(rect.top - margin - height, margin),
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
            alignItems: 'center',
            gap: BACK_GAP,
          }}
        >
          <PopupCard
            src={imageUrl}
            alt={backImageUrl ? `${name} (front)` : name}
            sideways={sideways}
          />
          {backImageUrl && <PopupCard src={backImageUrl} alt={`${name} (back)`} sideways={false} />}
        </div>
      )}
    </span>
  );
}
