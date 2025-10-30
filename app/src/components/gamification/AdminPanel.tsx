import React, { useEffect, useState } from 'react';
import { Button } from '@/components/button';

interface BadgeItem {
  id: number;
  code: string;
  name: string;
  description?: string;
}

interface RuleItem {
  id: number;
  code: string;
  rule_type: string;
  params?: any;
}

const AdminPanel: React.FC = () => {
  const [token, setToken] = useState<string>(() => localStorage.getItem('ai:admin_token') || '');
  const [badges, setBadges] = useState<BadgeItem[]>([]);
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetchAll();
  }, []);

  const headers = () => {
    const h: any = { 'Content-Type': 'application/json' };
    if (token) h['X-Admin-Token'] = token;
    return h;
  };

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [bR, rR] = await Promise.all([
        fetch('/api/v1/admin/badges', { headers: headers() }),
        fetch('/api/v1/admin/rules', { headers: headers() }),
      ]);
      if (!bR.ok) throw new Error('Failed to fetch badges');
      if (!rR.ok) throw new Error('Failed to fetch rules');
      const bJ = await bR.json();
      const rJ = await rR.json();
      setBadges(bJ.badges || []);
      setRules(rJ.rules || []);
      setErr(null);
    } catch (e: any) {
      setErr(e.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const createBadge = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = new FormData(e.target as HTMLFormElement);
    const code = form.get('code') as string;
    const name = form.get('name') as string;
    try {
      const res = await fetch('/api/v1/admin/badges', { method: 'POST', headers: headers(), body: JSON.stringify({ code, name }) });
      const j = await res.json();
      if (res.ok) {
        await fetchAll();
      } else {
        setErr(j.error || 'Failed to create');
      }
    } catch (err: any) {
      setErr(err.message || 'Failed');
    }
  };

  const createRule = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = new FormData(e.target as HTMLFormElement);
    const code = form.get('r_code') as string;
    const rule_type = form.get('rule_type') as string;
    const params = form.get('params') as string;
    let parsed = undefined;
    try {
      parsed = params ? JSON.parse(params) : undefined;
    } catch (e) {
      setErr('Invalid JSON in params');
      return;
    }
    try {
      const res = await fetch('/api/v1/admin/rules', { method: 'POST', headers: headers(), body: JSON.stringify({ code, rule_type, params: parsed }) });
      const j = await res.json();
      if (res.ok) {
        await fetchAll();
      } else {
        setErr(j.error || 'Failed to create rule');
      }
    } catch (err: any) {
      setErr(err.message || 'Failed');
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <h2 className="text-2xl font-bold mb-4">Admin — Badges & Rules</h2>
      <div className="mb-4">
        <label className="text-sm">Admin token (optional)</label>
        <div className="flex gap-2 mt-2">
          <input className="input" value={token} onChange={(e) => { setToken(e.target.value); localStorage.setItem('ai:admin_token', e.target.value); }} placeholder="X-Admin-Token or leave empty to use JWT" />
          <Button onClick={fetchAll}>Refresh</Button>
        </div>
      </div>

      {err && <div className="text-red-500 mb-2">{err}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 bg-card border border-border rounded">
          <h3 className="font-semibold mb-2">Badges</h3>
          <ul className="space-y-2 mb-4">
            {badges.map(b => (
              <li key={b.id} className="p-2 border border-border rounded bg-secondary">
                <div className="flex justify-between">
                  <div>
                    <div className="font-semibold">{b.name} <span className="text-xs text-muted-foreground">({b.code})</span></div>
                    <div className="text-sm text-muted-foreground">{b.description}</div>
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <form onSubmit={createBadge} className="space-y-2">
            <input name="code" className="input" placeholder="code" required />
            <input name="name" className="input" placeholder="name" required />
            <div>
              <Button type="submit">Create Badge</Button>
            </div>
          </form>
        </div>

        <div className="p-4 bg-card border border-border rounded">
          <h3 className="font-semibold mb-2">Rules</h3>
          <ul className="space-y-2 mb-4">
            {rules.map(r => (
              <li key={r.id} className="p-2 border border-border rounded bg-secondary">
                <div className="font-semibold">{r.code} <span className="text-xs text-muted-foreground">{r.rule_type}</span></div>
                <div className="text-sm text-muted-foreground">{JSON.stringify(r.params)}</div>
              </li>
            ))}
          </ul>

          <form onSubmit={createRule} className="space-y-2">
            <input name="r_code" className="input" placeholder="code" required />
            <input name="rule_type" className="input" placeholder="rule_type (e.g. first_xp, streak)" required />
            <textarea name="params" className="input" placeholder='params as JSON (e.g. {"amount":100})' />
            <div>
              <Button type="submit">Create Rule</Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
