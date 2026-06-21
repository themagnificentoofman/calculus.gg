'use client';

import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Trophy, Activity } from 'lucide-react';
import { collection, query, orderBy, limit, getDocs } from 'firebase/firestore';
import { db } from '@/firebase';
import { RankIcon, getRankInfo } from '@/components/RankDisplay';

type LeaderboardUser = {
  id: string;
  displayName: string;
  rating: number;
  photoURL?: string;
};

export default function LeaderboardPage() {
  const [users, setUsers] = useState<LeaderboardUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<'all-time' | 'monthly' | 'daily'>('all-time');

  useEffect(() => {
    const fetchLeaderboard = async () => {
      setLoading(true);
      try {
        const usersRef = collection(db, 'users');
        const q = query(usersRef, orderBy('rating', 'desc'), limit(100));
        const snapshot = await getDocs(q);
        
        const fetchedUsers: LeaderboardUser[] = [];
        snapshot.forEach((doc) => {
          const data = doc.data();
          fetchedUsers.push({
            id: doc.id,
            displayName: data.displayName || 'Unknown Player',
            rating: data.rating || 0,
            photoURL: data.photoURL,
          });
        });
        
        setUsers(fetchedUsers);
      } catch (error) {
        console.error('Error fetching leaderboard:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, [category]); // Re-fetch if category changes (even if it's the same data for now)

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
              <h1 className="text-4xl font-bold tracking-tight mb-2 flex items-center gap-3">
                <Trophy className="w-10 h-10 text-yellow-500" />
                Leaderboard
              </h1>
              <p className="dark:text-zinc-400 text-zinc-500">Top players ranked by Elo rating.</p>
            </div>

            <div className="flex dark:bg-zinc-900/50 bg-zinc-200/50 p-1 rounded-xl border dark:border-zinc-800/50 border-zinc-300/50 w-fit">
              {(['all-time', 'monthly', 'daily'] as const).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`px-4 py-2 rounded-lg text-sm font-bold capitalize transition-all ${
                    category === cat
                      ? 'dark:bg-zinc-800 bg-white dark:text-white text-zinc-900 shadow-sm'
                      : 'dark:text-zinc-500 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300 dark:hover:bg-zinc-800/50 hover:bg-white/50'
                  }`}
                >
                  {cat.replace('-', ' ')}
                </button>
              ))}
            </div>
          </div>

          <div className="dark:bg-zinc-900/40 bg-white border dark:border-zinc-800/50 border-zinc-200 rounded-3xl overflow-hidden backdrop-blur-sm shadow-sm">
            <div className="grid grid-cols-12 gap-4 p-4 border-b dark:border-zinc-800/50 border-zinc-200 text-xs font-bold dark:text-zinc-500 text-zinc-400 uppercase tracking-wider">
              <div className="col-span-2 sm:col-span-1 text-center">Rank</div>
              <div className="col-span-6 sm:col-span-7">Player</div>
              <div className="col-span-4 sm:col-span-4 text-right pr-4">Rating</div>
            </div>

            {loading ? (
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
                  const rankInfo = getRankInfo(user.rating);
                  return (
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      key={user.id}
                      className="grid grid-cols-12 gap-4 p-4 items-center dark:hover:bg-zinc-800/20 hover:bg-zinc-50 transition-colors"
                    >
                      <div className="col-span-2 sm:col-span-1 flex justify-center">
                        <span className="text-lg font-bold dark:text-zinc-500 text-zinc-400">#{index + 1}</span>
                      </div>
                      
                      <div className="col-span-6 sm:col-span-7 flex items-center gap-3">
                        {user.photoURL ? (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img src={user.photoURL} alt={user.displayName} className="w-10 h-10 rounded-full object-cover border dark:border-zinc-700 border-zinc-200" referrerPolicy="no-referrer" />
                        ) : (
                          <div className="w-10 h-10 bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 rounded-full flex items-center justify-center border border-emerald-500/30">
                            <span className="text-sm font-bold text-emerald-500">
                              {user.displayName.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                        <span className="font-bold dark:text-zinc-200 text-zinc-800 truncate">{user.displayName}</span>
                      </div>

                      <div className="col-span-4 sm:col-span-4 flex items-center justify-end gap-3 pr-2">
                        <div className="flex flex-col items-end">
                          <span className="font-mono font-bold text-emerald-400">{Math.round(user.rating)}</span>
                          <span className={`text-[10px] font-bold uppercase tracking-wider ${rankInfo.textColor}`}>
                            {rankInfo.name}
                          </span>
                        </div>
                        <RankIcon rating={user.rating} className="w-8 h-8 hidden sm:block" />
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
