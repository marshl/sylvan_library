import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { fetchJson } from '../api';

interface CardSet {
  id: number;
  name: string;
  code: string;
  type: string | null;
  keyrune_code: string;
  release_date: string | null;
  total_set_size: number;
  is_online_only: boolean;
  child_sets: CardSet[];
}

// A set in the list, with only the child sets that match the filters
interface ShownSet {
  set: CardSet;
  // False for a parent that's only shown because one of its child sets matches
  matches: boolean;
  children: ShownSet[];
}

const TYPE_LABELS: Record<string, string> = {
  from_the_vault: 'From the Vault',
  funny: 'Un-set',
};

function typeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ');
}

// The year is left off dates in the year the set is listed under
function formatDate(date: string | null, groupYear: string): string {
  if (!date) return '';
  return new Date(`${date}T00:00:00`).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: date.startsWith(groupYear) ? undefined : 'numeric',
  });
}

function setMatches(set: CardSet, text: string, type: string): boolean {
  return (
    (!type || set.type === type) &&
    (!text || set.name.toLowerCase().includes(text) || set.code.toLowerCase() === text)
  );
}

function filterSets(sets: CardSet[], text: string, type: string): ShownSet[] {
  const shown: ShownSet[] = [];
  for (const set of sets) {
    const matches = setMatches(set, text, type);
    const children = filterSets(set.child_sets, text, type);
    if (matches || children.length > 0) shown.push({ set, matches, children });
  }
  return shown;
}

function countSets(sets: CardSet[]): number {
  return sets.reduce((total, set) => total + 1 + countSets(set.child_sets), 0);
}

function collectTypes(sets: CardSet[], types: Map<string, number>) {
  for (const set of sets) {
    if (set.type) types.set(set.type, (types.get(set.type) ?? 0) + 1);
    collectTypes(set.child_sets, types);
  }
}

function SetRow({
  shown,
  depth,
  groupYear,
  expanded,
  onToggle,
}: {
  shown: ShownSet;
  depth: number;
  groupYear: string;
  expanded: boolean;
  onToggle?: () => void;
}) {
  const { set, matches, children } = shown;
  const childCount = countSets(children.map((c) => c.set));
  return (
    <>
      <tr
        className={`set-row${depth > 0 ? ' set-row-child' : ''}${matches ? '' : ' set-row-context'}`}
      >
        <td className="set-toggle-cell">
          {onToggle && children.length > 0 && (
            <button
              type="button"
              className="set-toggle"
              aria-expanded={expanded}
              aria-label={`${expanded ? 'Hide' : 'Show'} ${childCount} sets in ${set.name}`}
              onClick={onToggle}
            >
              <span className="set-toggle-arrow" aria-hidden="true">
                ▸
              </span>
              {childCount}
            </button>
          )}
        </td>
        <td className="set-name-cell">
          <Link
            to={`/search?query=${encodeURIComponent(`set:${set.code}`)}`}
            className="set-name"
            style={depth > 0 ? { paddingLeft: `${depth * 1.5}em` } : undefined}
          >
            <i
              className={`set-symbol ss ss-fw ss-${set.keyrune_code.toLowerCase()}`}
              aria-hidden="true"
            />
            <span>{set.name}</span>
          </Link>
          {set.is_online_only && <span className="set-tag">Online</span>}
        </td>
        <td className="set-code">{set.code}</td>
        <td className="set-type">{set.type ? typeLabel(set.type) : ''}</td>
        <td className="set-size">{set.total_set_size}</td>
        <td className="set-date">{formatDate(set.release_date, groupYear)}</td>
      </tr>
      {expanded &&
        children.map((child) => (
          <SetRow
            key={child.set.id}
            shown={child}
            depth={depth + 1}
            groupYear={groupYear}
            expanded
          />
        ))}
    </>
  );
}

export default function SetList() {
  const [sets, setSets] = useState<CardSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [searchParams, setSearchParams] = useSearchParams();
  const text = searchParams.get('q') ?? '';
  const type = searchParams.get('type') ?? '';

  useEffect(() => {
    fetchJson<CardSet[]>('/api/cards/all-sets/')
      .then(setSets)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const types = useMemo(() => {
    const counts = new Map<string, number>();
    collectTypes(sets, counts);
    return [...counts].sort((a, b) => typeLabel(a[0]).localeCompare(typeLabel(b[0])));
  }, [sets]);

  const filtering = Boolean(text.trim() || type);
  const shown = useMemo(
    () => filterSets(sets, text.trim().toLowerCase(), type),
    [sets, text, type],
  );
  const years = useMemo(() => {
    const byYear = new Map<string, ShownSet[]>();
    for (const s of shown) {
      const year = s.set.release_date?.slice(0, 4) ?? 'Unknown';
      byYear.set(year, [...(byYear.get(year) ?? []), s]);
    }
    return [...byYear];
  }, [shown]);

  function updateParam(key: string, value: string) {
    setSearchParams(
      (params) => {
        if (value) params.set(key, value);
        else params.delete(key);
        return params;
      },
      { replace: true },
    );
  }

  function toggle(id: number) {
    const next = new Set(expanded);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpanded(next);
  }

  const parents = shown.filter((s) => s.children.length > 0);
  const allExpanded = parents.every((s) => expanded.has(s.set.id));

  if (loading) {
    return <div className="results-page">Loading...</div>;
  }

  if (error) {
    return <div className="results-page error">Error: {error}</div>;
  }

  return (
    <div className="results-page set-list-page">
      <h1>Sets</h1>
      <div className="set-filters">
        <input
          type="search"
          aria-label="Filter sets"
          placeholder="Filter by name or code"
          value={text}
          onChange={(e) => updateParam('q', e.target.value)}
        />
        <select
          aria-label="Set type"
          value={type}
          onChange={(e) => updateParam('type', e.target.value)}
        >
          <option value="">All types</option>
          {types.map(([value, count]) => (
            <option key={value} value={value}>
              {typeLabel(value)} ({count})
            </option>
          ))}
        </select>
        {!filtering && parents.length > 0 && (
          <button
            type="button"
            className="link-button"
            onClick={() =>
              setExpanded(allExpanded ? new Set() : new Set(parents.map((s) => s.set.id)))
            }
          >
            {allExpanded ? 'Collapse all' : 'Expand all'}
          </button>
        )}
      </div>
      {shown.length === 0 ? (
        <p className="subtitle">No sets match.</p>
      ) : (
        <table className="set-table">
          <thead>
            <tr>
              <th className="set-toggle-cell">
                <span className="visually-hidden">Child sets</span>
              </th>
              <th className="set-name-cell">Name</th>
              <th className="set-code">Code</th>
              <th className="set-type">Type</th>
              <th className="set-size">Cards</th>
              <th className="set-date">Released</th>
            </tr>
          </thead>
          {years.map(([year, yearSets]) => (
            <tbody key={year}>
              <tr className="set-year">
                <th colSpan={6} scope="rowgroup">
                  {year}
                </th>
              </tr>
              {yearSets.map((s) => (
                <SetRow
                  key={s.set.id}
                  shown={s}
                  depth={0}
                  groupYear={year}
                  // Filtering shows every match, so nothing is hidden behind a toggle
                  expanded={filtering || expanded.has(s.set.id)}
                  onToggle={filtering ? undefined : () => toggle(s.set.id)}
                />
              ))}
            </tbody>
          ))}
        </table>
      )}
    </div>
  );
}
