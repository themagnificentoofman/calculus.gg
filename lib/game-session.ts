import { db } from '@/firebase';
import { createGameProgress } from './game-progress';
export const gameProgress = createGameProgress(db);
