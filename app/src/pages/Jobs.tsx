import React, { useEffect, useState } from 'react';
import { Card } from '@/components/card';
import { Button } from '@/components/button';
import { Input } from '@/components/input';
import { Link } from 'react-router-dom';

interface JobItem {
  id: number;
  status: string;
  created_at?: string;
}

const Jobs = () => {
  const [command, setCommand] = useState('python -c "print(1+1)"');
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const token = typeof window !== 'undefined' ? localStorage.getItem('ai:token') : null;

  const headers = () => {
    const h: any = { 'Content-Type': 'application/json' };
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  };

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/jobs', { headers: headers() });
      if (!res.ok) throw new Error('failed');
      const j = await res.json();
      setJobs(j.jobs || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    // poll every 5s
    const t = setInterval(fetchJobs, 5000);
    return () => clearInterval(t);
  }, []);

  const submitJob = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch('/api/v1/jobs', {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ language: 'python', payload: { command } }),
      });
      const j = await res.json();
      if (j.ok) {
        setCommand('python -c "print(1+1)"');
        fetchJobs();
      } else {
        console.error('submit failed', j);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gradient-hero">
      <div className="container mx-auto px-4">
        <h1 className="text-2xl font-bold mb-4">Jobs</h1>

        <Card className="p-4 mb-6">
          <form onSubmit={submitJob} className="space-y-3">
            <div>
              <label className="text-sm mb-1 block">Command</label>
              <Input value={command} onChange={(e) => setCommand((e.target as HTMLInputElement).value)} />
            </div>
            <div>
              <Button type="submit" disabled={submitting}>{submitting ? 'Submitting...' : 'Submit Job'}</Button>
            </div>
          </form>
        </Card>

        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-3">Recent Jobs</h2>
          {loading ? (
            <div>Loading jobs...</div>
          ) : (
            <div className="space-y-2">
              {jobs.length === 0 && <div className="text-sm text-muted-foreground">No jobs yet.</div>}
              {jobs.map((j) => (
                <Link key={j.id} to={`/jobs/${j.id}`} className="block">
                  <div className="p-2 border border-border rounded flex justify-between items-center hover:bg-muted">
                    <div>
                      <div className="font-medium">Job #{j.id}</div>
                      <div className="text-xs text-muted-foreground">{j.created_at || ''}</div>
                    </div>
                    <div className="text-sm">
                      <span className={`px-2 py-1 rounded ${j.status === 'finished' ? 'bg-green-200 text-green-800' : j.status === 'failed' ? 'bg-red-200 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>{j.status}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Jobs;
