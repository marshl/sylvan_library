import React, { useState } from 'react';
import { fetchJson } from '../api';
import type { Card, CardFace, CardPrinting, SearchResult as Result } from '../types';
import CardResultDetails from './CardResultDetails';
import RulesText, { ManaSymbols } from './ManaText';

const ROTATING_LAYOUTS = ['split', 'aftermath', 'planar'];
const DOUBLE_FACED_LAYOUTS = ['transform', 'meld', 'modal_dfc'];

function setSymbolClasses(printing: CardPrinting, selected: boolean): string {
  const classes = ['setIcon', 'ss', 'ss-2x', `ss-${printing.keyrune_code}`];
  if (printing.owned_count) classes.push('owned');
  if (printing.set.code === 'TSB') {
    classes.push('ss-timeshifted');
  } else {
    classes.push(`ss-${printing.rarity.name.toLowerCase()}`);
  }
  if (printing.rarity.symbol !== 'C') classes.push('ss-grad');
  if (selected) classes.push('clicked');
  classes.push(printing.rarity.symbol);
  return classes.join(' ');
}

function SetSymbols({
  card,
  selected,
  onSelect,
}: {
  card: Card;
  selected: CardPrinting;
  onSelect: (printing: CardPrinting) => void;
}) {
  return (
    <div className="search-result-set-list">
      <p style={{ textAlign: 'center', maxHeight: '200px', overflowY: 'auto' }}>
        {card.printings.map((printing) => (
          <i
            key={printing.id}
            className={setSymbolClasses(printing, printing.id === selected.id)}
            title={
              printing.owned_count
                ? `${printing.set.name}\nx ${printing.owned_count}`
                : printing.set.name
            }
            role="button"
            aria-label={printing.set.name}
            onClick={(e) => {
              e.stopPropagation();
              onSelect(printing);
            }}
          />
        ))}
      </p>
    </div>
  );
}

function Face({ face, ownedCount }: { face: CardFace; ownedCount: number | null }) {
  return (
    <div className="search-result-base-details" style={{ display: 'inline-block' }}>
      <h2 className="search-result-title">
        {face.name}{' '}
        <i
          className="fa fa-copy copy-text-link"
          title="Copy name"
          onClick={(e) => {
            e.stopPropagation();
            navigator.clipboard.writeText(face.name);
          }}
        />
        {face.mana_cost && (
          <>
            {' '}
            <span className="search-result-mana-cost">
              <ManaSymbols text={face.mana_cost} shadowed />
            </span>{' '}
            ({face.mana_value})
          </>
        )}
        {!!ownedCount && (
          <span
            style={{
              fontVariant: 'small-caps',
              float: 'right',
              paddingRight: '8px',
              fontSize: 'smaller',
            }}
          >
            You own: {ownedCount}
          </span>
        )}
      </h2>
      <div style={{ display: 'inline-flex' }} className="subtitle type-line">
        <span>{face.type_line}</span>
      </div>
      <h3 className="subtitle">
        {face.rules_text && (
          <RulesText
            text={face.rules_text}
            isPlaneswalker={face.types.includes('Planeswalker')}
            isSaga={face.subtypes.includes('Saga')}
          />
        )}
        {face.power !== null ? (
          <div className="subtitle pow-tuff">
            P/T: {face.power}/{face.toughness}
          </div>
        ) : (
          face.loyalty !== null && (
            <span className="subtitle pow-tuff">Loyalty: {face.loyalty}</span>
          )
        )}
      </h3>
    </div>
  );
}

export default function SearchResult({
  result,
  expanded,
  onExpand,
}: {
  result: Result;
  expanded: boolean;
  onExpand: () => void;
}) {
  const [card, setCard] = useState<Card>(result.card);
  const [printingId, setPrintingId] = useState(result.selected_printing.id);
  const [rotated, setRotated] = useState(false);
  const [flipped, setFlipped] = useState(false);
  // Bumped after the user adds or removes cards so ownership-based tabs reload
  const [ownershipVersion, setOwnershipVersion] = useState(0);

  const printing =
    card.printings.find((p) => p.id === printingId) ?? result.selected_printing;
  const layout = card.layout;
  const isDoubleFaced = DOUBLE_FACED_LAYOUTS.includes(layout);
  const showTransform =
    isDoubleFaced && !(layout === 'meld' && card.faces[0]?.side === 'c');

  async function onOwnershipChanged() {
    setOwnershipVersion((v) => v + 1);
    try {
      setCard(await fetchJson<Card>(`/api/cards/card/${card.id}/`));
    } catch {
      // Counts on the card stay stale until the next search; the tabs still reload
    }
  }

  return (
    <div
      className={`search-result ${card.owned_count ? 'owned' : ''} ${
        expanded ? 'expanded' : ''
      }`}
      onClick={onExpand}
    >
      <div className="card-image-container">
        <span className={`js-card-result-image-container ${flipped ? 'flipped' : ''}`}>
          {printing.face_printings.map((fp, i) => (
            <img
              key={fp.id}
              className={[
                'card-image',
                i === 0 ? 'side-front' : 'side-back',
                `layout-${layout}`,
                layout === 'planar' ? 'wide' : '',
                isDoubleFaced ? 'flipping' : '',
                expanded ? 'clicked' : '',
                rotated ? 'rotated' : '',
              ].join(' ')}
              src={fp.image_url}
              alt={card.name}
              width={100}
              loading="lazy"
            />
          ))}
        </span>
        <span className="image-actions">
          {ROTATING_LAYOUTS.includes(layout) && (
            <button type="button" onClick={() => setRotated((r) => !r)}>
              Rotate
            </button>
          )}
          {layout === 'flip' && (
            <button type="button" onClick={() => setRotated((r) => !r)}>
              Flip
            </button>
          )}
          {showTransform && (
            <button type="button" onClick={() => setFlipped((f) => !f)}>
              Transform
            </button>
          )}
        </span>
      </div>

      <div style={{ width: '100%' }}>
        <div style={{ display: 'flex' }}>
          {card.faces.map((face) => (
            <Face key={face.id} face={face} ownedCount={card.owned_count} />
          ))}
          <SetSymbols card={card} selected={printing} onSelect={(p) => setPrintingId(p.id)} />
        </div>
        <CardResultDetails
          cardId={card.id}
          printingId={printing.id}
          printingLabel={`${printing.set.name}${printing.number ? ` (#${printing.number})` : ''}`}
          expanded={expanded}
          onExpand={onExpand}
          ownershipVersion={ownershipVersion}
          onOwnershipChanged={onOwnershipChanged}
        />
      </div>
    </div>
  );
}
