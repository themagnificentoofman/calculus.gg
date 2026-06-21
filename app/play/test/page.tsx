'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { motion, AnimatePresence } from 'motion/react';
import { MathDisplay } from '@/components/MathDisplay';
import { ArrowRight, CheckCircle2, XCircle, RefreshCw, Home, Play, Calculator, Info } from 'lucide-react';
import Link from 'next/link';
import { generateQuestions } from '@/lib/gemini';
import { playSound } from '@/lib/sounds';
import { calculateProblemXp } from '@/lib/progression';
import { OperationType, handleFirestoreError } from '@/lib/firestore-errors';

interface Question {
  latexProblem: string;
  options: string[];
  correctIndex: number;
  explanation: string | string[];
  topic: string;
  difficulty: string;
}

export default function TestMode() {
  const { user } = useAuth();
  const [category, setCategory] = useState('all');
  const [difficulty, setDifficulty] = useState('medium');
  const [count, setCount] = useState(5);
  
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [xpEarned, setXpEarned] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);
  const { profile } = useAuth();
  const [playerColor, setPlayerColor] = useState(profile?.color || '#3b82f6');
  const [solvedProblems, setSolvedProblems] = useState<{topic: string, difficulty: string}[]>([]);
  
  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6', '#d946ef', '#f43f5e'];

  const handleColorSelect = async (color: string) => {
    setPlayerColor(color);
    if (user) {
      try {
        const { doc, updateDoc } = await import('firebase/firestore');
        const { db } = await import('@/firebase');
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

  const startGame = async () => {
    setLoading(true);
    try {
      const generatedQuestions = await generateQuestions(category, difficulty, count);
      if (generatedQuestions) {
        setQuestions(generatedQuestions);
        setCurrentIndex(0);
        setScore(0);
        setFinished(false);
        setSelectedOption(null);
        setShowExplanation(false);
        setSolvedProblems([]);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleOptionSelect = (index: number) => {
    if (showExplanation) return;
    setSelectedOption(index);
  };

  const checkAnswer = () => {
    if (selectedOption === null || showExplanation) return;
    
    if (selectedOption === questions[currentIndex].correctIndex) {
      playSound('correct');
      setScore(s => s + 1);
      setSolvedProblems(prev => [...prev, { topic: questions[currentIndex].topic, difficulty: questions[currentIndex].difficulty }]);
      
      // Auto-save XP continuously
      if (user) {
        import('firebase/firestore').then(({ doc, updateDoc, increment }) => {
          import('@/firebase').then(({ db }) => {
            const xp = calculateProblemXp('test', questions[currentIndex].difficulty);
            const topicKey = `topicXp.${questions[currentIndex].topic.toLowerCase()}`;
            
            setXpEarned(xp);
            setTimeout(() => setXpEarned(null), 2000);
            
            updateDoc(doc(db, 'users', user.uid), {
              xp: increment(xp),
              [topicKey]: increment(xp)
            }).catch(error => handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`));
          });
        });
      }
    } else {
      playSound('incorrect');
    }
    setShowExplanation(true);
  };

  const nextQuestion = async () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(i => i + 1);
      setSelectedOption(null);
      setShowExplanation(false);
    } else {
      playSound('end');
      setFinished(true);
      if (user) {
        import('firebase/firestore').then(({ doc, updateDoc, increment }) => {
          import('@/firebase').then(({ db }) => {
            updateDoc(doc(db, 'users', user.uid), {
              gamesPlayed: increment(1)
            }).catch(error => handleFirestoreError(error, OperationType.UPDATE, `users/${user.uid}`));
          });
        });
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
        <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        <p className="text-xl text-zinc-400 animate-pulse">Generating calculus problems...</p>
      </div>
    );
  }

  if (finished) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl max-w-md w-full text-center"
        >
          <Calculator className="w-20 h-20 text-blue-500 mx-auto mb-6" />
          <h2 className="text-3xl font-bold mb-2">Test Complete!</h2>
          <p className="text-zinc-400 mb-8">You scored <span className="font-bold font-mono text-xl" style={{ color: playerColor }}>{score}</span> out of {questions.length}</p>
          
          <div className="flex flex-col gap-4">
            <button 
              onClick={startGame}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold transition-colors"
            >
              Play Again
            </button>
            <button 
              onClick={() => { setQuestions([]); setFinished(false); }}
              className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors"
            >
              Change Settings
            </button>
            <Link href="/" className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl font-bold transition-colors block">
              Back to Dashboard
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  if (questions.length > 0) {
    const q = questions[currentIndex];
    const isCorrect = selectedOption === q.correctIndex;

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

        <div className="flex justify-between items-center mb-8">
          <Link href="/" className="text-zinc-400 hover:text-white flex items-center gap-2">
            <Home className="w-5 h-5" /> Dashboard
          </Link>
          <div className="text-zinc-400 font-mono">
            Question {currentIndex + 1} of {questions.length}
          </div>
          <div className="font-bold font-mono flex items-center gap-2" style={{ color: playerColor }}>
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
                    btnClass += "bg-zinc-800 border-blue-500/50 text-white";
                  } else {
                    btnClass += "bg-zinc-950 border-zinc-800 hover:border-blue-500/50 hover:bg-zinc-800 cursor-pointer text-zinc-300";
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
                  className="px-8 py-4 bg-blue-500 hover:bg-blue-600 text-white rounded-2xl font-bold text-lg transition-colors flex items-center gap-2"
                >
                  Confirm Answer <CheckCircle2 className="w-5 h-5" />
                </button>
              </motion.div>
            )}
          </motion.div>
        </AnimatePresence>

        {showExplanation && (
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
                {currentIndex < questions.length - 1 ? 'Next Question' : 'Finish Test'}
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen max-w-3xl mx-auto px-4 py-12 flex flex-col justify-center">
      <Link href="/" className="text-zinc-400 hover:text-white flex items-center gap-2 mb-12 w-fit transition-colors">
        <Home className="w-5 h-5" /> Back to Dashboard
      </Link>
      
      <div className="mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-4">
          <Calculator className="w-4 h-4" />
          <span>Test</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">Test Setup</h1>
        <p className="text-zinc-400 mt-4 text-lg">Configure your test session parameters.</p>
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
                className="w-full appearance-none bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
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
                      ? 'bg-blue-500/20 border-blue-500 text-blue-400' 
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
                The total number of questions in the test.
              </div>
            </label>
            <div className="flex items-center gap-4">
              <input 
                type="range" 
                min="1" 
                max="20" 
                value={count} 
                onChange={e => setCount(parseInt(e.target.value) || 5)}
                className="flex-1 h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="w-16 h-12 bg-zinc-950 border border-zinc-800 rounded-xl flex items-center justify-center font-mono font-bold text-xl text-blue-400">
                {count}
              </div>
            </div>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-bold text-zinc-300 mb-3 uppercase tracking-wider group relative w-fit">
              Display Color
              <svg className="w-4 h-4 text-zinc-500 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-zinc-800 text-xs text-zinc-300 rounded shadow-xl z-10 border border-zinc-700 normal-case font-normal">
                Choose your display color for the test.
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
            className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-bold text-lg transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-blue-500/20 flex items-center justify-center gap-2 group"
          >
            <Play className="w-5 h-5 fill-current" /> 
            <span>Start Test</span>
            <ArrowRight className="w-5 h-5 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all absolute right-6" />
          </button>
        </div>
      </div>
    </div>
  );
}


