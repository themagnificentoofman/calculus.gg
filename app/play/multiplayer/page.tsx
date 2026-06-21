'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { motion, AnimatePresence } from 'motion/react';
import { MathDisplay } from '@/components/MathDisplay';
import { Trophy, RefreshCw, Home, Play, CheckCircle2, XCircle, ArrowRight, Globe, Users, Info } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { OperationType, handleFirestoreError } from '@/lib/firestore-errors';
import { RankIcon, getRankInfo } from '@/components/RankDisplay';
import { db } from '@/firebase';
import { collection, addDoc, doc, onSnapshot, updateDoc, arrayUnion, serverTimestamp, getDoc, query, where, limit, getDocs, increment } from 'firebase/firestore';
import { generateQuestions } from '@/lib/gemini';
import { playSound } from '@/lib/sounds';
import { calculateProblemXp, calculateMatchRatingChanges, calculateOverallRating } from '@/lib/progression';
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

interface GameData {
  mode: string;
  status: string;
  players: string[];
  scores: Record<string, number>;
  questions?: Question[];
  winner?: string;
  settings?: {
    category?: string;
    difficulty?: string;
    winCondition: 'first_to_n' | 'time_limit';
    targetScore: number;
    timeLimit: number;
    penalties: boolean;
  };
  startTime?: number;
  messages?: ChatMessage[];
}

export default function MultiplayerMode() {
  const { user, profile } = useAuth();
  const [gameId, setGameId] = useState<string | null>(null);
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Setting up arena...');
  const [xpEarned, setXpEarned] = useState<number | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [playerProfiles, setPlayerProfiles] = useState<Record<string, any>>({});
  const [statsUpdated, setStatsUpdated] = useState(false);
  const [category, setCategory] = useState('all');
  const [difficulty, setDifficulty] = useState('hard');
  
  // New Settings
  const [winCondition, setWinCondition] = useState<'first_to_n' | 'time_limit'>('first_to_n');
  const [targetScore, setTargetScore] = useState(5);
  const [timeLimit, setTimeLimit] = useState(60);
  const [penalties, setPenalties] = useState(false);
  const [playerColor, setPlayerColor] = useState(profile?.color || '#a855f7');
  const [solvedProblems, setSolvedProblems] = useState<{ topic: string; difficulty: string; solved: boolean }[]>([]);
  
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6', '#d946ef', '#f43f5e'];

  const handleColorSelect = async (color: string) => {
    setPlayerColor(color);
    if (user) {
      try {
        await updateDoc(doc(db, 'users', user.uid), { color });
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
    if (gameData?.status === 'finished' && !statsUpdated && user) {
      setStatsUpdated(true);
      const sortedPlayers = [...gameData.players].sort((a, b) => (gameData.scores[b] || 0) - (gameData.scores[a] || 0));
      const winner = sortedPlayers[0];
      const isWinner = winner === user.uid;
      const placement = sortedPlayers.indexOf(user.uid) + 1;
      const totalPlayers = sortedPlayers.length;
      const myScore = gameData.scores[user.uid] || 0;
      
      const gameCategory = gameData.settings?.category || 'integration';
      const gameDifficulty = gameData.settings?.difficulty || 'hard';
      
      const opponentRatings = sortedPlayers
        .filter(uid => uid !== user.uid)
        .map(uid => playerProfiles[uid]?.rating || 0); // Use overall rating for expected performance
        
      const myRating = profile?.rating || 0;
      
      const allMatchProblems = gameData.questions?.map((q, index) => {
        // Find if the user answered this question
        const solvedRecord = solvedProblems[index];
        // If they didn't answer it, they failed it
        return {
          topic: q.topic,
          difficulty: q.difficulty,
          solved: solvedRecord ? solvedRecord.solved : false
        };
      }) || [];

      const ratingChanges = calculateMatchRatingChanges(
        myRating,
        opponentRatings,
        allMatchProblems,
        placement,
        totalPlayers
      );

      let totalXpBonus = 0;
      const topicXpUpdates: Record<string, any> = {};
      
      solvedProblems.forEach(p => {
        if (p.solved) {
          const baseXp = calculateProblemXp('multiplayer', p.difficulty);
          const totalXp = calculateProblemXp('multiplayer', p.difficulty, placement, totalPlayers);
          const bonusXp = totalXp - baseXp;
          totalXpBonus += bonusXp;
          if (!topicXpUpdates[`topicXp.${p.topic}`]) {
            topicXpUpdates[`topicXp.${p.topic}`] = 0;
          }
          topicXpUpdates[`topicXp.${p.topic}`] += bonusXp;
        }
      });

      import('firebase/firestore').then(({ doc, updateDoc, increment }) => {
        import('@/firebase').then(({ db }) => {
          const currentTopicRatings = profile?.topicRatings || {};
          const newTopicRatings = { ...currentTopicRatings };
          
          for (const topic in ratingChanges) {
            newTopicRatings[topic] = (newTopicRatings[topic] || 0) + ratingChanges[topic];
          }
          
          const newOverallRating = calculateOverallRating(newTopicRatings);

          // Convert topicXpUpdates to increments
          for (const key in topicXpUpdates) {
            topicXpUpdates[key] = increment(topicXpUpdates[key]);
          }

          const ratingUpdates: Record<string, any> = {};
          for (const topic in ratingChanges) {
            ratingUpdates[`topicRatings.${topic}`] = newTopicRatings[topic];
          }

          updateDoc(doc(db, 'users', user.uid), {
            gamesPlayed: increment(1),
            wins: increment(isWinner ? 1 : 0),
            losses: increment(!isWinner ? 1 : 0),
            xp: increment(totalXpBonus),
            ...topicXpUpdates,
            ...ratingUpdates,
            rating: newOverallRating
          }).catch(error => handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`));
        });
      });
    }
  }, [gameData?.status, statsUpdated, user, gameData?.scores, gameData?.players, gameData?.settings, profile, playerProfiles, solvedProblems, gameData?.questions]);

  useEffect(() => {
    if (!gameId) return;

    const unsub = onSnapshot(doc(db, 'games', gameId), async (docSnap) => {
      if (docSnap.exists()) {
        const data = docSnap.data() as GameData;
        setGameData(data);
        
        // Fetch profiles for players we don't have yet
        for (const uid of data.players) {
          setPlayerProfiles(prev => {
            if (!prev[uid]) {
              getDoc(doc(db, 'users', uid)).then(pSnap => {
                if (pSnap.exists()) {
                  setPlayerProfiles(p => ({ ...p, [uid]: pSnap.data() }));
                }
              }).catch(error => handleFirestoreError(error, OperationType.GET, `users/${uid}`));
            }
            return prev;
          });
        }
      }
    }, (error) => handleFirestoreError(error, OperationType.GET, `games/${gameId}`));

    return () => unsub();
  }, [gameId]);

  const hostId = gameData?.players?.[0];

  useEffect(() => {
    if (gameData?.status === 'active' && gameData.settings?.winCondition === 'time_limit' && gameData.startTime) {
      const interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - gameData.startTime!) / 1000);
        const remaining = Math.max(0, gameData.settings!.timeLimit - elapsed);
        setTimeLeft(remaining);
        
        if (remaining === 0 && hostId === user?.uid) {
          // Host finishes the game
          import('firebase/firestore').then(({ doc, updateDoc }) => {
            import('@/firebase').then(({ db }) => {
              updateDoc(doc(db, 'games', gameId!), {
                status: 'finished'
              });
            });
          });
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [gameData?.status, gameData?.settings, gameData?.startTime, hostId, gameId, user?.uid]);

  const createGame = async () => {
    if (!user) return;
    setLoadingMessage('Generating questions...');
    setLoading(true);
    try {
      const questionsCount = winCondition === 'first_to_n' ? Math.min(targetScore * 3, 20) : 20;
      const generatedQuestions = await generateQuestions(category, difficulty, questionsCount);
      
      if (generatedQuestions) {
        try {
          const docRef = await addDoc(collection(db, 'games'), {
            mode: 'multiplayer',
            status: 'waiting',
            players: [user.uid],
            scores: { [user.uid]: 0 },
            questions: generatedQuestions,
            settings: {
              category,
              difficulty,
              winCondition,
              targetScore,
              timeLimit,
              penalties
            },
            createdAt: serverTimestamp(),
          });
          setGameId(docRef.id);
        } catch (error) {
          handleFirestoreError(error, OperationType.CREATE, 'games');
        }
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const joinGame = async (idToJoin: string) => {
    if (!user) return;
    setJoinError('');
    
    // Validation
    const trimmedId = idToJoin.trim();
    if (!trimmedId) {
      setJoinError('Game ID is required.');
      return;
    }
    if (trimmedId.length < 5 || trimmedId.length > 30) {
      setJoinError('Game ID must be between 5 and 30 characters.');
      return;
    }
    if (!/^[a-zA-Z0-9]+$/.test(trimmedId)) {
      setJoinError('Game ID can only contain letters and numbers.');
      return;
    }

    setLoadingMessage('Joining game...');
    setLoading(true);
    try {
      const gameRef = doc(db, 'games', trimmedId);
      let gameSnap;
      try {
        gameSnap = await getDoc(gameRef);
      } catch (error) {
        handleFirestoreError(error, OperationType.GET, `games/${trimmedId}`);
        return;
      }
      if (gameSnap.exists()) {
        const data = gameSnap.data() as GameData;
        if (data.status === 'waiting' && !data.players.includes(user.uid)) {
          try {
            await updateDoc(gameRef, {
              players: arrayUnion(user.uid),
              [`scores.${user.uid}`]: 0,
            });
          } catch (error) {
            handleFirestoreError(error, OperationType.UPDATE, `games/${trimmedId}`);
          }
          setGameId(trimmedId);
        } else if (data.players.includes(user.uid)) {
          setGameId(trimmedId); // Rejoin
        } else {
          setJoinError("Game has already started or is finished.");
        }
      } else {
        setJoinError("Game not found. Please check the ID and try again.");
      }
    } catch (error) {
      console.error(error);
      setJoinError("An error occurred while joining the game.");
    } finally {
      setLoading(false);
    }
  };

  const joinRandomGame = async () => {
    if (!user) return;
    setLoadingMessage('Finding an available arena...');
    setLoading(true);
    try {
      const gamesRef = collection(db, 'games');
      const q = query(gamesRef, where('mode', '==', 'multiplayer'), where('status', '==', 'waiting'), limit(10));
      let querySnapshot;
      try {
        querySnapshot = await getDocs(q);
      } catch (error) {
        handleFirestoreError(error, OperationType.LIST, 'games');
        return;
      }
      
      let joined = false;
      for (const docSnap of querySnapshot.docs) {
        const data = docSnap.data() as GameData;
        if (data.players.length < 10 && !data.players.includes(user.uid)) {
          try {
            await updateDoc(doc(db, 'games', docSnap.id), {
              players: arrayUnion(user.uid),
              [`scores.${user.uid}`]: 0,
            });
          } catch (error) {
            handleFirestoreError(error, OperationType.UPDATE, `games/${docSnap.id}`);
          }
          setGameId(docSnap.id);
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
    if (!gameId) return;
    try {
      await updateDoc(doc(db, 'games', gameId), {
        status: 'active',
        startTime: Date.now()
      });
    } catch (error) {
      handleFirestoreError(error, OperationType.UPDATE, `games/${gameId}`);
    }
  };

  const handleOptionSelect = (index: number) => {
    if (showExplanation || !gameData || !gameData.questions || !user || !gameId) return;
    setSelectedOption(index);
  };

  const checkAnswer = async () => {
    if (selectedOption === null || showExplanation || !gameData || !gameData.questions || !user || !gameId) return;
    
    const q = gameData.questions[currentIndex];
    const isCorrect = selectedOption === q.correctIndex;
    
    setSolvedProblems(prev => [...prev, {
      topic: q.topic,
      difficulty: q.difficulty,
      solved: isCorrect
    }]);
    
    if (isCorrect) {
      playSound('correct');
      const newScore = (gameData.scores[user.uid] || 0) + 1;
      try {
        await updateDoc(doc(db, 'games', gameId), {
          [`scores.${user.uid}`]: newScore
        });

        // Continuous saving
        const xp = calculateProblemXp('multiplayer', q.difficulty);
        const topicKey = `topicXp.${q.topic}`;
        setXpEarned(xp);
        setTimeout(() => setXpEarned(null), 2000);
        await updateDoc(doc(db, 'users', user.uid), {
          xp: increment(xp),
          [topicKey]: increment(xp)
        });

        if (gameData.settings?.winCondition === 'first_to_n' && newScore >= gameData.settings.targetScore) {
          await updateDoc(doc(db, 'games', gameId), {
            status: 'finished'
          });
        }
      } catch (error) {
        handleFirestoreError(error, OperationType.UPDATE, `games/${gameId}`);
      }
    } else {
      playSound('incorrect');
      if (gameData.settings?.penalties) {
        const newScore = (gameData.scores[user.uid] || 0) - 1;
        try {
          await updateDoc(doc(db, 'games', gameId), {
            [`scores.${user.uid}`]: newScore
          });
        } catch (error) {
          handleFirestoreError(error, OperationType.UPDATE, `games/${gameId}`);
        }
      }
    }
    
    setShowExplanation(true);
  };

  const nextQuestion = async () => {
    if (!gameData || !gameData.questions || !gameId) return;
    
    if (currentIndex < gameData.questions.length - 1) {
      setCurrentIndex(i => i + 1);
      setSelectedOption(null);
      setShowExplanation(false);
    } else {
      playSound('end');
      // Finish game
      try {
        await updateDoc(doc(db, 'games', gameId), {
          status: 'finished'
        });
      } catch (error) {
        handleFirestoreError(error, OperationType.UPDATE, `games/${gameId}`);
      }
    }
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
        <RefreshCw className="w-12 h-12 text-purple-500 animate-spin mb-4" />
        <p className="text-xl text-zinc-400 animate-pulse">{loadingMessage}</p>
      </div>
    );
  }

  if (!gameId) {
    return (
      <div className="min-h-screen max-w-3xl mx-auto px-4 py-12 flex flex-col justify-center">
        <Link href="/" className="text-zinc-400 hover:text-white flex items-center gap-2 mb-12 w-fit transition-colors">
          <Home className="w-5 h-5" /> Back to Dashboard
        </Link>
        
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium mb-4">
            <Trophy className="w-4 h-4" />
            <span>Multiplayer</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">Multiplayer</h1>
          <p className="text-zinc-400 mt-4 text-lg">Join a global arena and compete against multiple players.</p>
        </div>
        
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
                  Determines the complexity of the problems. Higher difficulties yield higher rating rewards.
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
                  <div className="flex-1 flex gap-2">
                    <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 flex items-center gap-2">
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
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 font-mono transition-all"
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
          className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl max-w-md w-full text-center"
        >
          <Trophy className="w-20 h-20 text-purple-500 mx-auto mb-6 animate-pulse" />
          <h2 className="text-3xl font-bold mb-2">Lobby</h2>
          <p className="text-zinc-400 mb-8">Share this Game ID with your friends:</p>
          
          <div className="bg-zinc-950 border border-zinc-800 p-4 rounded-xl mb-8 font-mono text-xl text-purple-400 select-all">
            {gameId}
          </div>

          <div className="mb-8 text-left bg-zinc-950 border border-zinc-800 p-4 rounded-xl">
            <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider mb-4">Game Settings</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-400">Category:</span>
                <span className="text-white capitalize">{gameData.settings?.category || 'Integration'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Difficulty:</span>
                <span className="text-white capitalize">{gameData.settings?.difficulty || 'Hard'}</span>
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
                    <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-500 font-bold">
                      {playerProfiles[p]?.displayName?.charAt(0) || '?'}
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <span>{playerProfiles[p]?.displayName || 'Loading...'}</span>
                    {playerProfiles[p]?.rating !== undefined && (
                      <RankIcon rating={playerProfiles[p]?.rating} className="w-4 h-4" />
                    )}
                  </div>
                  {p === gameData.players[0] && <span className="ml-auto text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">HOST</span>}
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

          <Link href="/" className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors block">
            Leave Lobby
          </Link>
        </motion.div>
      </div>
    );
  }

  if (gameData?.status === 'finished') {
    // Sort scores
    const sortedPlayers = [...gameData.players].sort((a, b) => (gameData.scores[b] || 0) - (gameData.scores[a] || 0));
    const winner = sortedPlayers[0];
    const isWinner = winner === user.uid;

    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl max-w-md w-full text-center"
        >
          {isWinner ? (
            <div className="text-purple-500 text-6xl mb-6">👑</div>
          ) : (
            <div className="text-zinc-500 text-6xl mb-6">👏</div>
          )}
          
          <h2 className="text-3xl font-bold mb-8">
            {isWinner ? 'You Won!' : 'Game Over'}
          </h2>
          
          <div className="space-y-3 mb-8 text-left">
            {sortedPlayers.map((p, i) => (
              <div key={p} className={`flex items-center justify-between p-4 rounded-xl border ${p === user.uid ? 'bg-purple-500/10 border-purple-500/30' : 'bg-zinc-950 border-zinc-800'}`}>
                <div className="flex items-center gap-3">
                  <span className="text-zinc-500 font-mono font-bold w-4">{i + 1}.</span>
                  <div className="flex items-center gap-2">
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
                      <div className="w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-500 font-bold text-xs">
                        {playerProfiles[p]?.displayName?.charAt(0) || '?'}
                      </div>
                    )}
                    <span className={p === user.uid ? 'font-bold' : 'text-white'} style={p === user.uid ? { color: playerColor } : { color: playerProfiles[p]?.color || '#ffffff' }}>
                      {playerProfiles[p]?.displayName || 'Unknown'}
                    </span>
                    {playerProfiles[p]?.rating !== undefined && (
                      <RankIcon rating={playerProfiles[p]?.rating} className="w-4 h-4" />
                    )}
                  </div>
                </div>
                <motion.span 
                  key={gameData.scores[p] || 0}
                  initial={{ scale: 1.5, opacity: 0, y: -10 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 15 }}
                  className="font-mono font-bold inline-block"
                  style={p === user.uid ? { color: playerColor } : { color: playerProfiles[p]?.color || '#ffffff' }}
                >
                  {gameData.scores[p] || 0}
                  {gameData.settings?.winCondition === 'first_to_n' && <span className="text-zinc-500 text-xs ml-1">/ {gameData.settings.targetScore}</span>}
                </motion.span>
              </div>
            ))}
          </div>
          
          <div className="flex flex-col gap-4">
            <button 
              onClick={() => setGameId(null)}
              className="w-full py-3 bg-purple-600 hover:bg-purple-500 rounded-xl font-bold transition-colors"
            >
              Play Again
            </button>
            <Link href="/" className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors block">
              Back to Dashboard
            </Link>
          </div>
        </motion.div>
        <Chat gameId={gameId!} messages={gameData.messages || []} />
      </div>
    );
  }

  if (gameData?.status === 'active' && gameData.questions) {
    const q = gameData.questions[currentIndex];
    const isCorrect = selectedOption === q?.correctIndex;
    
    // Sort players by score for the leaderboard
    const sortedPlayers = [...gameData.players].sort((a, b) => (gameData.scores[b] || 0) - (gameData.scores[a] || 0));

    return (
      <div className="min-h-screen max-w-6xl mx-auto px-4 py-12 flex gap-8 flex-col lg:flex-row relative">
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
        <div className="flex-1">
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
                className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 mb-8"
              >
                <div className="text-2xl mb-12 w-full overflow-x-auto py-4">
                  <MathDisplay math={q.latexProblem} block />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {q.options.map((opt, i) => {
                    let btnClass = "p-6 rounded-2xl border text-lg transition-all text-left flex items-center gap-4 ";
                    
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
                        <div className="w-full">
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
              className={`p-6 rounded-2xl border mb-8 ${isCorrect ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}
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
                  {currentIndex < gameData.questions.length - 1 ? 'Next Question' : 'Finish Match'}
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
                  <div className="flex items-center gap-3">
                    <span className="text-zinc-500 font-mono font-bold w-4">{i + 1}.</span>
                    <div className="flex items-center gap-1.5">
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
                        <div className="w-5 h-5 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-500 font-bold text-[10px]">
                          {playerProfiles[p]?.displayName?.charAt(0) || '?'}
                        </div>
                      )}
                      <span className={`text-sm ${p === user.uid ? 'font-bold' : 'text-zinc-300'}`} style={p === user.uid ? { color: playerColor } : { color: playerProfiles[p]?.color || '#d4d4d8' }}>
                        {playerProfiles[p]?.displayName?.split(' ')[0] || 'Unknown'}
                      </span>
                      {playerProfiles[p]?.rating !== undefined && (
                        <RankIcon rating={playerProfiles[p]?.rating} className="w-3 h-3" />
                      )}
                    </div>
                  </div>
                  <motion.span 
                    key={gameData.scores[p] || 0}
                    initial={{ scale: 1.5, opacity: 0, y: -10 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 15 }}
                    className="font-mono font-bold inline-block"
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
