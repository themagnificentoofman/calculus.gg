'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { motion, AnimatePresence } from 'motion/react';
import { MathDisplay } from '@/components/MathDisplay';
import { LastAnswerReview, type AnsweredQuestion } from '@/components/LastAnswerReview';
import { Trophy, RefreshCw, Home, Play, CheckCircle2, XCircle, ArrowRight, Globe, Users, Info } from 'lucide-react';
import Image from 'next/image';
import { OperationType, handleFirestoreError } from '@/lib/firestore-errors';
import { RankIcon, getRankInfo } from '@/components/RankDisplay';
import { db } from '@/firebase';
import { doc, getDoc } from 'firebase/firestore';
import { generateQuestions } from '@/lib/questions';
import { playSound } from '@/lib/sounds';
import { loadWaitingGames } from '@/lib/stat-queries';
import { hasRating } from '@/lib/progression';
import { apiRequest, gameProgress } from '@/lib/game-session';
import { gameStandings, nextUnanswered, type GameSession } from '@/lib/game-progress';
import { GameResultStatus, GameSaveError } from '@/components/GameResultStatus';
import { Chat } from '@/components/Chat';

interface ChatMessage {
  senderId: string;
  senderName: string;
  text: string;
  timestamp: number;
}

interface Question {
  latexProblem: string;
  options: string[];
  correctIndex: number;
  explanation: string | string[];
  topic: string;
  difficulty: string;
}

type GameData = GameSession;

export default function MultiplayerMode() {
  const [match, setMatch] = useState(0);
  return <MultiplayerMatch key={match} onPlayAgain={() => setMatch(value => value + 1)} />;
}

function MultiplayerMatch({ onPlayAgain }: { onPlayAgain: () => void }) {
  const { user, profile, loading: authLoading } = useAuth();
  const [leaving, setLeaving] = useState(false);
  const [gameId, setGameId] = useState<string | null>(null);
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [loading, setLoading] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [loadingMessage, setLoadingMessage] = useState('Setting up arena...');
  const [xpEarned, setXpEarned] = useState<number | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [lastAnswer, setLastAnswer] = useState<AnsweredQuestion | null>(null);
  const [playerProfiles, setPlayerProfiles] = useState<Record<string, any>>({});
  const busy = useRef(false);
  const restoredGame = useRef<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [category, setCategory] = useState('all');
  const [difficulty, setDifficulty] = useState('hard');
  
  // New Settings
  const [winCondition, setWinCondition] = useState<'first_to_n' | 'time_limit'>('first_to_n');
  const [targetScore, setTargetScore] = useState(5);
  const [timeLimit, setTimeLimit] = useState(60);
  const [penalties, setPenalties] = useState(false);
  const [playerColor, setPlayerColor] = useState(profile?.color || '#a855f7');
  
  const ratingFor = (uid: string) => gameData?.receipts?.[uid]?.newRating ?? playerProfiles[uid]?.rating ?? 0;
  const ratedFor = (uid: string) => gameData?.receipts?.[uid]?.rated || hasRating(playerProfiles[uid]);

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
  
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [joinError, setJoinError] = useState('');

  // Load settings from local storage
  useEffect(() => {
    const savedSettings = localStorage.getItem('multiplayerSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        if (parsed.category) setCategory(parsed.category);
        if (parsed.difficulty) setDifficulty(parsed.difficulty);
        if (parsed.winCondition) setWinCondition(parsed.winCondition);
        if (parsed.targetScore) setTargetScore(parsed.targetScore);
        if (parsed.timeLimit) setTimeLimit(parsed.timeLimit);
        if (parsed.penalties !== undefined) setPenalties(parsed.penalties);
      } catch (e) {
        console.error('Failed to parse saved settings', e);
      }
    }
  }, []);

  // Save settings to local storage when they change
  useEffect(() => {
    const settingsToSave = {
      category,
      difficulty,
      winCondition,
      targetScore,
      timeLimit,
      penalties
    };
    localStorage.setItem('multiplayerSettings', JSON.stringify(settingsToSave));
  }, [category, difficulty, winCondition, targetScore, timeLimit, penalties]);

  useEffect(() => {
    if (!gameId || !user || leaving) return;

    const unsub = gameProgress.watchGame(gameId, user!.uid, async (view) => {
      {
        const data = view as GameData;
        if (data.status === 'cancelled') { setGameId(null); setGameData(null); setGenerationError('This lobby was cancelled or expired. Start or join a new game.'); return; }
        setGameData(data);
        if (user && restoredGame.current !== gameId) {
          restoredGame.current = gameId;
          setCurrentIndex(data.progressionVersion === 3 ? nextUnanswered(data, user.uid) : 0);
          setSelectedOption(null); setShowExplanation(false);
        }
        
        // Fetch profiles for players we don't have yet
        for (const uid of data.players) {
          setPlayerProfiles(prev => {
            if (!prev[uid]) {
              getDoc(doc(db, 'users_public', uid)).then(pSnap => {
                if (pSnap.exists()) {
                  setPlayerProfiles(p => ({ ...p, [uid]: pSnap.data() }));
                }
              }).catch(() => setSaveError('A player profile could not be loaded. Please reconnect.'));
            }
            return prev;
          });
        }
      }
    }, () => setSaveError('Game sync failed. Please reconnect.'));

    return () => unsub();
  }, [gameId, user, leaving]);

  const hostId = gameData?.players?.[0];

  useEffect(() => {
    if (!gameId || !user || gameData?.status !== 'active' || !gameData.deadline) return;
    let ending = false;
    const tick = async () => {
      const remaining = Math.max(0, Math.ceil((gameData.deadline! - Date.now()) / 1000));
      setTimeLeft(remaining);
      if (remaining === 0 && !ending) {
        ending = true;
        try { await gameProgress.completeGame(gameId, user.uid); }
        catch { setSaveError('Could not finish the match. Reconnecting…'); }
        finally { ending = false; }
      }
    };
    void tick(); const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [gameId, user, gameData?.status, gameData?.deadline]);

  const createGame = async () => {
    setGenerationError('');
    if (!user) return;
    setLoadingMessage('Generating questions...');
    setLoading(true);
    try {
      const questionsCount = winCondition === 'first_to_n' ? Math.min(targetScore * 3, 20) : 20;
      const generatedQuestions = await generateQuestions(category, difficulty, questionsCount, 'multiplayer');
      
      if (generatedQuestions) {
        try {
          const docRef = { id: await gameProgress.createGame(user.uid, 'multiplayer', generatedQuestions, { category, difficulty, settings: { winCondition, targetScore, timeLimit, penalties } }) };
          setGameId(docRef.id);
        } catch (error) {
          handleFirestoreError(error, OperationType.CREATE, 'games');
        }
      }
    } catch (error) {
      setGenerationError(error instanceof Error ? error.message : 'Could not generate questions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const joinGame = async (idToJoin: string) => {
    if (!user) return;
    setLoading(true); setGenerationError('');
    try {
      const id = idToJoin.trim();
      if (!/^[a-zA-Z0-9]{5,30}$/.test(id)) throw new Error('Enter a valid game ID.');
      await gameProgress.joinGame(id, user.uid, 'multiplayer');
      setGameId(id);
    } catch (error) { setGenerationError(error instanceof Error ? error.message : 'Could not join this game.'); }
    finally { setLoading(false); }
  };

  const joiningFromLink = useRef(false);
  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('join');
    if (user && id && !joiningFromLink.current) { joiningFromLink.current = true; void joinGame(id); }
  }, [user]);

  const joinRandomGame = async () => {
    if (!user) return;
    setLoadingMessage('Finding an available arena...');
    setLoading(true);
    try {
      const matches = await loadWaitingGames(db, user.uid, 'multiplayer');

      let joined = false;
      for (const data of matches) {
        if (data.players.length < 10 && !data.players.includes(user.uid)) {
          try {
            await gameProgress.joinGame(data.id, user.uid, 'multiplayer');
          } catch { continue; }
          setGameId(data.id);
          joined = true;
          break;
        }
      }
      
      if (!joined) {
        await createGame();
      }
    } catch (error) {
      console.error(error);
      await createGame();
    } finally {
      if(!gameId) setLoading(false);
    }
  };

  const startGame = async () => {
    if (!gameId || !user) return;
    try { await gameProgress.startGame(gameId, user.uid); }
    catch (error) { setSaveError(error instanceof Error ? error.message : 'Could not start this game.'); }
  };

  const handleOptionSelect = (index: number) => {
    if (saving || showExplanation || !gameData || !gameData.questions || !user || !gameId) return;
    setSelectedOption(index);
  };

  const checkAnswer = async () => {
    if (busy.current || selectedOption === null || showExplanation || !gameData?.questions || !user || !gameId || gameData.status !== 'active') return;
    busy.current = true; setSaving(true); setSaveError('');
    try {
      const q = gameData.questions[currentIndex];
      const result = await gameProgress.submitAnswer(gameId, user.uid, currentIndex, selectedOption);
      if (!result.answer) return;
      setSelectedOption(result.answer.selectedOption);
      setGameData(result.game as GameData);
      setLastAnswer({ question: result.game.questions[currentIndex], selectedOption: result.answer.selectedOption });
      playSound(result.answer.correct ? 'correct' : 'incorrect');
      if (result.answer.xp && !result.duplicate) {
        setXpEarned(result.answer.xp); setTimeout(() => setXpEarned(null), 2000);
      }
      setShowExplanation(true);
    } catch (error) { setSaveError(error instanceof Error ? error.message : 'Answer was not saved. Please retry.'); }
    finally { busy.current = false; setSaving(false); }
  };

  const nextQuestion = () => {
    if (saving || !showExplanation) return;
    setCurrentIndex(currentIndex + 1); setSelectedOption(null); setShowExplanation(false);
  };

  const leaveLobby = async () => {
    if (!gameId || leaving) return;
    setLeaving(true); setSaveError('');
    try { await gameProgress.leaveGame(gameId); setGameId(null); setGameData(null); }
    catch (error) { setSaveError(error instanceof Error ? error.message : 'Could not leave the lobby. Please retry.'); }
    finally { setLeaving(false); }
  };

  if (authLoading) return <main className="p-8 text-center text-zinc-400" role="status">Loading your account…</main>;

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
        <RefreshCw className="w-12 h-12 text-purple-500 animate-spin mb-4" />
        <p className="text-xl text-zinc-400 animate-pulse">{loadingMessage}</p>
      </div>
    );
  }

  if (!gameId) {
    return (
      <div className="min-h-screen max-w-3xl mx-auto px-4 py-12 flex flex-col justify-center">
        <a href="/" className="text-zinc-400 hover:text-white flex items-center gap-2 mb-12 w-fit transition-colors">
          <Home className="w-5 h-5" /> Back to Dashboard
        </a>
        
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium mb-4">
            <Trophy className="w-4 h-4 shrink-0" />
            <span>Multiplayer</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">Multiplayer</h1>
          <p className="text-zinc-400 mt-4 text-lg">Join a global arena and compete against multiple players.</p>
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
                <select aria-label="Category"
                  value={category} 
                  onChange={e => setCategory(e.target.value)}
                  className="w-full appearance-none bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
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
                  Determines the complexity of the problems. Harder problems earn more XP. Rating depends on results and opponent strength.
                </div>
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {['easy', 'medium', 'hard', 'olympiad'].map(diff => (
                  <button
                    key={diff}
                    onClick={() => setDifficulty(diff)}
                    className={`py-3 px-4 rounded-xl border text-sm font-bold capitalize transition-all ${
                      difficulty === diff 
                        ? 'bg-purple-500/20 border-purple-500 text-purple-400' 
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
                Win Condition
                <Info className="w-4 h-4 text-zinc-500 cursor-help" />
                <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                  Choose how the game ends: either the first player to reach a target score, or the player with the highest score when time runs out.
                </div>
              </label>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <button
                  onClick={() => setWinCondition('first_to_n')}
                  className={`py-3 px-4 rounded-xl border text-sm font-bold transition-all ${
                    winCondition === 'first_to_n'
                      ? 'bg-purple-500/20 border-purple-500 text-purple-400'
                      : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-900'
                  }`}
                >
                  First to N
                </button>
                <button
                  onClick={() => setWinCondition('time_limit')}
                  className={`py-3 px-4 rounded-xl border text-sm font-bold transition-all ${
                    winCondition === 'time_limit'
                      ? 'bg-purple-500/20 border-purple-500 text-purple-400'
                      : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-900'
                  }`}
                >
                  Time Limit
                </button>
              </div>

              {winCondition === 'first_to_n' ? (
                <div className="mb-4">
                  <label className="flex items-center gap-2 text-sm font-bold text-zinc-400 mb-2 group relative w-fit">
                    Target Score
                    <Info className="w-4 h-4 text-zinc-500 cursor-help" />
                    <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                      The number of correct answers needed to win the game.
                    </div>
                  </label>
                  <div className="flex items-center gap-4">
                    <input 
                      type="range" 
                      min="1" 
                      max="20" 
                      value={targetScore} 
                      onChange={e => setTargetScore(parseInt(e.target.value) || 5)}
                      className="flex-1 h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                    <div className="w-16 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center font-mono font-bold text-xl text-purple-400">
                      {targetScore}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mb-4">
                  <label className="flex items-center gap-2 text-sm font-bold text-zinc-400 mb-2 group relative w-fit">
                    Time Limit (seconds)
                    <Info className="w-4 h-4 text-zinc-500 cursor-help" />
                    <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                      The duration of the game. The player with the highest score at the end wins.
                    </div>
                  </label>
                  <div className="flex items-center gap-4">
                    <input 
                      type="range" 
                      min="30" 
                      max="300" 
                      step="30"
                      value={timeLimit} 
                      onChange={e => setTimeLimit(parseInt(e.target.value) || 60)}
                      className="flex-1 h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                    <div className="w-16 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center font-mono font-bold text-xl text-purple-400">
                      {timeLimit}s
                    </div>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3 mt-6">
                <input
                  type="checkbox"
                  id="penalties"
                  checked={penalties}
                  onChange={e => setPenalties(e.target.checked)}
                  className="w-5 h-5 rounded border-zinc-800 bg-zinc-950 text-purple-500 focus:ring-purple-500 focus:ring-offset-zinc-900"
                />
                <label htmlFor="penalties" className="flex items-center gap-2 text-sm font-bold text-zinc-300 group relative w-fit cursor-pointer">
                  Enable Penalties (-1 point for incorrect answers)
                  <Info className="w-4 h-4 text-zinc-500" />
                  <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                    If enabled, answering a question incorrectly will reduce your score by 1 point.
                  </div>
                </label>
              </div>

              <div className="mt-6">
                <label className="flex items-center gap-2 text-sm font-bold text-zinc-400 mb-2 group relative w-fit">
                  Display Color
                  <Info className="w-4 h-4 text-zinc-500 cursor-help" />
                  <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                    Choose your display color for multiplayer games.
                  </div>
                </label>
                <div className="flex items-center gap-4">
                  <div 
                    className="w-12 h-12 rounded-full border-2 border-zinc-700 overflow-hidden relative shrink-0"
                    style={{ backgroundColor: playerColor }}
                  >
                    <input
                      type="color"
                      value={playerColor}
                      onChange={(e) => handleColorSelect(e.target.value)}
                      className="absolute inset-[-10px] w-[200%] h-[200%] cursor-pointer opacity-0"
                    />
                  </div>
                  <div className="min-w-0 flex-1 flex gap-2">
                    <div className="min-w-0 flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 flex items-center gap-2">
                      <span className="text-zinc-500 font-mono text-xs">HEX</span>
                      <input 
                        type="text" 
                        value={playerColor.toUpperCase()}
                        onChange={(e) => {
                          const val = e.target.value;
                          if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                            handleColorSelect(val);
                          }
                        }}
                        className="bg-transparent border-none focus:outline-none text-white font-mono text-sm w-full uppercase"
                        maxLength={7}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-zinc-800/50 flex flex-col sm:flex-row gap-4">
            <button 
              onClick={createGame}
              className="flex-1 py-4 bg-purple-600 hover:bg-purple-500 text-white rounded-2xl font-bold text-lg transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-purple-500/20 flex items-center justify-center gap-2 group"
            >
              <Globe className="w-5 h-5 fill-current" /> 
              <span>Create Arena</span>
            </button>
            <button 
              onClick={joinRandomGame}
              className="flex-1 py-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-2xl font-bold text-lg transition-all hover:scale-[1.02] flex items-center justify-center gap-2 group"
            >
              <Users className="w-5 h-5" /> 
              <span>Find Match</span>
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-800/50"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-zinc-900/50 text-zinc-500 font-bold uppercase tracking-wider">OR JOIN EXISTING</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider">Game ID</label>
            <div className="flex gap-2">
              <input 
                type="text" 
                id="join-id"
                placeholder="Enter Game ID..."
                className="min-w-0 flex-1 bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 font-mono transition-all"
              />
              <button 
                onClick={() => {
                  const input = document.getElementById('join-id') as HTMLInputElement;
                  if (input.value) joinGame(input.value);
                }}
                className="px-8 bg-zinc-800 hover:bg-zinc-700 text-white rounded-2xl font-bold transition-all hover:scale-[1.02]"
              >
                Join
              </button>
            </div>
            {joinError && (
              <p className="text-red-400 text-sm mt-2">{joinError}</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (gameData?.status === 'waiting') {
    const isHost = gameData.players[0] === user.uid;

    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-zinc-900 border border-zinc-800 p-4 sm:p-8 rounded-3xl max-w-md w-full text-center"
        >
          <Trophy className="w-20 h-20 text-purple-500 mx-auto mb-6 animate-pulse" />
          <h2 className="text-3xl font-bold mb-2">Lobby</h2>
          <p className="text-zinc-400 mb-8">Share this Game ID with your friends:</p>
          
          <div className="bg-zinc-950 border border-zinc-800 p-4 rounded-xl mb-8 font-mono text-base sm:text-xl break-all text-purple-400 select-all">
            {gameId}
          </div>

          <div className="mb-8 text-left bg-zinc-950 border border-zinc-800 p-4 rounded-xl">
            <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider mb-4">Game Settings</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-400">Category:</span>
                <span className="text-white capitalize">{gameData.category || 'all'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Difficulty:</span>
                <span className="text-white capitalize">{gameData.difficulty || 'medium'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Win Condition:</span>
                <span className="text-white capitalize">{gameData.settings?.winCondition === 'first_to_n' ? 'First to N' : 'Time Limit'}</span>
              </div>
              {gameData.settings?.winCondition === 'first_to_n' ? (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Target Score:</span>
                  <span className="text-white">{gameData.settings?.targetScore}</span>
                </div>
              ) : (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Time Limit:</span>
                  <span className="text-white">{gameData.settings?.timeLimit}s</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-zinc-400">Penalties:</span>
                <span className="text-white">{gameData.settings?.penalties ? 'Enabled' : 'Disabled'}</span>
              </div>
            </div>
          </div>

          <div className="mb-8 text-left">
            <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider mb-4">Players ({gameData.players.length}/10)</h3>
            <div className="space-y-2">
              {gameData.players.map(p => (
                <div key={p} className="bg-zinc-950 border border-zinc-800 p-3 rounded-lg flex items-center gap-3">
                  {playerProfiles[p]?.photoURL ? (
                    <Image 
                      src={playerProfiles[p].photoURL} 
                      alt={playerProfiles[p].displayName || 'Player'} 
                      width={32} 
                      height={32} 
                      className="rounded-full"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="w-8 h-8 shrink-0 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-500 font-bold">
                      {playerProfiles[p]?.displayName?.charAt(0) || '?'}
                    </div>
                  )}
                  <div className="min-w-0 flex-1 flex items-center gap-2">
                    <span className="min-w-0 break-words">{playerProfiles[p]?.displayName || 'Loading...'}</span>
                    {playerProfiles[p]?.rating !== undefined && (
                      <RankIcon rated={ratedFor(p)} rating={ratingFor(p)} className="w-4 h-4 shrink-0" />
                    )}
                  </div>
                  {p === gameData.players[0] && <span className="ml-auto shrink-0 text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">HOST</span>}
                </div>
              ))}
            </div>
          </div>
          
          {isHost ? (
            <button 
              onClick={startGame}
              className="w-full py-3 bg-purple-600 hover:bg-purple-500 rounded-xl font-bold transition-colors mb-4"
            >
              Start Game
            </button>
          ) : (
            <p className="text-zinc-400 mb-4 animate-pulse">Waiting for host to start...</p>
          )}

          <GameSaveError error={saveError} />
          {saveError && <p role="alert" className="my-3 text-sm text-red-300">{saveError}</p>}
          <button disabled={leaving} onClick={leaveLobby} className="w-full min-h-11 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors disabled:opacity-50">
            {leaving ? 'Leaving…' : 'Leave Lobby'}
          </button>
        </motion.div>
      </div>
    );
  }

  if (gameData?.status === 'finished') {
    const standings = gameStandings(gameData);
    const sortedPlayers = standings.map(p => p.uid);
    const outcome = standings.find(p => p.uid === user.uid)?.outcome;
    const isWinner = outcome === 'win';

    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-zinc-900 border border-zinc-800 p-4 sm:p-8 rounded-3xl max-w-md w-full text-center"
        >
          {isWinner ? (
            <div className="text-purple-500 text-6xl mb-6">👑</div>
          ) : (
            <div className="text-zinc-500 text-6xl mb-6">👏</div>
          )}
          
          <h2 className="text-3xl font-bold mb-8">
            {isWinner ? 'You Won!' : outcome === 'draw' ? 'Draw!' : 'Game Over'}
          </h2>
          
          <div className="space-y-3 mb-8 text-left">
            {sortedPlayers.map((p, i) => (
              <div key={p} className={`flex items-center justify-between p-4 rounded-xl border ${p === user.uid ? 'bg-purple-500/10 border-purple-500/30' : 'bg-zinc-950 border-zinc-800'}`}>
                <div className="min-w-0 flex-1 flex items-center gap-3">
                  <span className="text-zinc-500 font-mono font-bold w-4">{standings.find(s => s.uid === p)?.rank}.</span>
                  <div className="min-w-0 flex-1 flex items-center gap-2">
                    {playerProfiles[p]?.photoURL ? (
                      <Image 
                        src={playerProfiles[p].photoURL} 
                        alt={playerProfiles[p].displayName || 'Player'} 
                        width={24} 
                        height={24} 
                        className="rounded-full"
                        referrerPolicy="no-referrer"
                      />
                    ) : (
                      <div className="w-6 h-6 shrink-0 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-500 font-bold text-xs">
                        {playerProfiles[p]?.displayName?.charAt(0) || '?'}
                      </div>
                    )}
                    <span className={`min-w-0 break-words ${p === user.uid ? 'font-bold' : 'text-white'}`} style={p === user.uid ? { color: playerColor } : { color: playerProfiles[p]?.color || '#ffffff' }}>
                      {playerProfiles[p]?.displayName || 'Unknown'}
                    </span>
                    {playerProfiles[p]?.rating !== undefined && (
                      <RankIcon rated={ratedFor(p)} rating={ratingFor(p)} className="w-4 h-4 shrink-0" />
                    )}
                  </div>
                </div>
                <motion.span 
                  key={gameData.scores[p] || 0}
                  initial={{ scale: 1.5, opacity: 0, y: -10 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 15 }}
                  className="shrink-0 ml-3 whitespace-nowrap font-mono font-bold inline-block"
                  style={p === user.uid ? { color: playerColor } : { color: playerProfiles[p]?.color || '#ffffff' }}
                >
                  {gameData.scores[p] || 0}
                  {gameData.settings?.winCondition === 'first_to_n' && <span className="text-zinc-500 text-xs ml-1">/ {gameData.settings.targetScore}</span>}
                </motion.span>
              </div>
            ))}
          </div>
          
          <GameResultStatus gameId={gameId} />
          <LastAnswerReview answer={lastAnswer} />

          <div className="flex flex-col gap-4">
            <button 
              onClick={onPlayAgain}
              className="w-full py-3 bg-purple-600 hover:bg-purple-500 rounded-xl font-bold transition-colors"
            >
              Play Again
            </button>
            <GameSaveError error={saveError} />
          <a href="/" className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors block">
              Back to Dashboard
            </a>
          </div>
        </motion.div>
        <Chat gameId={gameId!} messages={gameData.messages || []} />
      </div>
    );
  }

  if (gameData?.status === 'active' && currentIndex >= (gameData.questions?.length || 0)) {
    return <div className="min-h-screen max-w-2xl mx-auto px-4 py-24 text-center">
      <h2 className="text-2xl font-bold mb-4">Your questions are complete</h2>
      <p className="text-zinc-400">Waiting for the other players or the match deadline. Your answers and XP are saved.</p>
      <GameSaveError error={saveError} />
      <a className="inline-block mt-6 underline" href="/">Back to Dashboard</a>
      <Chat gameId={gameId!} messages={gameData.messages || []} />
    </div>;
  }

  if (gameData?.status === 'active' && gameData.questions) {
    const q = gameData.questions[currentIndex];
    const isCorrect = selectedOption === q?.correctIndex;
    
    // Sort players by score for the leaderboard
    const standings = gameStandings(gameData);
    const sortedPlayers = standings.map(p => p.uid);

    return (
      <div className="min-h-screen max-w-6xl mx-auto px-4 py-12 flex gap-8 flex-col lg:flex-row relative overflow-x-clip">
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
        
        {/* Main Game Area */}
        <div className="min-w-0 flex-1">
          <div className="flex justify-between items-center mb-8 bg-zinc-900/50 p-4 rounded-2xl border border-zinc-800">
            <div className="text-zinc-400 font-mono text-sm">
              Question {currentIndex + 1} of {gameData.questions.length}
            </div>
            {gameData.settings?.winCondition === 'time_limit' && timeLeft !== null && (
              <div className="text-purple-400 font-mono font-bold text-xl">
                {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
              </div>
            )}
            {gameData.settings?.winCondition === 'first_to_n' && (
              <div className="text-purple-400 font-mono font-bold text-sm">
                Target: {gameData.settings.targetScore} pts
              </div>
            )}
          </div>

          {q && (
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
                    
                    if (!showExplanation) {
                      if (selectedOption === i) {
                        btnClass += "bg-zinc-800 border-purple-500/50 text-white";
                      } else {
                        btnClass += "bg-zinc-950 border-zinc-800 hover:border-purple-500/50 hover:bg-zinc-800 cursor-pointer text-zinc-300";
                      }
                    } else {
                      if (i === q.correctIndex) {
                        btnClass += "bg-emerald-500/20 border-emerald-500 text-emerald-400";
                      } else if (i === selectedOption) {
                        btnClass += "bg-red-500/20 border-red-500 text-red-400";
                      } else {
                        btnClass += "bg-zinc-950 border-zinc-800 opacity-50";
                      }
                    }

                    return (
                      <button
                        key={i}
                        disabled={showExplanation}
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

                {!showExplanation && selectedOption !== null && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-8 flex justify-center"
                  >
                    <button
                      onClick={checkAnswer}
                      className="px-8 py-4 bg-purple-500 hover:bg-purple-600 text-white rounded-2xl font-bold text-lg transition-colors flex items-center gap-2"
                    >
                      Confirm Answer <CheckCircle2 className="w-5 h-5" />
                    </button>
                  </motion.div>
                )}
              </motion.div>
            </AnimatePresence>
          )}

          {showExplanation && q && (
            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className={`p-4 sm:p-6 rounded-2xl border mb-8 ${isCorrect ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}
            >
              <div className="flex items-center gap-3 mb-4">
                {isCorrect ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-500" />
                )}
                <h3 className={`text-xl font-bold ${isCorrect ? 'text-emerald-500' : 'text-red-500'}`}>
                  {isCorrect ? 'Correct!' : 'Incorrect.'}
                </h3>
              </div>
              
              <div className="prose prose-invert max-w-none">
                <h4 className="text-zinc-300 font-medium mb-2">Explanation:</h4>
                <div className="text-zinc-400 leading-relaxed w-full flex flex-col gap-4">
                  {Array.isArray(q.explanation) ? (
                    q.explanation.map((step: string, idx: number) => (
                      <div key={idx} className="w-full">
                        <MathDisplay math={step} block />
                      </div>
                    ))
                  ) : (
                    <MathDisplay math={q.explanation} block />
                  )}
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <button 
                  onClick={nextQuestion}
                  className="flex items-center gap-2 px-6 py-3 bg-white text-black rounded-full font-bold hover:bg-zinc-200 transition-colors"
                >
                  {currentIndex < gameData.questions.length - 1 ? 'Next Question' : 'View Match Status'}
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}
        </div>

        {/* Sidebar Leaderboard */}
        <div className="w-full lg:w-80 shrink-0">
          <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 sticky top-8">
            <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-purple-500" /> Live Standings
            </h3>
            <div className="space-y-3">
              {sortedPlayers.map((p, i) => (
                <div key={p} className={`flex items-center justify-between p-3 rounded-xl border ${p === user.uid ? 'bg-purple-500/10 border-purple-500/30' : 'bg-zinc-950 border-zinc-800'}`}>
                  <div className="min-w-0 flex-1 flex items-center gap-3">
                    <span className="text-zinc-500 font-mono font-bold w-4">{standings.find(s => s.uid === p)?.rank}.</span>
                    <div className="min-w-0 flex-1 flex items-center gap-1.5">
                      {playerProfiles[p]?.photoURL ? (
                        <Image 
                          src={playerProfiles[p].photoURL} 
                          alt={playerProfiles[p].displayName || 'Player'} 
                          width={20} 
                          height={20} 
                          className="rounded-full"
                          referrerPolicy="no-referrer"
                        />
                      ) : (
                        <div className="w-5 h-5 shrink-0 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-500 font-bold text-[10px]">
                          {playerProfiles[p]?.displayName?.charAt(0) || '?'}
                        </div>
                      )}
                      <span title={playerProfiles[p]?.displayName} className={`min-w-0 truncate text-sm ${p === user.uid ? 'font-bold' : 'text-zinc-300'}`} style={p === user.uid ? { color: playerColor } : { color: playerProfiles[p]?.color || '#d4d4d8' }}>
                        {playerProfiles[p]?.displayName?.split(' ')[0] || 'Unknown'}
                      </span>
                      {playerProfiles[p]?.rating !== undefined && (
                        <RankIcon rated={ratedFor(p)} rating={ratingFor(p)} className="w-3 h-3 shrink-0" />
                      )}
                    </div>
                  </div>
                  <motion.span 
                    key={gameData.scores[p] || 0}
                    initial={{ scale: 1.5, opacity: 0, y: -10 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 15 }}
                    className="shrink-0 ml-3 whitespace-nowrap font-mono font-bold inline-block"
                    style={p === user.uid ? { color: playerColor } : { color: playerProfiles[p]?.color || '#c084fc' }}
                  >
                    {gameData.scores[p] || 0}
                    {gameData.settings?.winCondition === 'first_to_n' && <span className="text-zinc-500 text-xs ml-1">/ {gameData.settings.targetScore}</span>}
                  </motion.span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <Chat gameId={gameId!} messages={gameData.messages || []} />
      </div>
    );
  }

  return null;
}
