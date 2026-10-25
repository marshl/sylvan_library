import React, { useState, useEffect } from 'react';
import { Link } from 'react-router';
import { fetchJson } from '../api';

interface Set {
  id: number;
  name: string;
  code: string;
  release_date: string;
  total_set_size: number;
  child_sets: Set[];
}

function SetRow({ cardSet, depth }: { cardSet: Set; depth: number }) {
  return (
    <>
      <tr>
        <td style={{ paddingLeft: `${(depth - 1) * 1.5}em` }}>
          <Link to={`/search?query=${encodeURIComponent(`set:${cardSet.code}`)}`}>
            {cardSet.name}
          </Link>
        </td>
        <td>{cardSet.total_set_size}</td>
        <td>{cardSet.release_date}</td>
      </tr>
      {cardSet.child_sets &&
        cardSet.child_sets.map((childSet) => (
          <SetRow key={childSet.id} cardSet={childSet} depth={depth + 1} />
        ))}
    </>
  );
}

export default function SetList() {
  const [sets, setSets] = useState<Set[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSets() {
      try {
        setSets(await fetchJson<Set[]>('/api/cards/all-sets/'));
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }

    fetchSets();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="results-page">
      <h1>All Sets</h1>
      <table className="set-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Release Date</th>
          </tr>
        </thead>
        <tbody>
          {sets.map((set) => (
            <SetRow key={set.id} cardSet={set} depth={1} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
