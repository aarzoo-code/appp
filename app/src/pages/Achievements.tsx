import React from 'react';
import BadgeGrid from '../components/gamification/BadgeGrid';

const Achievements: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Achievements</h1>
      <p className="text-muted-foreground mb-4">Your badges and accomplishments.</p>
      <BadgeGrid />
    </div>
  );
};

export default Achievements;
