import React, { useEffect, useState } from 'react';
import { fetchJson } from '../api';

/**
 * A text input that suggests card names as you type
 */
export default function CardNameInput({
  id,
  value,
  onChange,
  inputRef,
  placeholder,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  inputRef?: React.RefObject<HTMLInputElement | null>;
  placeholder?: string;
}) {
  const [names, setNames] = useState<string[]>([]);

  useEffect(() => {
    if (value.trim().length < 2) {
      setNames([]);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetchJson<string[]>(`/api/cards/card-names/?${new URLSearchParams({ q: value })}`, {
        signal: controller.signal,
      })
        .then(setNames)
        .catch(() => {});
    }, 150);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value]);

  return (
    <>
      <input
        id={id}
        ref={inputRef}
        list={`${id}-options`}
        autoComplete="off"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <datalist id={`${id}-options`}>
        {names.map((name) => (
          <option key={name} value={name} />
        ))}
      </datalist>
    </>
  );
}
