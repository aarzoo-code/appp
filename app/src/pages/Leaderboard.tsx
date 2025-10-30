import React, { useEffect, useState } from 'react';

interface Row {
  rank: number;
  user_id: number;
  display_name: string;
  xp: number;
  level: number;
}

const Leaderboard: React.FC = () => {
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    let mounted = true;
    if (typeof EventSource !== 'undefined') {
      const es = new EventSource('/api/v1/leaderboard/stream');
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (mounted && data?.rows) setRows(data.rows);
        } catch (err) {
          console.error('Invalid SSE data', err);
        }
      };
      es.onerror = (err) => {
        console.error('SSE error', err);
        es.close();
      };
      return () => { mounted = false; es.close(); };
    } else {
      const fetchBoard = async () => {
        try {
          const res = await fetch('/api/v1/leaderboard');
          const data = await res.json();
          if (mounted && data?.rows) setRows(data.rows);
        } catch (err) {
          console.error('Failed to fetch leaderboard', err);
        }
      };
      fetchBoard();
      const t = setInterval(fetchBoard, 10000);
      return () => { mounted = false; clearInterval(t); };
    }
  }, []);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Leaderboard</h1>
      <div className="overflow-x-auto">
        <table className="w-full table-auto border-collapse text-sm">
          <thead>
            <tr className="text-left">
              <th className="p-2">Rank</th>
              <th className="p-2">User</th>
              <th className="p-2">XP</th>
              <th className="p-2">Level</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.user_id} className="border-t">
                <td className="p-2">{r.rank}</td>
                <td className="p-2">{r.display_name}</td>
                <td className="p-2">{r.xp}</td>
                <td className="p-2">{r.level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Leaderboard;
