'use client';

import { useAuth } from '@/components/AuthProvider';
import { motion } from 'motion/react';
import { Calculator, Play, Trophy, Users, Zap, ArrowRight, Activity, Target, Brain, Flame, Swords, HelpCircle, Star, Settings } from 'lucide-react';
import Link from 'next/link';
import { RankIcon, getRankInfo } from '@/components/RankDisplay';
import { getXpProgress, getLevelFromXp } from '@/lib/progression';

import { GameHistory } from '@/components/GameHistory';

export default function Home() {
  const { user, profile, loading, logout } = useAuth();
  const xpProgress = getXpProgress(profile?.xp || 0);
  const currentLevel = getLevelFromXp(profile?.xp || 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-emerald-500/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!user ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-4xl mx-auto mt-16 sm:mt-24"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-sm font-medium mb-8">
              <Flame className="w-4 h-4" />
              <span>The ultimate calculus training platform</span>
            </div>
            <h1 className="text-5xl sm:text-7xl font-bold tracking-tighter mb-8 leading-tight">
              Master Calculus.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                Destroy the Competition.
              </span>
            </h1>
            <p className="text-lg sm:text-xl text-zinc-400 mb-10 max-w-2xl mx-auto leading-relaxed">
              A competitive calculus trainer featuring real-time multiplayer, Elo ratings, and step-by-step LaTeX explanations powered by AI.
            </p>
            <Link
              href="/auth"
              className="group relative px-8 py-4 bg-white text-black rounded-full font-bold text-lg transition-all hover:scale-105 hover:shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)] inline-block"
            >
              <span className="flex items-center gap-2">
                Start Grinding <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 xl:grid-cols-12 gap-8"
          >
            {/* Profile Sidebar */}
            <div className="xl:col-span-4 space-y-6">
              <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-6 backdrop-blur-sm">
                <div className="flex items-center gap-5 mb-6 relative">
                  <Link href="/settings" className="absolute top-0 right-0 p-2 text-zinc-500 hover:text-white transition-colors">
                    <Settings className="w-5 h-5" />
                  </Link>
                  {profile?.photoURL ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={profile.photoURL} alt="Profile" className="w-20 h-20 rounded-2xl object-cover border border-emerald-500/30 shadow-inner" referrerPolicy="no-referrer" />
                  ) : (
                    <div className="w-20 h-20 bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 rounded-2xl flex items-center justify-center border border-emerald-500/30 shadow-inner">
                      <span className="text-3xl font-bold text-emerald-400">
                        {profile?.displayName?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div>
                    <h2 className="text-2xl font-bold tracking-tight mb-1">{profile?.displayName}</h2>
                    {profile?.handle && (
                      <div className="text-sm text-zinc-400 mb-2">@{profile.handle}</div>
                    )}
                    <div className="flex flex-col gap-2">
                      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md ${getRankInfo(profile?.rating || 0).bgColor} ${getRankInfo(profile?.rating || 0).textColor} text-xs font-bold uppercase tracking-wider w-fit`}>
                        <RankIcon rating={profile?.rating || 0} className="w-3 h-3" />
                        {getRankInfo(profile?.rating || 0).name}
                      </div>
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800 text-zinc-300 text-xs font-bold uppercase tracking-wider w-fit">
                        Level {currentLevel}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mb-8">
                  <div className="flex justify-between text-xs font-bold text-zinc-400 mb-2 uppercase tracking-wider">
                    <span>XP Progress</span>
                    <span>{Math.floor(xpProgress.current)} / {xpProgress.max}</span>
                  </div>
                  <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full transition-all duration-1000"
                      style={{ width: `${xpProgress.percentage}%` }}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <StatCard label="Rating" value={Math.round(profile?.rating || 0)} icon={<Activity className="w-4 h-4 text-emerald-500" />} />
                  <StatCard label="Matches" value={profile?.gamesPlayed || 0} icon={<Brain className="w-4 h-4 text-blue-500" />} />
                  <StatCard label="Wins" value={profile?.wins || 0} icon={<Trophy className="w-4 h-4 text-yellow-500" />} />
                  <StatCard label="Losses" value={profile?.losses || 0} icon={<XCircle className="w-4 h-4 text-red-500" />} />
                </div>
              </div>

              <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-6 backdrop-blur-sm">
                <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider mb-4">Topic Mastery</h3>
                <div className="space-y-4">
                  {['integration', 'differentiation', 'limits', 'series', 'differential equations', 'multivariable'].map(topic => {
                    const topicXp = profile?.topicXp?.[topic] || 0;
                    const topicRating = profile?.topicRatings?.[topic] || 0;
                    const topicProgress = getXpProgress(topicXp);
                    const topicLevel = getLevelFromXp(topicXp);
                    
                    return (
                      <div key={topic} className="p-3 rounded-xl bg-zinc-950/50 border border-zinc-800/50">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-bold capitalize">{topic}</span>
                          <span className="text-xs font-bold text-emerald-400">Rating: {Math.round(topicRating)}</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-bold text-zinc-500 mb-1 uppercase tracking-wider">
                          <span>Level {topicLevel}</span>
                          <span>{Math.floor(topicProgress.current)} / {topicProgress.max}</span>
                        </div>
                        <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full transition-all duration-1000"
                            style={{ width: `${topicProgress.percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <GameHistory />
            </div>

            {/* Game Modes */}
            <div className="xl:col-span-8">
              <h2 className="text-2xl font-bold tracking-tight mb-6 flex items-center gap-2">
                <Play className="w-6 h-6 text-emerald-500" /> Select Mode
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ModeCard
                  title="Test"
                  description="Practice at your own pace. Choose category, difficulty, and question count."
                  icon={<Calculator className="w-6 h-6" />}
                  href="/play/test"
                  color="from-blue-500/20 to-cyan-500/5"
                  borderColor="border-blue-500/20 hover:border-blue-500/50"
                  iconColor="text-blue-400 bg-blue-500/10"
                />
                <ModeCard
                  title="Rapid"
                  description="Race against the clock. Solve as many problems as possible before time runs out."
                  icon={<Zap className="w-6 h-6" />}
                  href="/play/rapid"
                  color="from-yellow-500/20 to-orange-500/5"
                  borderColor="border-yellow-500/20 hover:border-yellow-500/50"
                  iconColor="text-yellow-400 bg-yellow-500/10"
                />
                <ModeCard
                  title="PvP"
                  description="Head-to-head calculus battle. Race to solve the most problems. Winner takes Elo."
                  icon={<Swords className="w-6 h-6" />}
                  href="/play/pvp"
                  color="from-red-500/20 to-rose-500/5"
                  borderColor="border-red-500/20 hover:border-red-500/50"
                  iconColor="text-red-400 bg-red-500/10"
                />
                <ModeCard
                  title="Multiplayer"
                  description="Compete against multiple players. Race to a target score or battle against the clock."
                  icon={<Trophy className="w-6 h-6" />}
                  href="/play/multiplayer"
                  color="from-purple-500/20 to-pink-500/5"
                  borderColor="border-purple-500/20 hover:border-purple-500/50"
                  iconColor="text-purple-400 bg-purple-500/10"
                />
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}

function StatCard({ label, value, icon }: { label: string, value: number | string, icon: React.ReactNode }) {
  return (
    <div className="bg-zinc-950/50 rounded-2xl p-4 border border-zinc-800/50 flex flex-col justify-between">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">{label}</span>
      </div>
      <span className="text-2xl font-bold font-mono tracking-tight">{value}</span>
    </div>
  );
}

function ModeCard({ title, description, icon, href, color, borderColor, iconColor, bgImage }: { title: string, description: string, icon: React.ReactNode, href: string, color: string, borderColor: string, iconColor: string, bgImage?: string }) {
  return (
    <Link href={href} className="block h-full group">
      <div className={`relative h-full p-6 rounded-3xl border ${borderColor} bg-zinc-900/40 backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl overflow-hidden`}>
        {/* Background Gradient */}
        <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-20 group-hover:opacity-40 transition-opacity duration-500`} />
        
        {/* Decorative elements */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-white/5 rounded-full blur-3xl group-hover:bg-white/10 transition-colors duration-500" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-white/5 rounded-full blur-3xl group-hover:bg-white/10 transition-colors duration-500" />

        <div className="relative z-10 flex flex-col h-full">
          <div className={`mb-5 p-4 rounded-2xl inline-flex ${iconColor} shadow-inner w-fit`}>
            {icon}
          </div>
          <h3 className="text-2xl font-bold mb-3 text-white flex items-center justify-between">
            {title}
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
              <ArrowRight className="w-4 h-4 text-white" />
            </div>
          </h3>
          <p className="text-zinc-400 text-sm leading-relaxed flex-grow">{description}</p>
        </div>
      </div>
    </Link>
  );
}

function XCircle(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="m15 9-6 6" />
      <path d="m9 9 6 6" />
    </svg>
  );
}
