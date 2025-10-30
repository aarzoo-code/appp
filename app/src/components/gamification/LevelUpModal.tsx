import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Confetti from 'react-confetti';

interface Props {
  open: boolean;
  newLevel?: number;
  newXp?: number;
  awardedBadges?: string[];
  onClose: () => void;
}

const LevelUpModal: React.FC<Props> = ({ open, newLevel, newXp, awardedBadges, onClose }) => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  useEffect(() => {
    setDimensions({ width: window.innerWidth, height: window.innerHeight });
    const onResize = () => setDimensions({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {!prefersReducedMotion && (
            <Confetti width={dimensions.width} height={dimensions.height} recycle={false} />
          )}
          <div className="absolute inset-0 bg-black/50" onClick={onClose} />
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="relative bg-white dark:bg-card rounded-lg p-8 mx-4 max-w-lg w-full shadow-lg"
          >
            <h2 className="text-2xl font-bold mb-2">Level Up!</h2>
            <p className="text-sm text-muted-foreground mb-4">Congratulations — you reached level <strong>{newLevel}</strong>!</p>
            {typeof newXp === 'number' && (
              <p className="text-sm text-muted-foreground mb-4">Total XP: {newXp}</p>
            )}
            {awardedBadges && awardedBadges.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">New Badges</h3>
                <ul className="list-disc list-inside text-sm text-muted-foreground">
                  {awardedBadges.map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex justify-end">
              <button className="px-4 py-2 rounded bg-primary text-primary-foreground" onClick={onClose}>Close</button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default LevelUpModal;
