import React, { useState, useEffect } from 'react';

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
      <tr className={`set-row-${depth}`}>
        <td style={{ paddingLeft: `${depth * 1.5}em` }}>{cardSet.name}</td>
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
        const response = await fetch('/api/cards/all-sets/');
        if (!response.ok) {
          throw new Error('Failed to fetch sets');
        }
        const data = await response.json();
        setSets(data);
      } catch (error) {
        setError(error.message);
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
