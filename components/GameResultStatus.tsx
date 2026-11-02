'use client';
import { useCallback, useEffect, useState } from 'react';
import { useAuth } from './AuthProvider';
import { gameProgress } from '@/lib/game-session';
import type { ResultReceipt } from '@/lib/game-progress';
export function GameResultStatus({ gameId }: { gameId: string | null }) {
  const { user } = useAuth();
  const [receipt, setReceipt] = useState<ResultReceipt | null>(null);
  const [error, setError] = useState('');
  const save = useCallback(async () => {
    if (!gameId || !user) return;
    setError('');
    try { setReceipt(await gameProgress.claimResult(gameId, user.uid)); }
    catch { setError('Could not save your result. Reconnect and retry.'); }
  }, [gameId, user]);
  useEffect(() => { setReceipt(null); void save(); }, [save]);
  if (error) return <div role="alert" className="mb-4 text-sm text-red-300">{error} <button className="underline" onClick={save}>Retry save</button></div>;
  return <p role="status" className="mb-4 text-sm text-zinc-400">{receipt ? receipt.legacy ? 'Historical result — no new rewards.' : !receipt.counted ? 'No answers submitted — statistics unchanged.' : receipt.rated ? `Result saved · Rating ${receipt.ratingChange >= 0 ? '+' : ''}${receipt.ratingChange.toFixed(1)} (${Math.round(receipt.newRating)} total)` : 'Result saved · Rating unchanged.' : 'Saving result…'}</p>;
}
export function GameSaveError({ error }: { error: string }) {
  return error ? <p role="alert" className="my-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{error}</p> : null;
}
