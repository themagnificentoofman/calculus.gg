'use client';

import { motion } from 'motion/react';
import { BookOpen, Trophy, Lightbulb, Shield, Mail, ArrowRight } from 'lucide-react';

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
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">Help & Information</h1>
            <p className="text-lg sm:text-xl text-zinc-400">Everything you need to know about Calculus Ninja.</p>
          </div>

          <section className="flex flex-col gap-5 rounded-3xl border border-emerald-400/20 bg-emerald-400/5 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
            <div>
              <h2 className="text-lg font-semibold">Have a question or feedback?</h2>
              <p className="mt-1 text-sm leading-relaxed text-zinc-400">Report a bug, flag a balance issue, or get in touch.</p>
            </div>
            <a href="/contact" className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-400 px-4 py-3 text-sm font-semibold text-zinc-950 transition-colors hover:bg-emerald-300"><Mail className="h-4 w-4" aria-hidden="true" />Contact Us<ArrowRight className="h-4 w-4" aria-hidden="true" /></a>
          </section>

          {/* Rules */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-5 sm:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 shrink-0 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-blue-500" />
              </div>
              <h2 className="text-xl sm:text-2xl font-bold">Rules & Guidelines</h2>
            </div>
            <ul className="space-y-4 text-zinc-300 leading-relaxed list-disc list-inside">
              <li><strong>No cheating:</strong> Using external calculators (like WolframAlpha, Symbolab) or AI tools during ranked matches is strictly prohibited.</li>
              <li><strong>Time limits:</strong> Rapid uses the time limit you choose, and each incorrect answer removes 5 seconds. In PvP and Multiplayer, you race against others.</li>
              <li><strong>Scoring:</strong> Correct answers increase your score and earn XP. Rating changes only after competitive matches. Incorrect answers may result in penalties depending on the game mode.</li>
              <li><strong>Respect others:</strong> Maintain a positive environment in multiplayer modes.</li>
            </ul>
          </section>

          {/* Problem Sources */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-5 sm:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 shrink-0 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-emerald-500" />
              </div>
              <h2 className="text-xl sm:text-2xl font-bold">Problem Sources</h2>
            </div>
            <p className="text-zinc-300 leading-relaxed mb-4">
              Calculus Ninja selects reusable problems from a versioned bank. Original templates are checked with exact mathematical methods and rendering tests before publication. Automatic validation does not mean every problem has been reviewed by a person. AI can assist offline authoring; gameplay selection and grading do not call OpenAI. The problems cover a wide range of topics including:
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

          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-5 sm:p-8">
            <h2 className="text-xl font-bold mb-4">Difficulty and problem reports</h2>
            <p className="text-zinc-300 leading-relaxed">Easy uses fundamental rules; Medium combines standard techniques; Hard requires several steps or careful domain and convergence analysis; Olympiad asks you to discover a concealed identity or transformation. These are template estimates, not measured solve-time rankings. A category may be unavailable while content is under review.</p>
            <p className="mt-4 text-zinc-400 leading-relaxed">Use the copyable problem ID and revision in an answer review to report an issue. Corrections create a new revision, so previous games and results keep their original questions. A round avoids duplicate problems and limits repeated families; small categories use a bounded relaxation of recent-history and family limits.</p>
          </section>

          {/* Ratings */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-5 sm:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 shrink-0 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <Trophy className="w-5 h-5 text-purple-500" />
              </div>
              <h2 className="text-xl sm:text-2xl font-bold">Ratings & Ranks</h2>
            </div>
            <p className="text-zinc-300 leading-relaxed mb-6">
              Rating measures competitive results in PvP and Multiplayer. Each opponent is compared separately using both players’ ratings from the start of the match. An upset earns more than an expected win; a tie counts as half a win. Changes are balanced between players and bounded by 32 points per match, regardless of room size. Difficulty rewards XP, not extra rating. Empty and all-wrong games do not transfer rating. PvP ends when both players finish; target-score Multiplayer ends when the target is reached. Timed games use a shared deadline, and other competitive games have a 30-minute limit.
            </p>
            <p className="text-zinc-400 mb-4 leading-relaxed">
              Overall rating is independent of topic ratings. Topic ratings compare only the same questions that both players attempted; unseen questions do not count as mistakes. Equal scores share a position. A player who never answers cannot win over someone who participated. Existing ratings are preserved, start at zero for new players, and can go below zero. Unrated means no qualifying competitive result yet.
            </p>
            <p className="text-zinc-400 mb-4 leading-relaxed">
              Every correct answer earns 10 XP (Easy), 20 XP (Medium), 30 XP (Hard), or 50 XP (Olympiad), in every mode. There are no placement bonuses. Level L requires 100 × L² total XP: level 1 needs 100, level 2 needs 400, and level 3 needs 900. Topic levels follow the same curve.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={0} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-zinc-500">Unrated</div>
                  <div className="text-sm text-zinc-500 font-mono">No rated matches</div>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 bg-zinc-950 rounded-2xl border border-zinc-800">
                <RankIcon rating={1} className="w-8 h-8" />
                <div>
                  <div className="font-bold text-amber-500">Bronze</div>
                  <div className="text-sm text-zinc-500 font-mono">Below 500 (rated)</div>
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

          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-5 sm:p-8">
            <h2 className="text-xl sm:text-2xl font-bold mb-4">History, replay &amp; analysis</h2>
            <div className="space-y-4 text-zinc-300 leading-relaxed">
              <p>Your stored round history has no automatic record limit. History displays 25 rounds per page; use date ranges, mode, topic, difficulty, recorded result, and replay capability to find older rounds. Filters search the full stored history. Unknown dates remain available under All dates.</p>
              <p>New rounds capture the exact bank problem revision and choice order, server-confirmed answers and scores, and your browser’s observed interactions. Replay is private to participants; only your own detailed perspective and public opponent scores are shown. Solutions and analysis unlock after the entire match ends, including when you finish your questions first.</p>
              <p>Recorded playback follows the original timeline, including countdowns, penalties and captured feedback. You can pause, seek, change speed, and jump between questions or events. Analysis shows saved solutions separately. Viewing a replay does not submit answers, generate problems, award XP, change ratings, or alter the match result.</p>
              <p>Recording means the round is still in progress. Syncing means captured events are waiting to upload. Available means the expected evidence synchronized; Partial means some events or timing could not be recovered. Unavailable means the replay data could not be loaded. Legacy — replay was not recorded for this round. Rounds already in progress when replay launched remain Legacy.</p>
              <p>Keep this device’s site data until synchronization finishes. Events are saved incrementally on this device and retried after reconnecting. Closing the browser, clearing site data, denied storage, or a crash can leave a partial replay. Unknown timings are shown as unknown. Reloads use separate clock segments; an unaligned segment is not given an invented time.</p>
              <p>History and synchronized replays are not automatically deleted. To bound recording cost, capture allows up to 4,096 client events per player per round, 32 page sessions, and 128 chunks per session, with at most 32 events and 24 KB per chunk. Reaching a recording limit marks the replay partial and does not change gameplay or remove the round from history. Chat and account credentials are not recorded in replay events.</p>
            </div>
          </section>

          {/* Tips */}
          <section className="bg-zinc-900/40 border border-zinc-800/50 rounded-3xl p-5 sm:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 shrink-0 rounded-xl bg-yellow-500/10 flex items-center justify-center">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
              </div>
              <h2 className="text-xl sm:text-2xl font-bold">Tips & How to Practice</h2>
            </div>
            <div className="space-y-6 text-zinc-300 leading-relaxed">
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
