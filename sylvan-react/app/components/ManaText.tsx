import React from 'react';

const MINUS_SYMBOLS = ['−', '-'];

/**
 * The mana-font classes for a symbol like "R", "2/W", "G/P" or "T"
 */
function manaClasses(rawSymbol: string, scale?: string, shadowed = false): string {
  const classes = ['ms'];
  if (scale) classes.push(`ms-${scale}`);

  let symbol = rawSymbol.toLowerCase();
  if (symbol.includes('/')) {
    if (symbol.endsWith('p')) {
      classes.push('ms-p');
      symbol = symbol[0];
    } else {
      symbol = symbol.replace('/', '');
    }
  }
  if (symbol === 't') symbol = 'tap';
  else if (symbol === 'q') symbol = 'untap';

  if (symbol.length === 2 && symbol[0] === 'h') {
    classes.push('ms-half');
    symbol = symbol[1];
  }

  classes.push(`ms-${symbol}`);
  if (symbol !== 'e' && symbol !== 'chaos') {
    classes.push('ms-cost');
    if (shadowed) classes.push('ms-shadow');
  }
  return classes.join(' ');
}

/**
 * Text with {X} mana symbols swapped for mana-font icons
 */
export function ManaSymbols({
  text,
  scale,
  shadowed = false,
}: {
  text: string;
  scale?: string;
  shadowed?: boolean;
}) {
  const parts = text.split(/{(.+?)}/);
  return (
    <>
      {parts.map((part, i) =>
        i % 2 === 1 ? (
          <i key={i} className={manaClasses(part, scale, shadowed)} />
        ) : (
          part && <React.Fragment key={i}>{part}</React.Fragment>
        ),
      )}
    </>
  );
}

/**
 * One line of rules text: mana symbols, with reminder text in italics
 */
function RulesLine({ text }: { text: string }) {
  const parts = text.split(/(\(.+?\))/);
  return (
    <>
      {parts.map((part, i) =>
        i % 2 === 1 ? (
          <i key={i}>
            <ManaSymbols text={part} />
          </i>
        ) : (
          <ManaSymbols key={i} text={part} />
        ),
      )}
    </>
  );
}

function LoyaltyCost({ cost }: { cost: string }) {
  const match = cost.match(/^\[?([+−-]?)([\dxX]+)\]?$/);
  if (!match) return <>{cost}</>;
  const [, sign, number] = match;
  const direction = MINUS_SYMBOLS.includes(sign) ? 'down' : sign === '+' ? 'up' : 'zero';
  return <i className={`ms ms-loyalty-${number.toLowerCase()} ms-3x ms-loyalty-${direction}`} />;
}

const ROMAN: Record<string, number> = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6 };

/**
 * Card rules text rendered the way the Django templates did: one paragraph
 * per line, mana and loyalty symbols as icons, saga chapter icons, and ability
 * words and reminder text in italics.
 */
export default function RulesText({
  text,
  isPlaneswalker = false,
  isSaga = false,
}: {
  text: string;
  isPlaneswalker?: boolean;
  isSaga?: boolean;
}) {
  return (
    <div>
      {text.split('\n').map((line, i) => {
        let prefix: React.ReactNode = null;
        let rest = line;

        const loyalty = isPlaneswalker && rest.match(/^(\[?[+−-]?[\dxX]+\]?):/);
        if (loyalty) {
          prefix = <LoyaltyCost cost={loyalty[1]} />;
          rest = rest.slice(loyalty[1].length);
        }

        const chapters = isSaga && rest.match(/^((?:[IV]+)(?:, [IV]+)*) — /);
        if (chapters) {
          prefix = chapters[1]
            .split(', ')
            .map((numeral) => (
              <i key={numeral} className={`ms ms-saga ms-saga-${ROMAN[numeral]} ms-2x`} />
            ));
          rest = rest.slice(chapters[1].length);
        }

        // Ability words like "Landfall — " at the start of a line
        const abilityWord = !loyalty && !chapters && rest.match(/^([^(—]+? — )/);
        return (
          <p key={i}>
            {prefix}
            {abilityWord ? (
              <>
                <i>{abilityWord[1]}</i>
                <RulesLine text={rest.slice(abilityWord[1].length)} />
              </>
            ) : (
              <RulesLine text={rest} />
            )}
          </p>
        );
      })}
    </div>
  );
}
