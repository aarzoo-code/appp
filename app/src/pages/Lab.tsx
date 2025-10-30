import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import LevelUpModal from "../components/gamification/LevelUpModal";

const Lab = () => {
  const [fileName, setFileName] = useState<string | null>(null);

  useEffect(() => {
    // Load last lab title if present
    const last = localStorage.getItem("ai:last_lab");
    if (last) setFileName(last);
  }, []);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
    }
  };

  const [levelUp, setLevelUp] = useState<{open: boolean; newLevel?: number; newXp?: number}>({ open: false });

  const awardXp = async (xp: number) => {
    try {
      const resp = await fetch('/api/v1/xp/award', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 1, xp, source: 'lab', source_id: fileName || 'manual' }),
      });
      const data = await resp.json();
      if (data?.leveled_up) {
        setLevelUp({ open: true, newLevel: data.new_level, newXp: data.new_xp });
      }
    } catch (err) {
      // fallback: localStorage credit
      const key = 'ai:stats';
      const cur = JSON.parse(localStorage.getItem(key) || '{}');
      cur.xp = (cur.xp || 0) + xp;
      localStorage.setItem(key, JSON.stringify(cur));
      setLevelUp({ open: true, newLevel: cur.level || 1, newXp: cur.xp });
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gradient-hero">
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm mb-6">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-primary">
            AI Lab
          </Link>
          <div />
        </div>
      </nav>

      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-foreground mb-4">Lab Environment (Stub)</h1>
        <p className="text-muted-foreground mb-4">This is a placeholder for the interactive lab. We'll integrate notebooks and runtimes later.</p>

        <div className="mb-6">
          <label className="block text-sm text-muted-foreground mb-2">Upload dataset (CSV)</label>
          <input type="file" accept=".csv" onChange={handleUpload} />
          {fileName && <p className="mt-2 text-sm">Selected: {fileName}</p>}
        </div>

        <div className="mb-6">
          <label className="block text-sm text-muted-foreground mb-2">Code Playground</label>
          <div className="rounded border border-border bg-card p-4 text-sm text-muted-foreground">Code editor placeholder — run cells here in a future iteration.</div>
        </div>

        <div>
          <button
            className="px-4 py-2 rounded bg-primary text-primary-foreground"
            onClick={() => awardXp(100)}
          >
            Run (complete lab)
          </button>
        </div>
      </div>
      <LevelUpModal open={levelUp.open} newLevel={levelUp.newLevel} newXp={levelUp.newXp} onClose={() => setLevelUp({ open: false })} />
    </div>
  );
};

export default Lab;
