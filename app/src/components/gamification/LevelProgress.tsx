import React from 'react';

interface Props {
  xp: number;
  level: number;
  nextThreshold: number;
}

const LevelProgress: React.FC<Props> = ({ xp, level, nextThreshold }) => {
  const progress = Math.min(100, Math.round((xp / nextThreshold) * 100));

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium">Level {level}</div>
        <div className="text-sm text-muted-foreground">{xp}/{nextThreshold} XP</div>
      </div>
      <div className="w-full h-3 bg-muted rounded overflow-hidden">
        <div
          className="h-3 bg-primary"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

export default LevelProgress;
