import { Crown, Gem, HelpCircle } from 'lucide-react';

export type RankName = 'Bronze' | 'Silver' | 'Gold' | 'Platinum' | 'Diamond' | 'Grandmaster' | 'Unrated';

export function getRankInfo(rating: number): { name: RankName; color: string; textColor: string; bgColor: string; borderColor: string } {
  if (rating >= 2500) return { name: 'Grandmaster', color: 'text-red-500', textColor: 'text-red-500', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/20' };
  if (rating >= 2000) return { name: 'Diamond', color: 'text-purple-500', textColor: 'text-purple-500', bgColor: 'bg-purple-500/10', borderColor: 'border-purple-500/20' };
  if (rating >= 1500) return { name: 'Platinum', color: 'text-cyan-400', textColor: 'text-cyan-400', bgColor: 'bg-cyan-400/10', borderColor: 'border-cyan-400/20' };
  if (rating >= 1000) return { name: 'Gold', color: 'text-yellow-500', textColor: 'text-yellow-500', bgColor: 'bg-yellow-500/10', borderColor: 'border-yellow-500/20' };
  if (rating >= 500) return { name: 'Silver', color: 'text-zinc-300', textColor: 'text-zinc-300', bgColor: 'bg-zinc-300/10', borderColor: 'border-zinc-300/20' };
  if (rating > 0) return { name: 'Bronze', color: 'text-amber-700', textColor: 'text-amber-700', bgColor: 'bg-amber-700/10', borderColor: 'border-amber-700/20' };
  return { name: 'Unrated', color: 'text-zinc-500', textColor: 'text-zinc-500', bgColor: 'bg-zinc-500/10', borderColor: 'border-zinc-500/20' };
}

function CustomStar({ points, className }: { points: number, className?: string }) {
  const cx = 12;
  const cy = 12;
  const outerRadius = 10;
  
  let innerRadius = 4;
  if (points === 3) innerRadius = 2.5;
  else if (points === 4) innerRadius = 4.5;
  else if (points === 5) innerRadius = 4.8;
  else if (points === 6) innerRadius = 5.5;
  else innerRadius = 5;

  const path = [];
  for (let i = 0; i < points * 2; i++) {
    const radius = i % 2 === 0 ? outerRadius : innerRadius;
    const angle = (i * Math.PI) / points - Math.PI / 2;
    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle);
    path.push(`${x.toFixed(2)},${y.toFixed(2)}`);
  }

  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <polygon points={path.join(' ')} />
    </svg>
  );
}

export function RankIcon({ rating, className = "w-8 h-8" }: { rating: number, className?: string }) {
  const { name, color } = getRankInfo(rating);
  const iconClass = `${className} ${color}`;

  switch (name) {
    case 'Bronze':
      return <CustomStar points={3} className={iconClass} />;
    case 'Silver':
      return <CustomStar points={4} className={iconClass} />;
    case 'Gold':
      return <CustomStar points={5} className={iconClass} />;
    case 'Platinum':
      return <CustomStar points={6} className={iconClass} />;
    case 'Diamond':
      return <Gem className={iconClass} />;
    case 'Grandmaster':
      return <Crown className={iconClass} />;
    case 'Unrated':
      return <HelpCircle className={iconClass} />;
    default:
      return <CustomStar points={5} className={iconClass} />;
  }
}
