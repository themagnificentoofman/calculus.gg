export interface SolvedProblem {
  topic: string;
  difficulty: string;
}

export interface ProgressionResult {
  xpGained: number;
  newXp: number;
  newLevel: number;
  topicXpGained: number;
  newTopicXp: number;
  newTopicLevel: number;
  ratingChange: number;
  newTopicRating: number;
  newOverallRating: number;
}

export function getLevelFromXp(xp: number): number {
  return Math.floor(Math.sqrt((xp || 0) / 100));
}

export function getXpForLevel(level: number): number {
  return 100 * Math.pow(level, 2);
}

export function getXpProgress(xp: number): { current: number; max: number; percentage: number } {
  const level = getLevelFromXp(xp);
  const currentLevelXp = getXpForLevel(level);
  const nextLevelXp = getXpForLevel(level + 1);
  const xpIntoLevel = xp - currentLevelXp;
  const xpNeeded = nextLevelXp - currentLevelXp;
  return {
    current: xpIntoLevel,
    max: xpNeeded,
    percentage: Math.min(100, Math.max(0, (xpIntoLevel / xpNeeded) * 100))
  };
}

export function calculateProblemXp(
  mode: 'test' | 'rapid' | 'pvp' | 'multiplayer',
  difficulty: string,
  placement?: number,
  totalPlayers?: number
): number {
  let base = 0;
  switch (difficulty) {
    case 'easy': base = 10; break;
    case 'medium': base = 20; break;
    case 'hard': base = 30; break;
    case 'olympiad': base = 50; break;
    default: base = 20;
  }

  let xp = base;

  // Mode multipliers
  if (mode === 'pvp') xp *= 1.5;
  if (mode === 'multiplayer') xp *= 2.0;
  if (mode === 'rapid') xp *= 1.2;

  // Placement bonus is applied per problem to scale with performance
  if (placement !== undefined && totalPlayers !== undefined && totalPlayers > 1) {
    if (placement === 1) xp *= 1.5;
    else if (placement === 2) xp *= 1.2;
    else if (placement === 3) xp *= 1.1;
  }

  return Math.floor(xp);
}

export function calculateMatchRatingChanges(
  playerRating: number,
  opponentRatings: number[],
  problems: { topic: string; difficulty: string; solved: boolean }[],
  placement?: number,
  totalPlayers?: number
): Record<string, number> {
  const avgOpponentRating = opponentRatings.length > 0 
    ? opponentRatings.reduce((a, b) => a + b, 0) / opponentRatings.length 
    : playerRating;

  const expected = 1 / (1 + Math.pow(10, (avgOpponentRating - playerRating) / 400));

  let actual = 0.5;
  if (placement !== undefined && totalPlayers !== undefined && totalPlayers > 1) {
    actual = (totalPlayers - placement) / (totalPlayers - 1); // 1st = 1, last = 0
  }

  const topicChanges: Record<string, number> = {};

  // If no opponents (e.g. Test/Rapid mode), rating doesn't change based on Elo, 
  // but we might want a small bump for solving hard problems. 
  // The prompt implies Elo is for multiplayer/PvP.
  if (opponentRatings.length === 0) {
    return topicChanges; // No rating change in solo modes
  }

  const matchMultiplier = actual - expected;

  problems.forEach(p => {
    let k = 20;
    switch (p.difficulty) {
      case 'easy': k = 16; break;
      case 'medium': k = 24; break;
      case 'hard': k = 32; break;
      case 'olympiad': k = 48; break;
    }

    // If they solved it, they get the positive/negative change based on match outcome.
    // If they failed it, they get a negative change regardless of match outcome, or a scaled change.
    // Let's simplify: the rating change is distributed across all problems encountered.
    // If actual > expected (did well), solving hard problems gives more rating.
    // If actual < expected (did poorly), failing easy problems loses more rating.
    
    let problemChange = k * matchMultiplier;
    
    // Adjust based on whether they solved this specific problem
    if (p.solved) {
      if (problemChange < 0) problemChange /= 2; // Penalized less for problems they actually solved
    } else {
      if (problemChange > 0) problemChange = 0; // Don't gain rating for problems they failed
      else problemChange *= 1.5; // Penalized more for problems they failed
    }

    if (!topicChanges[p.topic]) topicChanges[p.topic] = 0;
    topicChanges[p.topic] += problemChange;
  });

  // Normalize and cap changes per topic
  Object.keys(topicChanges).forEach(topic => {
    let change = Math.round(topicChanges[topic] / Math.max(1, problems.filter(p => p.topic === topic).length));
    if (change < -30) change = -30;
    if (change > 50) change = 50;
    topicChanges[topic] = change;
  });

  return topicChanges;
}

export function calculateOverallRating(topicRatings: Record<string, number>): number {
  const ratings = Object.values(topicRatings);
  if (ratings.length === 0) return 0;
  const sum = ratings.reduce((a, b) => a + b, 0);
  return Math.round(sum / ratings.length);
}
