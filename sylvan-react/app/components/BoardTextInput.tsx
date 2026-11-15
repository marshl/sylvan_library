import React, { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { fetchJson, isAbortError } from '../api';

// The count at the start of a line, like "4", "4x" or "4 x ". The x has to be on its
// own so that the X of a name like "1 Xira Arien" isn't taken as part of the count.
const LINE_START = /^(\s*(?:\d+\s*(?:x\b)?\s*)?)(.*)$/i;
// The commander marker at the end of a line, which picking a name keeps
const LINE_END = /\s*\*cmdr\*\s*$/i;

/**
 * The card name being typed on the caret's line: where it starts, where it ends (not
 * counting a commander marker) and the part of it before the caret
 */
interface NameAtCaret {
  start: number;
  end: number;
  typed: string;
}

function nameAtCaret(text: string, caret: number): NameAtCaret | null {
  const lineStart = text.lastIndexOf('\n', caret - 1) + 1;
  const lineEndIndex = text.indexOf('\n', caret);
  const lineEnd = lineEndIndex === -1 ? text.length : lineEndIndex;
  const before = text.slice(lineStart, caret);
  const match = LINE_START.exec(before);
  if (!match) return null;
  const start = lineStart + match[1].length;
  const rest = text.slice(start, lineEnd);
  const marker = LINE_END.exec(rest);
  const end = marker ? start + marker.index : lineEnd;
  // The caret is inside the commander marker
  if (caret > end) return null;
  return { start, end, typed: match[2] };
}

/**
 * Where a character of a textarea is drawn, relative to the textarea's top left corner.
 * The text up to that character is copied into a hidden div styled like the textarea,
 * and the position of a marker put after it is measured.
 */
function caretPosition(textarea: HTMLTextAreaElement, index: number) {
  const style = getComputedStyle(textarea);
  const mirror = document.createElement('div');
  for (const property of [
    'boxSizing',
    'width',
    'paddingTop',
    'paddingRight',
    'paddingBottom',
    'paddingLeft',
    'borderTopWidth',
    'borderRightWidth',
    'borderBottomWidth',
    'borderLeftWidth',
    'borderStyle',
    'fontFamily',
    'fontSize',
    'fontWeight',
    'fontStyle',
    'letterSpacing',
    'lineHeight',
    'tabSize',
    'textTransform',
  ] as const) {
    mirror.style[property] = style[property];
  }
  mirror.style.position = 'absolute';
  mirror.style.visibility = 'hidden';
  mirror.style.top = '0';
  mirror.style.left = '-9999px';
  mirror.style.whiteSpace = 'pre-wrap';
  mirror.style.overflowWrap = 'break-word';
  mirror.textContent = textarea.value.slice(0, index);
  const marker = document.createElement('span');
  marker.textContent = '​';
  mirror.appendChild(marker);
  document.body.appendChild(mirror);
  const position = {
    top: marker.offsetTop - textarea.scrollTop,
    left: marker.offsetLeft - textarea.scrollLeft,
    height: marker.offsetHeight,
  };
  document.body.removeChild(mirror);
  return position;
}

/**
 * The text box for a board's cards, which suggests card names while one is being typed.
 * Arrow keys move through the suggestions, Enter or Tab picks one and Escape hides them.
 */
export default function BoardTextInput({
  value,
  onChange,
  textareaRef,
  className,
  ariaLabel,
  rows,
}: {
  value: string;
  onChange: (value: string) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  className?: string;
  ariaLabel: string;
  rows?: number;
}) {
  const listId = useId();
  // The name being typed, set only by typing so that pasting or moving the caret
  // doesn't bring up suggestions
  const [target, setTarget] = useState<NameAtCaret | null>(null);
  // The suggestions, along with the text they're for, so that ones for text that has
  // since changed aren't picked
  const [suggestions, setSuggestions] = useState<{ query: string; names: string[] }>({
    query: '',
    names: [],
  });
  const [highlighted, setHighlighted] = useState(0);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  // Where to put the caret once a picked name is in the text
  const pendingCaret = useRef<number | null>(null);

  const query = target?.typed.trim() ?? '';

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions({ query: '', names: [] });
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetchJson<string[]>(`/api/cards/card-names/?${new URLSearchParams({ q: query })}`, {
        signal: controller.signal,
      })
        .then((names) => {
          setSuggestions({ query, names });
          setHighlighted(0);
        })
        .catch((err) => {
          if (!isAbortError(err)) setSuggestions({ query: '', names: [] });
        });
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (pendingCaret.current !== null && textarea) {
      textarea.setSelectionRange(pendingCaret.current, pendingCaret.current);
      pendingCaret.current = null;
    }
  }, [value, textareaRef]);

  const current = suggestions.query === query ? suggestions.names : [];
  // A name that's already typed out in full doesn't need suggesting
  const finished = current.length === 1 && current[0].toLowerCase() === query.toLowerCase();
  const open = target !== null && current.length > 0 && !finished;

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!open || !textarea || !target) {
      setPosition(null);
      return;
    }
    const caret = caretPosition(textarea, target.start);
    setPosition({ top: caret.top + caret.height, left: caret.left });
  }, [open, target, textareaRef]);

  function pick(name: string) {
    if (!target) return;
    pendingCaret.current = target.start + name.length;
    onChange(value.slice(0, target.start) + name + value.slice(target.end));
    setTarget(null);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (!open) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlighted((h) => (h + 1) % current.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlighted((h) => (h - 1 + current.length) % current.length);
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      const name = current[highlighted];
      // Enter after typing a whole name starts a new line as usual
      if (e.key === 'Enter' && name.toLowerCase() === query.toLowerCase()) {
        setTarget(null);
        return;
      }
      e.preventDefault();
      pick(name);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setTarget(null);
    } else if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(e.key)) {
      setTarget(null);
    }
  }

  return (
    <div className="board-text-input">
      <textarea
        ref={textareaRef}
        className={className}
        aria-label={ariaLabel}
        aria-autocomplete="list"
        aria-controls={listId}
        aria-expanded={open}
        aria-activedescendant={open ? `${listId}-${highlighted}` : undefined}
        rows={rows}
        value={value}
        spellCheck={false}
        onChange={(e) => {
          const inputType = (e.nativeEvent as InputEvent).inputType ?? '';
          const typing = inputType.startsWith('insertText') || inputType.startsWith('delete');
          const caret = e.target.selectionStart;
          setTarget(
            typing && caret === e.target.selectionEnd ? nameAtCaret(e.target.value, caret) : null,
          );
          onChange(e.target.value);
        }}
        onKeyDown={onKeyDown}
        onMouseDown={() => setTarget(null)}
        onBlur={() => setTarget(null)}
      />
      {open && position && (
        <ul
          id={listId}
          role="listbox"
          className="card-suggestions"
          style={{ top: position.top, left: position.left }}
        >
          {current.map((name, i) => (
            <li
              key={name}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === highlighted}
              className={i === highlighted ? 'highlighted' : ''}
              // Picking on mouse down keeps the focus in the textarea
              onMouseDown={(e) => {
                e.preventDefault();
                pick(name);
              }}
              onMouseEnter={() => setHighlighted(i)}
            >
              {name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
