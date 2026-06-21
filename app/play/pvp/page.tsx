'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { motion, AnimatePresence } from 'motion/react';
import { MathDisplay } from '@/components/MathDisplay';
import { Users, RefreshCw, Home, Play, CheckCircle2, XCircle, ArrowRight, Swords, Info } from 'lucide-react';
import Link from 'next/link';
import { OperationType, handleFirestoreError } from '@/lib/firestore-errors';
import { RankIcon, getRankInfo } from '@/components/RankDisplay';
import { db } from '@/firebase';
import { collection, addDoc, doc, onSnapshot, updateDoc, arrayUnion, serverTimestamp, getDoc, getDocs, query, where, limit, increment } from 'firebase/firestore';
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

interface AnswerRecord {
  questionIndex: number;
  timeMs: number;
}

interface GameData {
  mode: string;
  status: string;
  players: string[];
  scores: Record<string, number>;
  questions?: Question[];
  winner?: string;
  category?: string;
  difficulty?: string;
  messages?: ChatMessage[];
  startTime?: number;
  timeline?: Record<string, AnswerRecord[]>;
}

export default function PvPMode() {
  const { user, profile } = useAuth();
  const [gameId, setGameId] = useState<string | null>(null);
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [xpEarned, setXpEarned] = useState<number | null>(null);
  const [playerProfiles, setPlayerProfiles] = useState<Record<string, any>>({});
  const [statsUpdated, setStatsUpdated] = useState(false);
  const [category, setCategory] = useState('all');
  const [difficulty, setDifficulty] = useState('medium');
  const [count, setCount] = useState(5);
  const [playerColor, setPlayerColor] = useState(profile?.color || '#ef4444');
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
  const [countdown, setCountdown] = useState<number | null>(null);
  const [gameStarted, setGameStarted] = useState(false);
  
  const countdownRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (gameData?.status === 'active' && !gameStarted && countdown === null) {
      setCountdown(3);
    }
  }, [gameData?.status, gameStarted, countdown]);

  useEffect(() => {
    if (countdown === null) return;
    
    if (countdown > 0) {
      playSound('tick');
      countdownRef.current = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    } else if (countdown === 0) {
      playSound('start');
      setCountdown(null);
      setGameStarted(true);
    }
    
    return () => {
      if (countdownRef.current) clearTimeout(countdownRef.current);
    };
  }, [countdown]);

  useEffect(() => {
    if (gameData?.status === 'finished' && !statsUpdated && user) {
      setStatsUpdated(true);
      const myScore = gameData.scores[user.uid] || 0;
      const opponentUid = gameData.players.find(p => p !== user.uid);
      const opponentScore = opponentUid ? (gameData.scores[opponentUid] || 0) : 0;
      
      const isWinner = myScore > opponentScore;
      const isTie = myScore === opponentScore;
      const placement = isWinner ? 1 : (isTie ? 1.5 : 2);
      
      const opponentRating = playerProfiles[opponentUid || '']?.rating || 0;
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
        [opponentRating],
        allMatchProblems,
        placement,
        2
      );

      let totalXpBonus = 0;
      const topicXpUpdates: Record<string, any> = {};
      
      solvedProblems.forEach(p => {
        if (p.solved) {
          const baseXp = calculateProblemXp('pvp', p.difficulty);
          const totalXp = calculateProblemXp('pvp', p.difficulty, placement, 2);
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
            losses: increment(!isWinner && !isTie ? 1 : 0),
            xp: increment(totalXpBonus),
            ...topicXpUpdates,
            ...ratingUpdates,
            rating: newOverallRating
          }).catch(error => handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`));
        });
      });
    }
  }, [gameData?.status, statsUpdated, user, gameData?.scores, gameData?.players, gameData?.category, gameData?.difficulty, profile, playerProfiles, solvedProblems, gameData?.questions]);

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

  const [invitedFriendId, setInvitedFriendId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && user) {
      const params = new URLSearchParams(window.location.search);
      const invite = params.get('invite');
      if (invite) {
        setInvitedFriendId(invite);
      }
      const joinId = params.get('join');
      if (joinId) {
        joinGame(joinId);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const createGame = async () => {
    if (!user) return;
    setLoading(true);
    try {
      // Generate questions first
      const generatedQuestions = await generateQuestions(category, difficulty, count);
      
      if (generatedQuestions) {
        try {
          const docRef = await addDoc(collection(db, 'games'), {
            mode: 'pvp',
            status: 'waiting',
            players: [user.uid],
            scores: { [user.uid]: 0 },
            questions: generatedQuestions,
            category,
            difficulty,
            createdAt: serverTimestamp(),
          });
          setGameId(docRef.id);

          // Send invite if invitedFriendId is set
          if (invitedFriendId) {
            await addDoc(collection(db, 'gameInvites'), {
              from: user.uid,
              to: invitedFriendId,
              gameId: docRef.id,
              status: 'pending',
              createdAt: Date.now()
            });
          }
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
    setLoading(true);
    try {
      const gameRef = doc(db, 'games', idToJoin);
      let gameSnap;
      try {
        gameSnap = await getDoc(gameRef);
      } catch (error) {
        handleFirestoreError(error, OperationType.GET, `games/${idToJoin}`);
        return;
      }
      if (gameSnap.exists()) {
        const data = gameSnap.data() as GameData;
        if (data.status === 'waiting' && data.players.length < 2 && !data.players.includes(user.uid)) {
          try {
            await updateDoc(gameRef, {
              players: arrayUnion(user.uid),
              [`scores.${user.uid}`]: 0,
              status: 'active',
              startTime: Date.now()
            });
          } catch (error) {
            handleFirestoreError(error, OperationType.UPDATE, `games/${idToJoin}`);
          }
          setGameId(idToJoin);
        } else if (data.players.includes(user.uid)) {
          setGameId(idToJoin); // Rejoin
        } else {
          alert("Game is full or already started.");
        }
      } else {
        alert("Game not found.");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionSelect = (index: number) => {
    if (showExplanation || !gameData || !gameData.questions || !user || !gameId) return;
    setSelectedOption(index);
  };

  const findMatch = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const q = query(
        collection(db, 'games'), 
        where('status', '==', 'waiting'), 
        where('mode', '==', 'pvp'),
        where('category', '==', category),
        where('difficulty', '==', difficulty),
        limit(5)
      );
      const querySnapshot = await getDocs(q);
      
      let joined = false;
      for (const docSnap of querySnapshot.docs) {
        const data = docSnap.data() as GameData;
        if (data.players.length < 2 && !data.players.includes(user.uid)) {
          try {
            await updateDoc(doc(db, 'games', docSnap.id), {
              players: arrayUnion(user.uid),
              [`scores.${user.uid}`]: 0,
              status: 'active',
              startTime: Date.now()
            });
            setGameId(docSnap.id);
            joined = true;
            break;
          } catch (e) {
            console.error('Failed to join', e);
          }
        }
      }

      if (!joined) {
        await createGame(); // Make new game if no suitable one found
      }
    } catch (error) {
       console.error(error);
       await createGame();
    } finally {
      setLoading(false);
    }
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
      const matchTime = Date.now() - (gameData.startTime || Date.now());
      
      try {
        await updateDoc(doc(db, 'games', gameId), {
          [`scores.${user.uid}`]: newScore,
          [`timeline.${user.uid}`]: arrayUnion({ questionIndex: currentIndex, timeMs: matchTime })
        });

        // Continuous saving
        const xp = calculateProblemXp('pvp', q.difficulty);
        const topicKey = `topicXp.${q.topic}`;
        setXpEarned(xp);
        setTimeout(() => setXpEarned(null), 2000);
        await updateDoc(doc(db, 'users', user.uid), {
          xp: increment(xp),
          [topicKey]: increment(xp)
        });
      } catch (error) {
        handleFirestoreError(error, OperationType.UPDATE, `games/${gameId}`);
      }
    } else {
      playSound('incorrect');
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
        <RefreshCw className="w-12 h-12 text-red-500 animate-spin mb-4" />
        <p className="text-xl text-zinc-400 animate-pulse">Setting up arena...</p>
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
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium mb-4">
            <Swords className="w-4 h-4" />
            <span>PvP</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">PvP</h1>
          <p className="text-zinc-400 mt-4 text-lg">Challenge another player in a head-to-head calculus battle.</p>
          
          {invitedFriendId && (
            <div className="mt-4 p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex items-center gap-3">
              <Users className="w-5 h-5 text-indigo-400" />
              <p className="text-sm text-indigo-200">
                You are setting up a game to invite a friend. They will receive a notification once you create the lobby.
              </p>
            </div>
          )}
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
                  className="w-full appearance-none bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-white focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all"
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
                        ? 'bg-red-500/20 border-red-500 text-red-400' 
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
                Number of Questions
                <Info className="w-4 h-4 text-zinc-500 cursor-help" />
                <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                  The amount of questions in the match.
                </div>
              </label>
              <div className="flex items-center gap-4">
                <input 
                  type="range" 
                  min="1" 
                  max="10" 
                  value={count} 
                  onChange={e => setCount(parseInt(e.target.value) || 5)}
                  className="flex-1 h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-red-500"
                />
                <div className="w-16 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center font-mono font-bold text-xl text-red-400">
                  {count}
                </div>
              </div>
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider group relative w-fit">
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

          <div className="pt-4 border-t border-zinc-800/50 flex gap-4">
            <button 
              onClick={findMatch}
              className="flex-1 py-4 bg-red-600 hover:bg-red-500 text-white rounded-2xl font-bold text-lg transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-red-500/20 flex items-center justify-center gap-2 group"
            >
              <Users className="w-5 h-5 fill-current" /> 
              <span>Find Match</span>
            </button>
            <button 
              onClick={createGame}
              className="px-6 py-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-2xl font-bold text-lg transition-all hover:scale-[1.02] flex items-center justify-center gap-2 group"
              title="Create Custom / Invite"
            >
              <Swords className="w-5 h-5" /> 
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
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-white focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 font-mono transition-all"
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
          </div>
        </div>
      </div>
    );
  }

  if (gameData?.status === 'waiting') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl max-w-md w-full text-center"
        >
          <Users className="w-20 h-20 text-red-500 mx-auto mb-6 animate-pulse" />
          <h2 className="text-3xl font-bold mb-2">Waiting for Opponent...</h2>
          <p className="text-zinc-400 mb-6">Share this Game ID with your friend:</p>
          
          <div className="bg-zinc-950 border border-zinc-800 p-4 rounded-xl mb-6 font-mono text-xl text-red-400 select-all">
            {gameId}
          </div>

          {invitedFriendId && (
            <div className="mb-6 p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
              <p className="text-sm text-indigo-300 font-medium">
                Invite sent! Waiting for them to join...
              </p>
            </div>
          )}

          <div className="bg-zinc-950 border border-zinc-800 p-4 rounded-xl mb-8 text-left space-y-2">
            <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider mb-3">Game Settings</h3>
            <div className="flex justify-between items-center text-sm">
              <span className="text-zinc-400">Category</span>
              <span className="text-white capitalize">{gameData.category || 'Mixed'}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-zinc-400">Difficulty</span>
              <span className="text-white capitalize">{gameData.difficulty || 'Medium'}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-zinc-400">Questions</span>
              <span className="text-white">{gameData.questions?.length || 5}</span>
            </div>
          </div>
          
          <Link href="/" className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors block">
            Cancel
          </Link>
        </motion.div>
      </div>
    );
  }

  if (gameData?.status === 'finished') {
    const myScore = gameData.scores[user.uid] || 0;
    const opponentUid = gameData.players.find(p => p !== user.uid);
    const opponentScore = opponentUid ? (gameData.scores[opponentUid] || 0) : 0;
    const opponentRating = opponentUid ? (playerProfiles[opponentUid]?.rating || 0) : 0;
    const myRating = profile?.rating || 0;
    
    const isWinner = myScore > opponentScore;
    const isTie = myScore === opponentScore;

    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl max-w-md w-full text-center"
        >
          {isWinner ? (
            <div className="text-red-500 text-6xl mb-6">🏆</div>
          ) : isTie ? (
            <div className="text-zinc-500 text-6xl mb-6">🤝</div>
          ) : (
            <div className="text-blue-500 text-6xl mb-6">💀</div>
          )}
          
          <h2 className="text-3xl font-bold mb-2">
            {isWinner ? 'Victory!' : isTie ? 'Draw!' : 'Defeat!'}
          </h2>
          
          <div className="flex justify-center gap-8 my-8">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <RankIcon rating={myRating} className="w-4 h-4" />
                <p className="text-zinc-400 text-sm">You</p>
              </div>
              <p className="text-4xl font-bold font-mono" style={{ color: playerColor }}>{myScore}</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <p className="text-zinc-400 text-sm">Opponent</p>
                <RankIcon rating={opponentRating} className="w-4 h-4" />
              </div>
              <p className="text-4xl font-bold font-mono" style={{ color: opponentUid ? (playerProfiles[opponentUid]?.color || '#3b82f6') : '#3b82f6' }}>{opponentScore}</p>
            </div>
          </div>
          
          {/* Match Timeline Summary */}
          {(() => {
            const allAnswers: any[] = [];
            if (gameData.timeline) {
              Object.values(gameData.timeline).forEach(playerAnswers => {
                if (Array.isArray(playerAnswers)) {
                   allAnswers.push(...playerAnswers);
                }
              });
            }
            if (allAnswers.length > 0) {
              const maxTime = Math.max(10000, ...allAnswers.map(a => a.timeMs)); // minimum 10s scale

              return (
                <div className="mb-8 pt-6 border-t border-zinc-800/50 text-left">
                  <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider mb-4">Timeline (Correct Answers)</h3>
                  <div className="space-y-3">
                    {(gameData.questions || []).map((q, idx) => {
                      const myAnswer = gameData.timeline?.[user.uid]?.find((a: any) => a.questionIndex === idx);
                      const oppAnswer = opponentUid ? gameData.timeline?.[opponentUid]?.find((a: any) => a.questionIndex === idx) : null;
                      
                      if (!myAnswer && !oppAnswer) return null; // Only show if someone answered correctly

                      return (
                        <div key={idx} className="flex flex-col gap-2 bg-zinc-950 p-3 rounded-xl border border-zinc-800/50">
                          <div className="flex items-center justify-between text-xs font-bold text-zinc-500 uppercase">
                            <span>Q{idx + 1}</span>
                            <span>{Math.max(myAnswer?.timeMs || 0, oppAnswer?.timeMs || 0) > 0 ? (Math.max(myAnswer?.timeMs || 0, oppAnswer?.timeMs || 0) / 1000).toFixed(1) + 's max' : ''}</span>
                          </div>
                          <div className="relative h-6 bg-zinc-900 rounded-lg">
                            {/* Visual Timeline Bar */}
                            {myAnswer && (
                              <div 
                                className="absolute top-0 bottom-0 w-1.5 z-20 shadow-lg rounded-full"
                                title={`You: ${(myAnswer.timeMs / 1000).toFixed(1)}s`}
                                style={{ 
                                  backgroundColor: playerColor,
                                  left: `${Math.min(98, (myAnswer.timeMs / maxTime) * 100)}%`
                                }}
                              />
                            )}
                            {oppAnswer && (
                              <div 
                                className="absolute top-0 bottom-0 w-1.5 z-10 shadow-lg rounded-full"
                                title={`Opponent: ${(oppAnswer.timeMs / 1000).toFixed(1)}s`}
                                style={{ 
                                  backgroundColor: opponentUid ? (playerProfiles[opponentUid]?.color || '#3b82f6') : '#3b82f6',
                                  left: `${Math.min(98, (oppAnswer.timeMs / maxTime) * 100)}%`
                                }}
                              />
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            }
            return null;
          })()}

          <div className="flex flex-col gap-4">
            <button 
              onClick={() => setGameId(null)}
              className="w-full py-3 bg-red-600 hover:bg-red-500 rounded-xl font-bold transition-colors"
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

  if (gameData?.status === 'active' && countdown !== null) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={countdown}
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.5, opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="text-8xl font-bold text-red-500 font-mono"
          >
            {countdown > 0 ? countdown : 'GO!'}
          </motion.div>
        </AnimatePresence>
        <button
          onClick={() => {
            setCountdown(null);
            setGameStarted(true);
          }}
          className="absolute bottom-10 px-6 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors text-zinc-400 hover:text-white"
        >
          Skip Countdown
        </button>
      </div>
    );
  }

  if (gameData?.status === 'active' && gameData.questions && gameStarted) {
    const q = gameData.questions[currentIndex];
    const isCorrect = selectedOption === q?.correctIndex;
    
    const myScore = gameData.scores[user.uid] || 0;
    const opponentUid = gameData.players.find(p => p !== user.uid);
    const opponentScore = opponentUid ? (gameData.scores[opponentUid] || 0) : 0;
    const opponentName = opponentUid ? (playerProfiles[opponentUid]?.displayName || 'Opponent') : 'Opponent';
    const opponentRating = opponentUid ? (playerProfiles[opponentUid]?.rating || 0) : 0;
    const myRating = profile?.rating || 0;

    return (
      <div className="min-h-screen max-w-4xl mx-auto px-4 py-12 relative">
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

        <div className="flex justify-between items-center mb-8 bg-zinc-900/50 p-4 rounded-2xl border border-zinc-800">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="flex items-center gap-1.5 justify-center mb-1">
                <RankIcon rating={myRating} className="w-3 h-3" />
                <p className="text-xs text-zinc-500 uppercase font-bold tracking-wider">You</p>
              </div>
              <motion.p 
                key={myScore}
                initial={{ scale: 1.5, opacity: 0, y: -10 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                transition={{ type: 'spring', stiffness: 500, damping: 15 }}
                className="text-2xl font-bold font-mono inline-block"
                style={{ color: playerColor }}
              >
                {myScore}
              </motion.p>
            </div>
          </div>
          
          <div className="text-zinc-400 font-mono text-sm">
            Q {currentIndex + 1} / {gameData.questions.length}
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="flex items-center gap-1.5 justify-center mb-1">
                <p className="text-xs text-zinc-500 uppercase font-bold tracking-wider">{opponentName}</p>
                <RankIcon rating={opponentRating} className="w-3 h-3" />
              </div>
              <motion.p 
                key={opponentScore}
                initial={{ scale: 1.5, opacity: 0, y: -10 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                transition={{ type: 'spring', stiffness: 500, damping: 15 }}
                className="text-2xl font-bold font-mono inline-block"
                style={{ color: opponentUid ? (playerProfiles[opponentUid]?.color || '#3b82f6') : '#3b82f6' }}
              >
                {opponentScore}
              </motion.p>
            </div>
          </div>
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
                      btnClass += "bg-zinc-800 border-red-500/50 text-white";
                    } else {
                      btnClass += "bg-zinc-950 border-zinc-800 hover:border-red-500/50 hover:bg-zinc-800 cursor-pointer text-zinc-300";
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
                    className="px-8 py-4 bg-red-500 hover:bg-red-600 text-white rounded-2xl font-bold text-lg transition-colors flex items-center gap-2"
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
        <Chat gameId={gameId!} messages={gameData.messages || []} />
      </div>
    );
  }

  return null;
}
