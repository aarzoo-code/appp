import React, { useEffect, useState } from 'react';

interface Badge {
  id: number;
  code: string;
  name: string;
  description?: string;
  icon?: string | null;
  earned?: boolean;
}

const BadgeGrid: React.FC = () => {
  const [badges, setBadges] = useState<Badge[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const [resAll, resUser] = await Promise.all([
          fetch('/api/v1/badges'),
          fetch('/api/v1/users/1/badges'),
        ]);
        const all = await resAll.json();
        const user = await resUser.json();
        const earnedCodes = new Set((user.badges || []).map((b: any) => b.code));
        const items = (all.badges || []).map((b: any) => ({ ...b, earned: earnedCodes.has(b.code) }));
        setBadges(items);
      } catch (err) {
        console.error('Failed to load badges', err);
      }
    })();
  }, []);

  if (!badges.length) return <div className="text-sm text-muted-foreground">No badges found.</div>;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {badges.map(b => (
        <div key={b.id} className="p-4 border border-border rounded-lg bg-card text-center">
          <div className="text-xl font-bold mb-2">{b.name} {b.earned && <span className="text-sm text-green-500">✔</span>}</div>
          <div className="text-sm text-muted-foreground mb-3">{b.description}</div>
          {!b.earned ? (
            <button
              className="px-3 py-1 rounded bg-primary text-primary-foreground text-sm"
              onClick={async () => {
                try {
                  const resp = await fetch(`/api/v1/users/1/badges`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: b.code }) });
                  const data = await resp.json();
                  if (data.ok) {
                    setBadges(prev => prev.map(p => p.id === b.id ? { ...p, earned: true } : p));
                  }
                } catch (err) {
                  console.error('Failed to award badge', err);
                }
              }}
            >Claim</button>
          ) : (
            <div className="text-xs text-muted-foreground">Earned</div>
          )}
        </div>
      ))}
    </div>
  );
};

export default BadgeGrid;
