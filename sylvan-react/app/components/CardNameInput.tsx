import React, { useEffect, useState } from 'react';
import { fetchJson } from '../api';

/**
 * A text input that suggests card names as you type. With exactOnPick, picking a
 * suggestion puts a "!" in front of it, so that it's searched for by its exact name.
 */
export default function CardNameInput({
  id,
  value,
  onChange,
  inputRef,
  placeholder,
  exactOnPick = false,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  inputRef?: React.RefObject<HTMLInputElement | null>;
  placeholder?: string;
  exactOnPick?: boolean;
}) {
  const [names, setNames] = useState<string[]>([]);

  // Names are suggested for what comes after a "!" too
  const query = value.replace(/^!/, '').trim();

  useEffect(() => {
    if (query.length < 2) {
      setNames([]);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetchJson<string[]>(`/api/cards/card-names/?${new URLSearchParams({ q: query })}`, {
        signal: controller.signal,
      })
        .then(setNames)
        .catch(() => {});
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  // Chrome marks a picked suggestion as replacement text, and Firefox gives no input
  // type for it
  function isPick(e: React.SyntheticEvent, newValue: string): boolean {
    const inputType = (e.nativeEvent as InputEvent).inputType;
    return (
      !newValue.startsWith('!') &&
      (inputType === 'insertReplacementText' || (!inputType && names.includes(newValue)))
    );
  }

  return (
    <>
      <input
        id={id}
        ref={inputRef}
        list={`${id}-options`}
        autoComplete="off"
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          const newValue = e.target.value;
          onChange(exactOnPick && isPick(e, newValue) ? `!${newValue}` : newValue);
        }}
        // Picking the name that's already typed doesn't change the text, so React gives no
        // change event for it
        onInput={(e) => {
          if (exactOnPick && e.currentTarget.value === value && isPick(e, value)) {
            onChange(`!${value}`);
          }
        }}
      />
      <datalist id={`${id}-options`}>
        {names.map((name) => (
          <option key={name} value={name} />
        ))}
      </datalist>
    </>
  );
}
