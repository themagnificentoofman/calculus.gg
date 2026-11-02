'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { db } from '@/firebase';
import { collection, query, where, getDocs, orderBy, limit } from 'firebase/firestore';
import { Trophy, Calculator, Zap, Swords, Users, Calendar, Filter, ArrowUpDown } from 'lucide-react';
import { loadRecentGames } from '@/lib/stat-queries';
import { gameStandings, type GameSession } from '@/lib/game-progress';
import { format } from 'date-fns';

interface GameRecord {
  id: string;
  mode: string;
  status: string;
  players: string[];
  scores: Record<string, number>;
  createdAt: any;
  category?: string;
  difficulty?: string;
  winner?: string;
  progressionVersion?: number;
  answers?: GameSession['answers'];
}

export function GameHistory() {
  const { user, profile } = useAuth();
  const [games, setGames] = useState<GameRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'opponents'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterMode, setFilterMode] = useState<string>('all');
  const [filterDate, setFilterDate] = useState<string>('all');

  useEffect(() => {
    let active = true;
    setGames([]); setError(''); setLoading(true);
    if (!user) { setLoading(false); return; }

    const fetchGames = async () => {
      try {
        const gameData = await loadRecentGames(db, user.uid) as GameRecord[];
        if (active) setGames(gameData);
      } catch (error) {
        if (active) setError('Game history could not be loaded.');
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchGames();
    return () => { active = false; };
  }, [user, profile?.gamesPlayed, retry]);

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'test': return <Calculator className="w-4 h-4 text-blue-500" />;
      case 'rapid': return <Zap className="w-4 h-4 text-yellow-500" />;
      case 'pvp': return <Swords className="w-4 h-4 text-red-500" />;
      case 'ffa':
      case 'multiplayer': return <Trophy className="w-4 h-4 text-purple-500" />;
      default: return <Trophy className="w-4 h-4 text-emerald-500" />;
    }
  };

  const filteredGames = games.filter(game => {
    if (filterMode !== 'all' && (game.mode === 'ffa' ? 'multiplayer' : game.mode) !== filterMode) return false;
    
    if (filterDate !== 'all' && game.createdAt) {
      const gameDate = game.createdAt.toDate ? game.createdAt.toDate() : new Date(game.createdAt);
      const now = new Date();
      const diffTime = now.getTime() - gameDate.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (filterDate === 'today' && gameDate.toDateString() !== now.toDateString()) return false;
      if (filterDate === 'week' && diffDays > 7) return false;
      if (filterDate === 'month' && diffDays > 30) return false;
    }
    
    return true;
  });

  const sortedGames = [...filteredGames].sort((a, b) => {
    if (sortBy === 'date') {
      const dateA = a.createdAt?.toDate ? a.createdAt.toDate().getTime() : new Date(a.createdAt || 0).getTime();
      const dateB = b.createdAt?.toDate ? b.createdAt.toDate().getTime() : new Date(b.createdAt || 0).getTime();
      return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    } else if (sortBy === 'score') {
      const scoreA = a.scores?.[user?.uid || ''] || 0;
      const scoreB = b.scores?.[user?.uid || ''] || 0;
      return sortOrder === 'asc' ? scoreA - scoreB : scoreB - scoreA;
    } else if (sortBy === 'opponents') {
      const oppA = a.players.length - 1;
      const oppB = b.players.length - 1;
      return sortOrder === 'asc' ? oppA - oppB : oppB - oppA;
    }
    return 0;
  });

  if (error) return <div role="alert" className="rounded-xl border border-red-500/30 p-4 text-sm text-red-300">{error} <button onClick={() => setRetry(value => value + 1)} className="ml-2 min-h-11 px-3 underline">Retry</button></div>;

  if (loading) {
    return <div className="text-center text-zinc-500 py-4">Loading history...</div>;
  }

  return (
    <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-6 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider">Recent Games (up to 50)</h3>
        
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1 bg-zinc-950/50 border border-zinc-800/50 rounded-lg p-1">
            <Filter className="w-3 h-3 text-zinc-400 ml-1" />
            <select 
              value={filterMode} 
              onChange={e => setFilterMode(e.target.value)}
              className="bg-transparent text-zinc-300 border-none outline-none cursor-pointer"
            >
              <option value="all">All Modes</option>
              <option value="test">Test</option>
              <option value="rapid">Rapid</option>
              <option value="pvp">PvP</option>
              <option value="multiplayer">Multiplayer</option>
            </select>
          </div>
          
          <div className="flex items-center gap-1 bg-zinc-950/50 border border-zinc-800/50 rounded-lg p-1">
            <Calendar className="w-3 h-3 text-zinc-400 ml-1" />
            <select 
              value={filterDate} 
              onChange={e => setFilterDate(e.target.value)}
              className="bg-transparent text-zinc-300 border-none outline-none cursor-pointer"
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
            </select>
          </div>

          <div className="flex items-center gap-1 bg-zinc-950/50 border border-zinc-800/50 rounded-lg p-1">
            <ArrowUpDown className="w-3 h-3 text-zinc-400 ml-1" />
            <select 
              value={sortBy} 
              onChange={e => setSortBy(e.target.value as any)}
              className="bg-transparent text-zinc-300 border-none outline-none cursor-pointer"
            >
              <option value="date">Date</option>
              <option value="score">Score</option>
              <option value="opponents">Opponents</option>
            </select>
            <button 
              onClick={() => setSortOrder(o => o === 'asc' ? 'desc' : 'asc')}
              className="px-2 text-zinc-400 hover:text-white"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
        {sortedGames.length === 0 ? (
          <div className="text-center text-zinc-500 py-8">
            No games found. Play some matches to see your history!
          </div>
        ) : (
          sortedGames.map(game => {
            const myScore = game.scores?.[user?.uid || ''] || 0;
            const isMultiplayer = game.mode === 'pvp' || game.mode === 'multiplayer' || game.mode === 'ffa';
            const opponentsCount = Math.max(0, game.players.length - 1);
            
            let resultText = 'Completed';
            let resultColor = 'text-zinc-400';
            
            if (isMultiplayer) {
              const outcome = gameStandings(game as GameSession).find(p => p.uid === user?.uid)?.outcome;
              resultText = outcome === 'win' ? 'Victory' : outcome === 'draw' ? 'Draw' : outcome === 'unplayed' ? 'Unplayed' : 'Defeat';
              resultColor = outcome === 'win' ? 'text-emerald-500' : outcome === 'draw' ? 'text-yellow-500' : outcome === 'unplayed' ? 'text-zinc-400' : 'text-red-500';
            }

            const gameDate = game.createdAt?.toDate ? game.createdAt.toDate() : new Date(game.createdAt || Date.now());

            return (
              <div key={game.id} className="flex items-center justify-between p-3 rounded-xl bg-zinc-950/50 border border-zinc-800/50 hover:border-zinc-700 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-zinc-900`}>
                    {getModeIcon(game.mode)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium capitalize">{game.mode === 'ffa' ? 'Multiplayer' : game.mode === 'pvp' ? 'PvP' : game.mode} Game</p>
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-zinc-900 ${resultColor}`}>
                        {resultText}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-500">
                      {Number.isNaN(gameDate.getTime()) ? 'Unknown date' : format(gameDate, 'MMM d, yyyy')} • {game.category || 'Mixed'}
                      {isMultiplayer && ` • ${opponentsCount} Opponent${opponentsCount !== 1 ? 's' : ''}`}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="font-mono text-sm font-bold text-white">{myScore}</span>
                  <p className="text-[10px] text-zinc-500 uppercase tracking-wider">Score</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
