'use client';

import { motion } from 'motion/react';
import { BookOpen, Trophy, Lightbulb, Shield, ArrowLeft, Star, Medal, Crown, Zap } from 'lucide-react';
import Link from 'next/link';

import { RankIcon } from '@/components/RankDisplay';

export default function HelpPage() {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-emerald-500/30">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-12"
        >
          {/* Header */}
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-4">Help & Information</h1>
            <p className="text-xl text-zinc-400">Everything you need to know about calculus.gg.</p>
          </div>

          {/* Rules */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-blue-500" />
              </div>
              <h2 className="text-2xl font-bold">Rules & Guidelines</h2>
            </div>
            <ul className="space-y-4 text-zinc-300 list-disc list-inside">
              <li><strong>No cheating:</strong> Using external calculators (like WolframAlpha, Symbolab) or AI tools during ranked matches is strictly prohibited.</li>
              <li><strong>Time limits:</strong> Each mode has specific time constraints. In Rapid mode, you have 60 seconds to answer as many questions as possible. In PvP and Multiplayer, you race against others.</li>
              <li><strong>Scoring:</strong> Correct answers increase your score and rating. Incorrect answers may result in penalties depending on the game mode.</li>
              <li><strong>Respect others:</strong> Maintain a positive environment in multiplayer modes.</li>
            </ul>
          </section>

          {/* Problem Sources */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-emerald-500" />
              </div>
              <h2 className="text-2xl font-bold">Problem Sources</h2>
            </div>
            <p className="text-zinc-300 mb-4">
              Our calculus problems are dynamically generated using advanced AI models (Gemini) to ensure an infinite variety of questions. The problems cover a wide range of topics including:
            </p>
            <ul className="space-y-2 text-zinc-300 list-disc list-inside">
              <li>Integration</li>
              <li>Differentiation</li>
              <li>Limits</li>
              <li>Series</li>
              <li>Differential Equations</li>
              <li>Multivariable Calculus</li>
            </ul>
          </section>

          {/* Ratings */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <Trophy className="w-5 h-5 text-purple-500" />
              </div>
              <h2 className="text-2xl font-bold">Ratings & Ranks</h2>
            </div>
            <p className="text-zinc-300 mb-6">
              Your rating reflects your calculus proficiency. Compete in ranked modes to climb the leaderboard and earn new ranks. Ratings are calculated based on your performance on individual problems, taking into account the difficulty of the problem, your placement in the match, and the ratings of your opponents. You also earn XP for every problem you solve correctly, which contributes to your overall level and topic mastery.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={0} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-zinc-500">Unrated</div>
                  <div className="text-sm text-zinc-500 font-mono">0</div>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={1} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-amber-700">Bronze</div>
                  <div className="text-sm text-zinc-500 font-mono">1 - 499</div>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={500} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-zinc-300">Silver</div>
                  <div className="text-sm text-zinc-500 font-mono">500 - 999</div>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={1000} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-yellow-500">Gold</div>
                  <div className="text-sm text-zinc-500 font-mono">1000 - 1499</div>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={1500} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-cyan-400">Platinum</div>
                  <div className="text-sm text-zinc-500 font-mono">1500 - 1999</div>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={2000} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-purple-500">Diamond</div>
                  <div className="text-sm text-zinc-500 font-mono">2000 - 2499</div>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={2500} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-red-500">Grandmaster</div>
                  <div className="text-sm text-zinc-500 font-mono">2500+</div>
                </div>
              </div>
            </div>
          </section>

          {/* Tips */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-yellow-500/10 flex items-center justify-center">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
              </div>
              <h2 className="text-2xl font-bold">Tips & How to Practice</h2>
            </div>
            <div className="space-y-6 text-zinc-300">
              <div>
                <h3 className="text-lg font-bold text-white mb-2">1. Start with Test Mode</h3>
                <p>Use the Test mode to practice without time pressure. Review the step-by-step LaTeX explanations after answering to understand the methodology.</p>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-2">2. Build Speed in Rapid Mode</h3>
                <p>Once you are comfortable with the concepts, use Rapid mode to improve your mental math and pattern recognition speed. Focus on accuracy first, then speed.</p>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-2">3. Memorize Common Derivatives & Integrals</h3>
                <p>Having common rules (power rule, trig functions, exponential/logarithmic rules) memorized will significantly decrease your solve time in competitive modes.</p>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-2">4. Review Your Mistakes</h3>
                <p>Don&apos;t just guess! If you get a problem wrong, take the time to read the explanation and understand why the correct answer is what it is.</p>
              </div>
            </div>
          </section>

        </motion.div>
      </div>
    </main>
  );
}
