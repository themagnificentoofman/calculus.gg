'use client';

import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Trophy, Activity } from 'lucide-react';
import { collection, query, orderBy, limit, getDocs } from 'firebase/firestore';
import { loadLeaderboard } from '@/lib/stat-queries';
import { useAuth } from '@/components/AuthProvider';
import { db } from '@/firebase';
import { RankIcon, getRankInfo } from '@/components/RankDisplay';

type LeaderboardUser = {
  id: string;
  displayName: string;
  rating: number;
  photoURL?: string;
};

export default function LeaderboardPage() {
  const { user: currentUser, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<LeaderboardUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!currentUser) { setLoading(false); setError('Sign in to view the leaderboard.'); return; }
    const fetchLeaderboard = async () => {
      setError('');
      setLoading(true);
      try {
        const rows = await loadLeaderboard(db);
        const fetchedUsers = rows.map((data: any) => ({
          id: data.id, displayName: data.displayName || 'Unknown Player',
          rating: data.rating || 0, photoURL: data.photoURL,
        }));
        setUsers(fetchedUsers);
      } catch (error) {
        console.error('Error fetching leaderboard:', error);
        setError('Could not load the leaderboard. Please refresh to retry.');
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, [currentUser, authLoading]);

  return (
    <main className="min-h-screen dark:text-zinc-50 text-zinc-900 font-sans selection:bg-emerald-500/30">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-2 flex items-center gap-3">
                <Trophy className="shrink-0 w-8 h-8 sm:w-10 sm:h-10 text-yellow-500" />
                Leaderboard
              </h1>
              <p className="dark:text-zinc-400 text-zinc-500">Top players ranked by rating.</p>
            </div>

            <span className="text-sm text-zinc-500">All-time rating</span>
          </div>

          <div className="dark:bg-zinc-900/90 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-3xl overflow-hidden backdrop-blur-sm shadow-sm">
            <div className="grid grid-cols-[2.5rem_minmax(0,1fr)_4.5rem] gap-2 p-3 sm:grid-cols-12 sm:gap-4 sm:p-4 border-b dark:border-zinc-800/50 border-zinc-200 text-xs font-bold dark:text-zinc-500 text-zinc-400 uppercase tracking-wider">
              <div className="sm:col-span-1 text-center">Rank</div>
              <div className="sm:col-span-7">Player</div>
              <div className="sm:col-span-4 text-right sm:pr-4">Rating</div>
            </div>

            {error ? <p role="alert" className="p-6 text-red-400">{error}</p> : loading ? (
              <div className="p-12 flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-emerald-500"></div>
              </div>
            ) : users.length === 0 ? (
              <div className="p-12 text-center dark:text-zinc-500 text-zinc-400">
                No players found.
              </div>
            ) : (
              <div className="divide-y dark:divide-zinc-800/50 divide-zinc-200">
                {users.map((user, index) => {
                  const position = users.findIndex(other => Math.round(other.rating) === Math.round(user.rating)) + 1;
                  const rankInfo = getRankInfo(user.rating, true);
                  return (
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      key={user.id}
                      className="grid grid-cols-[2.5rem_minmax(0,1fr)_4.5rem] gap-2 p-3 sm:grid-cols-12 sm:gap-4 sm:p-4 items-center dark:hover:bg-zinc-800/20 hover:bg-zinc-50 transition-colors"
                    >
                      <div className="sm:col-span-1 flex justify-center">
                        <span className="text-lg font-bold dark:text-zinc-500 text-zinc-400">#{position}</span>
                      </div>
                      
                      <div className="sm:col-span-7 min-w-0 flex items-center gap-2 sm:gap-3">
                        {user.photoURL ? (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img src={user.photoURL} alt={user.displayName} className="shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-full object-cover border dark:border-zinc-700 border-zinc-200" referrerPolicy="no-referrer" />
                        ) : (
                          <div className="shrink-0 w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 rounded-full flex items-center justify-center border border-emerald-500/30">
                            <span className="text-sm font-bold text-emerald-500">
                              {user.displayName.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                        <span title={user.displayName} className="min-w-0 text-sm sm:text-base font-bold dark:text-zinc-200 text-zinc-800 truncate">{user.displayName}</span>
                      </div>

                      <div className="sm:col-span-4 flex items-center justify-end gap-2 sm:gap-3 sm:pr-2">
                        <div className="flex flex-col items-end">
                          <span className="font-mono font-bold text-emerald-400">{Math.round(user.rating)}</span>
                          <span className={`text-[10px] font-bold tracking-normal sm:uppercase sm:tracking-wider ${rankInfo.textColor}`}>
                            {rankInfo.name}
                          </span>
                        </div>
                        <RankIcon rated rating={user.rating} className="w-8 h-8 hidden sm:block" />
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </main>
  );
}
