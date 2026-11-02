'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { motion, AnimatePresence } from 'motion/react';
import { MathDisplay } from '@/components/MathDisplay';
import { ArrowRight, Zap, RefreshCw, Home, Timer, Info } from 'lucide-react';
import { OperationType, handleFirestoreError } from '@/lib/firestore-errors';
import { RankIcon, getRankInfo } from '@/components/RankDisplay';
import { generateQuestions } from '@/lib/questions';
import { playSound } from '@/lib/sounds';
import { apiRequest, gameProgress } from '@/lib/game-session';
import { nextUnanswered } from '@/lib/game-progress';
import { GameResultStatus, GameSaveError } from '@/components/GameResultStatus';
import { db } from '@/firebase';
import { doc, onSnapshot } from 'firebase/firestore';

interface Question {
  latexProblem: string;
  options: string[];
  correctIndex: number;
  explanation: string | string[];
  topic: string;
  difficulty: string;
}

export default function RapidMode() {
  const { user } = useAuth();
  const [category, setCategory] = useState('all');
  const [difficulty, setDifficulty] = useState('medium');
  const [timeLimit, setTimeLimit] = useState(60); // seconds
  
  const [loading, setLoading] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [finished, setFinished] = useState(false);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [xpEarned, setXpEarned] = useState<number | null>(null);
  const { profile } = useAuth();
  const [playerColor, setPlayerColor] = useState(profile?.color || '#eab308');
  const [gameId, setGameId] = useState<string | null>(null);
  const busy = useRef(false);
  const finishedRef = useRef(false);
  const deadlineRef = useRef(0);
  const startTimeRef = useRef(0);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6', '#d946ef', '#f43f5e'];

  const handleColorSelect = async (color: string) => {
    setPlayerColor(color);
    if (user) {
      try {
        await apiRequest('profile', { patch: { color } });
      } catch (error) {
        console.error('Failed to update color', error);
      }
    }
  };

  useEffect(() => {
    if (profile?.color) {
      setPlayerColor(profile.color);
    }
  }, [profile?.color]);
  
  const startGame = async () => {
    if (!user || busy.current) return;
    setGenerationError(''); setSaveError(''); setLoading(true);
    try {
      const generated = await generateQuestions(category, difficulty, 20, 'rapid');
      const id = await gameProgress.createGame(user.uid, 'rapid', generated, { category, difficulty, timeLimit });
      finishedRef.current = false;
      setQuestions((await gameProgress.getGame(id)).questions || []); setCurrentIndex(0); setSelectedOption(null); setScore(0);
      setTimeLeft(timeLimit); setFinished(false); setCountdown(3); setGameId(id);
    } catch (error) { setGenerationError(error instanceof Error ? error.message : 'Could not start the game.'); }
    finally { setLoading(false); }
  };

  const finishGame = useCallback(async () => {
    if (!gameId || !user || finishedRef.current) return;
    finishedRef.current = true;
    try {
      const result = await gameProgress.completeGame(gameId, user.uid);
      if (result.game.status === 'finished') { setFinished(true); playSound('end'); }
      else { deadlineRef.current = result.game.deadline || 0; finishedRef.current = false; }
    } catch (error) {
      finishedRef.current = false;
      setSaveError('Could not finish the game. Reconnecting…');
    }
  }, [gameId, user]);

  useEffect(() => {
    if (!gameId || !user) return;
    return gameProgress.watchGame(gameId, user.uid, game => {
      deadlineRef.current = game.deadline || 0; startTimeRef.current = game.startTime || 0;
      setScore(game.scores[user.uid] || 0);
      if (game.status === 'finished') { finishedRef.current = true; setFinished(true); }
    }, () => setSaveError('Game sync failed. Please reconnect.'));
  }, [gameId, user]);

  useEffect(() => {
    if (!gameId || finished) return;
    const tick = () => {
      if (!deadlineRef.current) return;
      const untilStart = Math.max(0, Math.ceil((startTimeRef.current - Date.now()) / 1000));
      setCountdown(untilStart || null);
      const remaining = Math.max(0, Math.ceil((deadlineRef.current - Math.max(Date.now(), startTimeRef.current)) / 1000));
      setTimeLeft(remaining);
      if (!untilStart && !remaining) void finishGame();
    };
    tick(); const interval = setInterval(tick, 200);
    return () => clearInterval(interval);
  }, [gameId, finished, finishGame]);

  const handleOptionSelect = (index: number) => {
    if (!saving && !finished && countdown === null) setSelectedOption(index);
  };

  const checkAnswer = async () => {
    if (busy.current || finishedRef.current || countdown !== null || selectedOption === null || !user || !gameId) return;
    busy.current = true; setSaving(true); setSaveError('');
    try {
      const result = await gameProgress.submitAnswer(gameId, user.uid, currentIndex, selectedOption);
      if (!result.answer) { setFinished(true); finishedRef.current = true; return; }
      playSound(result.answer.correct ? 'correct' : 'incorrect');
      if (result.answer.xp && !result.duplicate) {
        setXpEarned(result.answer.xp); setTimeout(() => setXpEarned(null), 2000);
      }
      deadlineRef.current = result.game.deadline || 0;
      setScore(result.game.scores[user.uid]); setSelectedOption(null);
      if (result.game.status === 'finished') { setFinished(true); finishedRef.current = true; }
      else setCurrentIndex(nextUnanswered(result.game, user.uid));
    } catch (error) { setSaveError(error instanceof Error ? error.message : 'Answer was not saved. Please retry.'); }
    finally { busy.current = false; setSaving(false); }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl text-zinc-400">Please sign in to play.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <RefreshCw className="w-12 h-12 text-yellow-500 animate-spin mb-4" />
        <p className="text-xl text-zinc-400 animate-pulse">Generating rapid problems...</p>
      </div>
    );
  }

  if (finished) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-zinc-900 border border-zinc-800 p-4 sm:p-8 rounded-3xl max-w-md w-full text-center"
        >
          <Zap className="w-20 h-20 text-yellow-500 mx-auto mb-6" />
          <h2 className="text-3xl font-bold mb-2">Rapid Complete!</h2>
          <p className="text-zinc-400 mb-8">You solved <span className="font-bold font-mono text-xl" style={{ color: playerColor }}>{score}</span> problems. This round allowed {timeLimit} seconds; wrong answers deducted 5 seconds.</p>
          
          <GameResultStatus gameId={gameId} />
          <div className="flex flex-col gap-4">
            <button 
              onClick={startGame}
              className="w-full py-3 bg-yellow-600 hover:bg-yellow-500 rounded-xl font-bold transition-colors"
            >
              Play Again
            </button>
            <button 
              onClick={() => {
                setQuestions([]);
                setFinished(false);
              }}
              className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors"
            >
              Change Settings
            </button>
            <a href="/" className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors block">
              Back to Dashboard
            </a>
          </div>
        </motion.div>
      </div>
    );
  }

  if (countdown !== null) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={countdown}
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="text-8xl font-bold text-yellow-500 font-mono"
          >
            {countdown > 0 ? countdown : 'GO!'}
          </motion.div>
        </AnimatePresence>

      </div>
    );
  }

  if (questions.length > 0) {
    const q = questions[currentIndex];

    return (
      <div className="min-h-screen max-w-4xl mx-auto px-4 py-12 relative overflow-x-clip">
        <GameSaveError error={saveError} />
        <AnimatePresence>
          {xpEarned !== null && (
             <motion.div 
               initial={{ opacity: 0, y: 20, scale: 0.8 }}
               animate={{ opacity: 1, y: 0, scale: 1 }}
               exit={{ opacity: 0, y: -20 }}
               className="pointer-events-none fixed top-24 right-10 md:right-20 bg-amber-500/20 border border-amber-500/50 text-amber-500 font-bold px-4 py-2 rounded-xl flex items-center gap-2 z-50 shadow-lg"
             >
               <span className="text-xl">+</span>
               <span className="text-2xl">{xpEarned} XP</span>
             </motion.div>
          )}
        </AnimatePresence>

        <div className="flex justify-between items-center gap-3 mb-8">
          <a href="/" className="text-zinc-400 hover:text-white flex items-center gap-2">
            <Home className="w-5 h-5" /> Quit
          </a>
          <div className={`flex items-center gap-2 font-mono text-xl sm:text-2xl font-bold ${timeLeft <= 10 ? 'text-red-500 animate-pulse' : 'text-yellow-500'}`}>
            <Timer className="w-6 h-6" />
            {timeLeft}s
          </div>
          <div className="font-bold font-mono text-xl sm:text-2xl flex items-center gap-2 whitespace-nowrap" style={{ color: playerColor }}>
            Score: 
            <motion.span
              key={score}
              initial={{ scale: 1.5, opacity: 0, y: -10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 500, damping: 15 }}
              className="inline-block"
            >
              {score}
            </motion.span>
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div 
            key={currentIndex}
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -20, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="bg-zinc-900 border border-zinc-800 rounded-3xl p-4 sm:p-8 mb-8"
          >
            <div className="text-xl sm:text-2xl mb-6 sm:mb-12 w-full overflow-x-auto py-4">
              <MathDisplay math={q.latexProblem} block />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {q.options.map((opt, i) => {
                let btnClass = "p-4 sm:p-6 rounded-2xl border text-lg transition-all text-left flex items-center gap-3 sm:gap-4 ";
                if (selectedOption === i) {
                  btnClass += "bg-zinc-800 border-yellow-500/50 text-white";
                } else {
                  btnClass += "bg-zinc-950 border-zinc-800 hover:border-yellow-500/50 hover:bg-zinc-800 cursor-pointer text-zinc-300";
                }

                return (
                  <button
                    key={i}
                    onClick={() => handleOptionSelect(i)}
                    className={btnClass}
                  >
                    <span className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm font-bold shrink-0">
                      {String.fromCharCode(65 + i)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <MathDisplay math={opt} />
                    </div>
                  </button>
                );
              })}
            </div>

            {selectedOption !== null && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-8 flex justify-center"
              >
                <button
                  onClick={checkAnswer}
                  className="px-8 py-4 bg-yellow-500 hover:bg-yellow-600 text-white rounded-2xl font-bold text-lg transition-colors flex items-center gap-2"
                >
                  Confirm Answer <Zap className="w-5 h-5" />
                </button>
              </motion.div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div className="min-h-screen max-w-3xl mx-auto px-4 py-12 flex flex-col justify-center">
      <a href="/" className="text-zinc-400 hover:text-white flex items-center gap-2 mb-12 w-fit transition-colors">
        <Home className="w-5 h-5" /> Back to Dashboard
      </a>
      
      <div className="mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-sm font-medium mb-4">
          <Zap className="w-4 h-4" />
          <span>Rapid</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">Rapid</h1>
        <p className="text-zinc-400 mt-4 text-lg">Race against the clock. How many can you solve?</p>
      </div>
      
      {generationError && <p role="alert" className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">{generationError}</p>}
      <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-3xl p-6 sm:p-10 space-y-8 backdrop-blur-sm shadow-xl">
        <div className="space-y-6">
          <div>
            <label className="flex items-center gap-2 text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider group relative w-fit">
              Category
              <Info className="w-4 h-4 text-zinc-500 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                Select the mathematical topic for the questions.
              </div>
            </label>
            <div className="relative">
              <select 
                value={category} 
                onChange={e => setCategory(e.target.value)}
                className="w-full appearance-none bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-white focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 transition-all"
              >
                <option value="all">All</option>
                <option value="integration">Integration</option>
                <option value="differentiation">Differentiation</option>
                <option value="limits">Limits</option>
                <option value="series">Series</option>
                <option value="differential equations">Differential Equations</option>
                <option value="multivariable">Multivariable Calculus</option>
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none text-zinc-500">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
              </div>
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider group relative w-fit">
              Difficulty
              <Info className="w-4 h-4 text-zinc-500 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                Higher difficulties yield more XP per correct answer.
              </div>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {['easy', 'medium', 'hard', 'olympiad'].map(diff => (
                <button
                  key={diff}
                  onClick={() => setDifficulty(diff)}
                  className={`py-3 px-4 rounded-xl border text-sm font-bold capitalize transition-all ${
                    difficulty === diff 
                      ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400' 
                      : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-900'
                  }`}
                >
                  {diff}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider group relative w-fit">
              Time Limit
              <Info className="w-4 h-4 text-zinc-500 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                The duration of the rapid fire session.
              </div>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[30, 60, 120, 300].map(time => (
                <button
                  key={time}
                  onClick={() => setTimeLimit(time)}
                  className={`py-3 px-4 rounded-xl border text-sm font-bold transition-all ${
                    timeLimit === time 
                      ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400' 
                      : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-900'
                  }`}
                >
                  {time}s
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider group relative w-fit">
              Display Color
              <svg className="w-4 h-4 text-zinc-500 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                Choose your display color for the game.
              </div>
            </label>
            <div className="flex flex-wrap gap-3">
              {colors.map(color => (
                <button
                  key={color}
                  onClick={() => handleColorSelect(color)}
                  className={`w-10 h-10 rounded-full transition-transform ${playerColor === color ? 'scale-110 ring-2 ring-white ring-offset-2 ring-offset-zinc-900' : 'hover:scale-105'}`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-zinc-800/50">
          <button 
            onClick={startGame}
            className="w-full py-4 bg-yellow-600 hover:bg-yellow-500 text-white rounded-2xl font-bold text-lg transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-yellow-500/20 flex items-center justify-center gap-2 group"
          >
            <Zap className="w-5 h-5 fill-current" /> 
            <span>Start Rapid</span>
            <ArrowRight className="w-5 h-5 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all absolute right-6" />
          </button>
        </div>
      </div>
    </div>
  );
}
