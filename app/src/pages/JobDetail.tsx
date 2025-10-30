import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '@/components/card';
import { Button } from '@/components/button';

const JobDetail: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const token = typeof window !== 'undefined' ? localStorage.getItem('ai:token') : null;

  const headers = () => {
    const h: any = { 'Content-Type': 'application/json' };
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  };

  const fetchJob = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/jobs/${id}`, { headers: headers() });
      if (!res.ok) throw new Error('failed to fetch');
      const j = await res.json();
      setJob(j.job || null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJob();
    const t = setInterval(fetchJob, 3000);
    return () => clearInterval(t);
  }, [id]);

  const cancelJob = async () => {
    if (!id) return;
    setCancelling(true);
    try {
      const res = await fetch(`/api/v1/jobs/${id}/cancel`, { method: 'POST', headers: headers() });
      const j = await res.json();
      if (j.ok) {
        fetchJob();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCancelling(false);
    }
  };

  if (loading) return <div className="p-4">Loading...</div>;
  if (!job) return <div className="p-4">Job not found</div>;

  return (
    <div className="min-h-screen p-8 bg-gradient-hero">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">Job #{job.id}</h1>
          <div>
            <Button variant="ghost" onClick={() => navigate(-1)}>Back</Button>
            {job.status !== 'finished' && job.status !== 'failed' && (
              <Button className="ml-2" onClick={cancelJob} disabled={cancelling}>{cancelling ? 'Cancelling...' : 'Cancel Job'}</Button>
            )}
          </div>
        </div>

        <Card className="p-4 mb-4">
          <div className="mb-2"><strong>Status:</strong> {job.status}</div>
          <div className="mb-2"><strong>Language:</strong> {job.language}</div>
          <div className="mb-2"><strong>Created:</strong> {job.created_at}</div>
        </Card>

        <Card className="p-4">
          <h2 className="font-semibold mb-2">Output</h2>
          <pre className="whitespace-pre-wrap text-sm">{job.output || 'No output yet.'}</pre>
        </Card>
      </div>
    </div>
  );
};

export default JobDetail;
