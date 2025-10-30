import React, { useEffect, useState } from 'react';
import LevelProgress from './LevelProgress';
import BadgeGrid from './BadgeGrid';

interface ProgressPayload {
  ok: boolean;
  user: any;
  xp: number;
  level: number;
  xp_to_next: number;
  next_level_threshold: number;
  level_progress_percent: number;
  streak: { current_streak?: number };
  recent_events: any[];
  badges: any[];
}

const ProgressPanel: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ProgressPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const token = typeof window !== 'undefined' ? localStorage.getItem('ai:token') : null;

  const fetchProgress = async () => {
    setLoading(true);
    try {
      const headers: any = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch('/api/v1/me/progress', { headers });
      if (!res.ok) throw new Error('Failed to fetch progress');
      const json = await res.json();
      setData(json as ProgressPayload);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProgress();
  }, []);

  const doCheckin = async () => {
    try {
      const headers: any = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch('/api/v1/me/checkin', { method: 'POST', headers });
      const j = await res.json();
      if (j.ok) {
        // refresh progress
        await fetchProgress();
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="p-4">Loading progress...</div>;
  if (error) return <div className="p-4 text-red-500">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold">Level {data.level}</h3>
          <div className="text-sm text-muted-foreground">{data.xp} XP</div>
        </div>
        <div>
          <button className="px-3 py-1 rounded bg-primary text-white" onClick={doCheckin}>
            Check in
          </button>
        </div>
      </div>

      <LevelProgress xp={data.xp} level={data.level} nextThreshold={data.next_level_threshold} />

      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">{data.xp_to_next} XP to next level</div>
        <div className="text-sm text-muted-foreground">Streak: {data.streak?.current_streak || 0}</div>
      </div>

      <div>
        <h4 className="font-semibold mb-2">Badges</h4>
        <BadgeGrid />
      </div>
    </div>
  );
};

export default ProgressPanel;
