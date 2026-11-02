import { finite, getStandings, type GameMode } from './progression.ts';

export interface GameQuestion { latexProblem: string; options: string[]; correctIndex: number; explanation: string | string[]; topic: string; difficulty: string }
export interface SavedAnswer { selectedOption: number; correct: boolean; xp: number; timeMs: number }
export interface MatchSettings { category?: string; difficulty?: string; winCondition: 'first_to_n' | 'time_limit'; targetScore: number; timeLimit: number; penalties: boolean }
export interface ResultReceipt { ratingChange: number; newRating: number; topicChanges: Record<string, number>; outcome: string; rank: number; rated: boolean; counted: boolean; legacy?: boolean }
export interface GameSession {
  mode: GameMode; status: 'waiting' | 'active' | 'finished'; players: string[]; scores: Record<string, number>;
  questions?: GameQuestion[]; category?: string; difficulty?: string; settings?: MatchSettings;
  startTime?: number; deadline?: number; finishedAt?: number; createdAt?: unknown;
  progressionVersion?: number; answers?: Record<string, Record<string, SavedAnswer>>;
  ratingSnapshot?: Record<string, { rating: number; topicRatings: Record<string, number> }>;
  completedPlayers?: string[]; pendingClaims?: string[]; receipts?: Record<string, ResultReceipt>;
  timeline?: Record<string, { questionIndex: number; timeMs: number }[]>;
  messages?: { senderId: string; senderName: string; text: string; timestamp: number }[]; winner?: string;
}
export function gamePlayers(game: GameSession) {
  return game.players.map(uid => {
    const answers = game.answers?.[uid] || {};
    return { uid, score: finite(game.scores[uid]), attempted: (game.progressionVersion || 0) >= 2 ? Object.keys(answers).length : 1,
      correct: Object.values(answers).filter(a => a.correct).length, answers,
      rating: finite(game.ratingSnapshot?.[uid]?.rating), topicRatings: game.ratingSnapshot?.[uid]?.topicRatings || {} };
  });
}
export const gameStandings = (game: GameSession) => getStandings(gamePlayers(game));
export const isCompetitive = (game: GameSession) => game.mode === 'pvp' || game.mode === 'multiplayer';
export const nextUnanswered = (game: GameSession, uid: string) => {
  const index = (game.questions || []).findIndex((_, i) => !game.answers?.[uid]?.[i]);
  return index === -1 ? (game.questions || []).length : index;
};
