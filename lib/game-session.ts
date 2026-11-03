import {observeReplay} from './replay/browser-events';
import { auth, db } from '@/firebase';
import { collection, doc, onSnapshot, query, where } from 'firebase/firestore';
import type { GameMode } from './progression';
import type { GameSession } from './game-progress';
export async function apiRequest(resource: string, body: Record<string, unknown>) {
  const user = auth.currentUser;
  if (!user) throw new Error('Please sign in.');
  const response = await fetch(`/api/${resource}`, { method: 'POST', headers: { Authorization: `Bearer ${await user.getIdToken()}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: AbortSignal.timeout(resource === 'questions' ? 85000 : 30000) });
  const payload = await response.json().catch(() => null) as Record<string, any> | null;
  if (!response.ok || !payload) throw new Error(payload?.error || 'The server could not save this operation. Please retry.');
  return payload;
}
export function gameView(game: any, progress: any = {}) {
  return { ...game, questions: (game.questions || []).map((q: any, index: number) => ({ ...q, correctIndex: -1, explanation: [], ...progress.reviews?.[index] })),
    answers: { ...game.answers, ...(auth.currentUser && progress.answers ? { [auth.currentUser.uid]: progress.answers } : {}) } } as GameSession;
}
const command = async (action: string, gameId?: string, data = {}) => {
  const result = await apiRequest('games', { action, ...(gameId ? { gameId } : {}), ...data });
  if (result.game) result.game = gameView(result.game, result.progress);
  return result;
};
export const gameProgress = {
  async createGame(_uid: string, mode: GameMode, set: { questionSetId: string }, options: any) {
    return (await apiRequest('games', { action: 'create', mode, questionSetId: set.questionSetId, options })).id as string;
  },
  async getGame(id: string) { return (await command('view', id)).game as GameSession; },
  joinGame: (id: string, _uid: string, mode: string) => command('join', id, { mode }),
  leaveGame: (id: string) => command('leave', id),
  startGame: (id: string, _uid: string) => command('start', id),
  async submitAnswer(id:string,uid:string,index:number,selectedOption:number){
    const key=`answer-request:${uid}:${id}:${index}`;let requestId=crypto.randomUUID();
    try{requestId=sessionStorage.getItem(key)||requestId;sessionStorage.setItem(key,requestId);}catch{}
    observeReplay(id,'submission_started',{questionIndex:index,selectedOption,requestId});
    try{const result=await command('answer',id,{index,selectedOption,requestId});observeReplay(id,'answer_response',{questionIndex:index,requestId,serverEventId:result.answer?.serverEventId});return result;}
    catch(error){observeReplay(id,'submission_rejected',{questionIndex:index,requestId,reason:'transport-uncertain'});throw error;}
  },
  completeGame: (id: string, _uid: string) => command('complete', id),
  async claimResult(id: string, _uid: string) { return (await command('claim', id)).receipt; },
  syncPendingResults: (_uid: string) => command('sync'),
  watchGame(id: string, uid: string, callback: (game: GameSession) => void, onError: (error: unknown) => void) {
    let game: any, progress: any;
    const emit = () => {
      if (!game || !progress) return;
      const committed = Object.keys(game.answers?.[uid] || {}), reviewed = Object.keys(progress.answers || {});
      if (committed.length !== reviewed.length || committed.some(i => !progress.answers?.[i])) return;
      callback(gameView(game, progress));
    };
    const a = onSnapshot(doc(db, 'games', id), s => { if (s.exists()) { game = s.data(); emit(); } }, onError);
    const b = onSnapshot(doc(db, 'games', id, 'reviews', uid), s => { progress = s.data() || {}; emit(); }, onError);
    return () => { a(); b(); };
  },
  watchPendingResults(uid: string, onError: (error: unknown) => void) {
    let stopped = false, syncing = false;
    const sync = async () => { if (stopped || syncing) return; syncing = true; try { await command('sync'); } catch (e) { if (!stopped) onError(e); } finally { syncing = false; } };
    void sync();
    const interval = setInterval(sync, 30000);
    const timers = new Map<string, ReturnType<typeof setTimeout>>();
    const stop = onSnapshot(query(collection(db, 'games'), where('players', 'array-contains', uid), where('status', '==', 'active')), snapshot => {
      for (const timer of timers.values()) clearTimeout(timer); timers.clear();
      for (const row of snapshot.docs) { const g = row.data(); if (g.progressionVersion === 3 && g.deadline) timers.set(row.id, setTimeout(sync, Math.max(0, g.deadline - Date.now()) + 50)); }
    }, onError);
    return () => { stopped = true; stop(); clearInterval(interval); for (const timer of timers.values()) clearTimeout(timer); };
  },
};
